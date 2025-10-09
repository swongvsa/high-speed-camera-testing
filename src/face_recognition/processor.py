"""
Face recognition pipeline orchestration.
Coordinates detection, recognition, and annotation.
"""

import logging
import time
from typing import Optional

import numpy as np

from src.face_recognition.annotator import FaceAnnotator
from src.face_recognition.config import FaceRecognitionConfig
from src.face_recognition.detector import FaceDetector
from src.face_recognition.embeddings_manager import EmbeddingsManager
from src.face_recognition.recognizer import FaceRecognizer

logger = logging.getLogger(__name__)


class FaceRecognitionProcessor:
    """
    Orchestrates the complete face recognition pipeline:
    1. Face detection
    2. Embedding generation
    3. Recognition (matching against database)
    4. Annotation (visual overlay)

    Thread-safe for single-threaded frame processing.
    """

    def __init__(
        self,
        config: FaceRecognitionConfig,
        embeddings_manager: Optional[EmbeddingsManager] = None,
        recognize_every_n_frames: int = 10,
    ):
        """
        Initialize processor.

        Args:
            config: Face recognition configuration
            embeddings_manager: Optional embeddings manager (creates new if None)
        """
        self._config = config
        self._embeddings_mgr = embeddings_manager or EmbeddingsManager()
        self._detector = FaceDetector(config)
        self._recognizer = FaceRecognizer(config, self._embeddings_mgr)
        self._annotator = FaceAnnotator(config)

        # How often to run recognition (1 = every frame). Skipping frames
        # reduces CPU usage and noisy DeepFace errors when no face is present.
        self._recognize_every_n_frames = recognize_every_n_frames
        self._frame_counter = 0

        # Throttle recognition error logs to avoid flooding the terminal when
        # many frames do not contain faces or DeepFace fails briefly.
        self._last_recognition_log_ts = 0.0
        self._recognition_log_interval = 5.0  # seconds

        logger.info(
            f"Face recognition processor initialized with {len(self._embeddings_mgr)} enrolled face(s)"
        )

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, str]:
        """
        Process a single frame through face recognition pipeline.

        Args:
            frame: Input frame (H×W×3 RGB or BGR)

        Returns:
            Tuple of (annotated_frame, debug_info):
                - annotated_frame: Frame with face boxes and labels
                - debug_info: String with recognition results
        """
        try:
            # Ensure RGB format
            if len(frame.shape) == 2:
                # Grayscale -> RGB
                frame_rgb = np.stack([frame, frame, frame], axis=-1)
            else:
                frame_rgb = frame

            # Step 1: Detect faces
            detected_faces = self._detector.detect_faces(frame_rgb)

            if len(detected_faces) == 0:
                # No faces detected
                debug_info = "No faces detected"
                return frame_rgb, debug_info

            # Step 2: Generate embeddings and recognize
            recognition_results = []

            # Increment frame counter and decide whether to run recognition this frame
            self._frame_counter += 1
            do_recognize = (self._frame_counter % self._recognize_every_n_frames) == 0

            for face_data in detected_faces:
                try:
                    face_img = face_data["face"]

                    # Validate face crop size (skip tiny crops)
                    try:
                        h, w = face_img.shape[:2]
                    except Exception:
                        h = w = 0

                    if not do_recognize:
                        # Skip heavy recognition step, return unknown for now
                        recognition_results.append((None, 1.0))
                        continue

                    if h < 24 or w < 24:
                        logger.debug(f"Skipping recognition for tiny face crop ({w}x{h})")
                        recognition_results.append((None, 1.0))
                        continue

                    # Generate embedding for detected face
                    embedding = self._recognizer.generate_embedding(face_img)

                    # Match against database
                    name, distance = self._recognizer.recognize_face(embedding)

                    recognition_results.append((name, distance))

                except Exception as e:
                    # Throttle repeated recognition errors to avoid log flooding
                    now = time.time()
                    if now - self._last_recognition_log_ts > self._recognition_log_interval:
                        logger.error(f"Recognition failed for face: {e}")
                        self._last_recognition_log_ts = now
                    else:
                        logger.debug(f"Recognition transient error suppressed: {e}")
                    recognition_results.append((None, 1.0))

            # Step 3: Annotate frame
            annotated_frame = self._annotator.annotate(
                frame=frame_rgb,
                faces=detected_faces,
                recognition_results=recognition_results,
            )

            # Add status text
            num_recognized = sum(1 for name, _ in recognition_results if name is not None)
            annotated_frame = self._annotator.add_status_text(
                frame=annotated_frame,
                num_faces=len(detected_faces),
                num_recognized=num_recognized,
            )

            # Ensure contiguous array
            if not annotated_frame.flags["C_CONTIGUOUS"]:
                annotated_frame = np.ascontiguousarray(annotated_frame)

            # Step 4: Generate debug info
            debug_info = self._generate_debug_info(recognition_results)

            return annotated_frame, debug_info

        except Exception as e:
            logger.error(f"Frame processing failed: {e}", exc_info=True)
            return frame, f"⚠️ Error: {str(e)}"

    def _generate_debug_info(self, recognition_results: list[tuple[Optional[str], float]]) -> str:
        """
        Generate debug information for recognition results.

        Args:
            recognition_results: List of (name, distance) tuples

        Returns:
            Formatted string with recognition info
        """
        if len(recognition_results) == 0:
            return "No faces detected"

        lines = [f"Detected {len(recognition_results)} face(s):\n"]

        for i, (name, distance) in enumerate(recognition_results, 1):
            if name:
                # Convert distance to confidence
                if self._config.distance_metric == "cosine":
                    confidence = (1 - distance) * 100
                else:
                    confidence = max(0, (1 - distance / 2) * 100)

                lines.append(
                    f"{i}. {name} (confidence: {confidence:.1f}%, distance: {distance:.3f})"
                )
            else:
                lines.append(f"{i}. Unknown (distance: {distance:.3f})")

        # Add database info with model compatibility
        total_enrolled = len(self._embeddings_mgr)
        compatible = self._embeddings_mgr.get_all_embeddings(
            model_name=self._config.model_name
        )
        num_compatible = len(compatible)

        if num_compatible == total_enrolled:
            lines.append(f"\n📊 Database: {total_enrolled} enrolled face(s)")
        else:
            lines.append(
                f"\n⚠️ Database: {num_compatible}/{total_enrolled} faces compatible with {self._config.model_name}\n"
                f"💡 Re-enroll {total_enrolled - num_compatible} face(s) to use with this model"
            )

        return "\n".join(lines)

    def enroll_face(self, name: str, image: np.ndarray | str) -> dict:
        """
        Enroll a new face in the database.

        Args:
            name: Person's name
            image: Face image as numpy array or file path

        Returns:
            Enrollment result dictionary

        Raises:
            ValueError: If face detection/extraction fails
            RuntimeError: If embedding generation fails
        """
        # Validate single face
        face_data = self._detector.extract_single_face(image)

        if face_data is None:
            raise ValueError("Could not extract face from image")

        # Enroll using recognizer
        result = self._recognizer.enroll_face(name, image)

        logger.info(f"Enrolled '{name}' successfully")
        return result

    def remove_face(self, name: str) -> bool:
        """
        Remove a face from the database.

        Args:
            name: Person's name

        Returns:
            True if removed, False if not found
        """
        return self._embeddings_mgr.remove_face(name)

    def list_enrolled_faces(self) -> list[str]:
        """Get list of all enrolled faces."""
        return self._embeddings_mgr.list_faces()

    @property
    def num_enrolled(self) -> int:
        """Get number of enrolled faces."""
        return len(self._embeddings_mgr)

    @property
    def is_ready(self) -> bool:
        """Check if processor is ready."""
        return True  # Always ready, database can be empty

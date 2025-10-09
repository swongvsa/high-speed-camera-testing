"""
Face detection wrapper using DeepFace.
"""

import logging
from typing import Optional

import numpy as np
from deepface import DeepFace

from src.face_recognition.config import FaceRecognitionConfig

logger = logging.getLogger(__name__)


class FaceDetector:
    """
    Wrapper for DeepFace face detection.

    Detects faces in frames and extracts face regions with bounding boxes.
    """

    def __init__(self, config: FaceRecognitionConfig):
        """
        Initialize face detector.

        Args:
            config: Face recognition configuration
        """
        self._config = config
        logger.info(f"Face detector initialized with {config.detector_backend} backend")

    def detect_faces(
        self, frame: np.ndarray
    ) -> list[dict[str, tuple[int, int, int, int] | np.ndarray]]:
        """
        Detect all faces in a frame.

        Args:
            frame: Input frame (H×W×3 RGB or BGR)

        Returns:
            List of detected faces, each containing:
                - 'bbox': (x, y, w, h) bounding box
                - 'face': Cropped and aligned face image
                - 'confidence': Detection confidence (if available)
                - 'is_real': Liveness check result (if anti-spoofing enabled)

        Note:
            Returns empty list if no faces detected and enforce_detection=False
        """
        try:
            # Use DeepFace.extract_faces for detection
            face_objs = DeepFace.extract_faces(
                img_path=frame,
                detector_backend=self._config.detector_backend,
                enforce_detection=False,  # Don't raise error, return empty list
                align=self._config.align_faces,
                anti_spoofing=self._config.enable_anti_spoofing,
            )

            detected_faces = []
            for face_obj in face_objs:
                # DeepFace returns facial_area as dict with x, y, w, h, left_eye, right_eye
                facial_area = face_obj.get("facial_area", {})
                bbox = (
                    facial_area.get("x", 0),
                    facial_area.get("y", 0),
                    facial_area.get("w", 0),
                    facial_area.get("h", 0),
                )

                # Normalize the cropped face array to a clean uint8 contiguous RGB image
                face_crop = face_obj.get("face")
                if isinstance(face_crop, (list, tuple)):
                    # Defensive: sometimes DeepFace may return non-array; skip
                    face_crop = None

                if isinstance(face_crop, np.ndarray):
                    # Convert grayscale to 3-channel
                    if face_crop.ndim == 2:
                        face_crop = np.stack([face_crop, face_crop, face_crop], axis=-1)

                    # If float in 0..1, scale up
                    if np.issubdtype(face_crop.dtype, np.floating):
                        if face_crop.max() <= 1.0:
                            face_crop = (face_crop * 255.0).clip(0, 255).astype(np.uint8)
                        else:
                            face_crop = face_crop.astype(np.uint8)

                    face_crop = np.ascontiguousarray(face_crop)

                    # If it looks like BGR (most camera outputs), convert to RGB for DeepFace
                    try:
                        if face_crop.shape[-1] == 3:
                            # Heuristic: we assume DeepFace prefers RGB
                            face_crop = face_crop[:, :, ::-1].copy()  # BGR->RGB
                    except Exception:
                        pass

                face_data = {
                    "bbox": bbox,
                    "face": face_crop,  # Cropped and normalized face image or None
                    "confidence": face_obj.get("confidence", 1.0),
                }

                # Add anti-spoofing result if enabled
                if self._config.enable_anti_spoofing:
                    face_data["is_real"] = face_obj.get("is_real", True)

                detected_faces.append(face_data)

            logger.debug(f"Detected {len(detected_faces)} face(s) in frame")
            return detected_faces

        except Exception as e:
            logger.error(f"Face detection failed: {e}", exc_info=True)
            return []

    def extract_single_face(
        self, image: np.ndarray | str
    ) -> Optional[dict[str, np.ndarray | tuple[int, int, int, int]]]:
        """
        Extract exactly one face from an image (for enrollment).

        Args:
            image: Image as numpy array or file path

        Returns:
            Dictionary with 'face' and 'bbox', or None if not exactly 1 face

        Raises:
            ValueError: If multiple faces or no faces detected
        """
        try:
            face_objs = DeepFace.extract_faces(
                img_path=image,
                detector_backend=self._config.detector_backend,
                enforce_detection=self._config.enforce_detection,
                align=self._config.align_faces,
                anti_spoofing=self._config.enable_anti_spoofing,
            )

            if len(face_objs) == 0:
                raise ValueError("No face detected in image")

            if len(face_objs) > 1:
                raise ValueError(
                    f"Multiple faces detected ({len(face_objs)}). Please provide image with exactly one face."
                )

            # Extract single face
            face_obj = face_objs[0]

            # Check anti-spoofing if enabled
            if self._config.enable_anti_spoofing:
                if not face_obj.get("is_real", True):
                    raise ValueError("Liveness check failed. Image may be a photo or screen.")

            facial_area = face_obj.get("facial_area", {})
            bbox = (
                facial_area.get("x", 0),
                facial_area.get("y", 0),
                facial_area.get("w", 0),
                facial_area.get("h", 0),
            )

            return {"face": face_obj["face"], "bbox": bbox}

        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Face extraction failed: {e}", exc_info=True)
            raise RuntimeError(f"Face extraction failed: {e}")

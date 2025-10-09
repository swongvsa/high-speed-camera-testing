"""
Visual annotation for face recognition.
Draws bounding boxes and labels on detected faces.
"""

import logging
from typing import Optional

import cv2
import numpy as np

from src.face_recognition.config import FaceRecognitionConfig

logger = logging.getLogger(__name__)


class FaceAnnotator:
    """
    Annotates frames with face bounding boxes and labels.
    """

    def __init__(self, config: FaceRecognitionConfig):
        """
        Initialize annotator.

        Args:
            config: Face recognition configuration
        """
        self._config = config

    def annotate(
        self,
        frame: np.ndarray,
        faces: list[dict],
        recognition_results: list[tuple[Optional[str], float]],
    ) -> np.ndarray:
        """
        Annotate frame with face bounding boxes and labels.

        Args:
            frame: Input frame (H×W×3)
            faces: List of detected faces with 'bbox' key
            recognition_results: List of (name, distance) tuples for each face

        Returns:
            Annotated frame with bounding boxes and labels
        """
        annotated = frame.copy()

        for face, (name, distance) in zip(faces, recognition_results):
            bbox = face["bbox"]
            x, y, w, h = bbox

            # Determine if recognized
            is_recognized = name is not None
            label = name if is_recognized else "Unknown"

            # Choose color based on recognition status
            color = (
                self._config.bbox_color_known
                if is_recognized
                else self._config.bbox_color_unknown
            )

            # Draw bounding box
            cv2.rectangle(
                annotated,
                (x, y),
                (x + w, y + h),
                color,
                self._config.bbox_thickness,
            )

            # Prepare label text
            if self._config.show_labels:
                label_text = label

                if self._config.show_confidence:
                    # Convert distance to confidence percentage
                    # For cosine: similarity = 1 - distance
                    if self._config.distance_metric == "cosine":
                        confidence = (1 - distance) * 100
                    else:
                        # For euclidean metrics, use inverse relationship
                        confidence = max(0, (1 - distance / 2) * 100)

                    label_text = f"{label} ({confidence:.1f}%)"

                # Draw label background
                (text_width, text_height), baseline = cv2.getTextSize(
                    label_text,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    self._config.text_scale,
                    self._config.text_thickness,
                )

                # Draw filled rectangle for text background
                cv2.rectangle(
                    annotated,
                    (x, y - text_height - baseline - 5),
                    (x + text_width, y),
                    color,
                    -1,  # Filled
                )

                # Draw label text
                cv2.putText(
                    annotated,
                    label_text,
                    (x, y - baseline - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    self._config.text_scale,
                    (255, 255, 255),  # White text
                    self._config.text_thickness,
                )

        return annotated

    def add_status_text(
        self, frame: np.ndarray, num_faces: int, num_recognized: int
    ) -> np.ndarray:
        """
        Add status text to frame showing recognition stats.

        Args:
            frame: Input frame
            num_faces: Total number of faces detected
            num_recognized: Number of faces recognized

        Returns:
            Frame with status text
        """
        annotated = frame.copy()

        status_text = (
            f"Face Recognition: {num_recognized}/{num_faces} recognized"
        )

        # Ensure frame is contiguous for cv2 operations
        if not annotated.flags["C_CONTIGUOUS"]:
            annotated = np.ascontiguousarray(annotated)

        cv2.putText(
            annotated,
            status_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        return annotated

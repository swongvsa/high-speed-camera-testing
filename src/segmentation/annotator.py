"""
Frame annotation using Supervision library.
"""

import logging
from typing import List, Optional

import numpy as np
import supervision as sv

from src.segmentation.config import SegmentationConfig

logger = logging.getLogger(__name__)


class FrameAnnotator:
    """
    Applies visual annotations to frames using Supervision.

    Handles masks, bounding boxes, labels, and confidence scores.
    Configurable styles and colors.
    """

    def __init__(self, config: SegmentationConfig):
        """
        Initialize annotator with configuration.

        Args:
            config: Segmentation configuration
        """
        self._config = config

        # Create mask annotator with opacity
        self._mask_annotator = sv.MaskAnnotator(
            opacity=config.mask_opacity,
        )

        # Create label annotator (positioned at center of mass)
        self._label_annotator = sv.LabelAnnotator(
            text_position=sv.Position.CENTER_OF_MASS,
            text_scale=0.5,
            text_thickness=1,
            text_padding=5,
        )

        # Optional: Bounding box annotator for clarity
        self._box_annotator = sv.BoxAnnotator(
            thickness=2,
        )

    def annotate(
        self,
        frame: np.ndarray,
        detections: sv.Detections,
        class_names: Optional[dict] = None,
    ) -> np.ndarray:
        """
        Apply annotations to frame.

        Args:
            frame: Input frame (H×W×3 RGB)
            detections: Supervision detections with masks
            class_names: Optional mapping of class_id -> name

        Returns:
            Annotated frame (same shape as input)

        Note:
            Creates a copy of the frame to avoid modifying the original.
        """
        # Early return if no detections
        if len(detections) == 0:
            logger.debug("No detections to annotate")
            return frame

        # Work on a copy
        annotated = frame.copy()

        # Apply mask annotations
        annotated = self._mask_annotator.annotate(
            scene=annotated,
            detections=detections,
        )

        # Apply labels if configured
        if self._config.show_labels:
            labels = self._create_labels(detections, class_names)
            annotated = self._label_annotator.annotate(
                scene=annotated,
                detections=detections,
                labels=labels,
            )

        logger.debug(f"Annotated frame with {len(detections)} detections")
        return annotated

    def _create_labels(
        self,
        detections: sv.Detections,
        class_names: Optional[dict] = None,
    ) -> List[str]:
        """
        Create label strings for each detection.

        Args:
            detections: Supervision detections
            class_names: Optional class name mapping

        Returns:
            List of label strings (one per detection)
        """
        labels = []

        for i, (class_id, confidence) in enumerate(
            zip(detections.class_id, detections.confidence)
        ):
            # Get class name (or use ID if no mapping)
            if class_names and class_id in class_names:
                class_name = class_names[class_id]
            else:
                class_name = f"Class {class_id}"

            # Build label string
            if self._config.show_confidence:
                label = f"{class_name} {confidence:.2f}"
            else:
                label = class_name

            labels.append(label)

        return labels

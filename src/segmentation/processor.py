"""
Frame processing orchestration for segmentation pipeline.
"""

import logging
from typing import Optional

import numpy as np
import supervision as sv

from src.segmentation.annotator import FrameAnnotator
from src.segmentation.config import SegmentationConfig
from src.segmentation.detector import SegmentationDetector

logger = logging.getLogger(__name__)


class SegmentationProcessor:
    """
    Orchestrates the complete segmentation pipeline:
    1. Detection (YOLO inference)
    2. Optional tracking (ByteTrack)
    3. Optional smoothing
    4. Annotation (masks, labels)

    Thread-safe for single-threaded frame processing.
    """

    def __init__(self, config: SegmentationConfig):
        """
        Initialize processor with configuration.

        Args:
            config: Segmentation configuration
        """
        self._config = config
        self._detector = SegmentationDetector(config)
        self._annotator = FrameAnnotator(config)

        # Optional components
        self._tracker: Optional[sv.ByteTrack] = None
        self._smoother: Optional[sv.DetectionsSmoother] = None

        # Initialize optional components
        if config.enable_tracking:
            self._tracker = sv.ByteTrack()
            logger.debug("ByteTrack tracking enabled")

        if config.enable_smoothing:
            self._smoother = sv.DetectionsSmoother()
            logger.debug("Detection smoothing enabled")

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, str]:
        """
        Process a single frame through the segmentation pipeline.

        Args:
            frame: Input frame (H×W×3 RGB or H×W grayscale)

        Returns:
            tuple: (annotated_frame, debug_info)
                - annotated_frame: Frame with segmentation masks and labels
                - debug_info: String with top 3 detections info

        Pipeline:
            1. Convert grayscale to RGB if needed
            2. Run YOLO detection
            3. Apply tracking (if enabled)
            4. Apply smoothing (if enabled)
            5. Annotate with masks and labels
        """
        try:
            # Ensure RGB format
            if len(frame.shape) == 2:
                # Grayscale -> RGB
                frame_rgb = np.stack([frame, frame, frame], axis=-1)
            else:
                frame_rgb = frame

            # Step 1: Detect objects
            detections = self._detector.detect(frame_rgb)

            # Step 1a: Filter by class if configured
            if self._config.class_filter is not None and len(detections) > 0:
                mask = [
                    class_id in self._config.class_filter
                    for class_id in detections.class_id
                ]
                detections = detections[mask]
                logger.debug(
                    f"Filtered to {len(detections)} objects in classes {self._config.class_filter}"
                )

            # Step 2: Apply tracking (if enabled)
            if self._tracker is not None and len(detections) > 0:
                detections = self._tracker.update_with_detections(detections)
                logger.debug(f"Tracking updated: {len(detections)} objects")

            # Step 3: Apply smoothing (if enabled)
            if self._smoother is not None and len(detections) > 0:
                detections = self._smoother.update_with_detections(detections)
                logger.debug(f"Smoothing applied: {len(detections)} objects")

            # Step 4: Annotate frame
            annotated_frame = self._annotator.annotate(
                frame=frame_rgb,
                detections=detections,
                class_names=self._get_class_names(),
            )

            # Ensure contiguous array for cv2 operations
            if not annotated_frame.flags['C_CONTIGUOUS']:
                annotated_frame = np.ascontiguousarray(annotated_frame)

            # Add status indicator
            import cv2
            status_text = f"Segmentation ON | {len(detections)} objects | conf≥{self._config.confidence_threshold:.2f}"
            cv2.putText(
                annotated_frame,
                status_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            # Generate debug info for top 3 detections
            debug_info = self._generate_debug_info(detections)

            return annotated_frame, debug_info

        except Exception as e:
            logger.error(f"Frame processing failed: {e}", exc_info=True)
            # Return original frame on error with error message
            return frame, f"⚠️ Error: {str(e)}"

    def _generate_debug_info(self, detections: sv.Detections) -> str:
        """
        Generate debug information for top 3 detections.

        Args:
            detections: Supervision detections

        Returns:
            Formatted string with top 3 detections
        """
        if len(detections) == 0:
            return "🔍 No objects detected\n\n💡 Try:\n- Lower confidence threshold\n- Point at common objects (person, chair, laptop, phone)"

        class_names = self._get_class_names() or {}

        # Count detections by class
        from collections import Counter
        class_counts = Counter(detections.class_id.tolist())

        # Get top 3 by average confidence per class
        class_info = []
        for class_id, count in class_counts.items():
            class_name = class_names.get(class_id, f"Class_{class_id}")
            # Get confidences for this class
            mask = detections.class_id == class_id
            confidences = detections.confidence[mask]
            avg_conf = confidences.mean()
            max_conf = confidences.max()

            class_info.append({
                'class_id': class_id,
                'name': class_name,
                'count': count,
                'avg_conf': avg_conf,
                'max_conf': max_conf
            })

        # Sort by max confidence
        class_info.sort(key=lambda x: x['max_conf'], reverse=True)

        # Format top 3
        lines = [f"✅ Detected {len(detections)} objects:\n"]
        for i, info in enumerate(class_info[:3], 1):
            lines.append(
                f"{i}. {info['name']}: {info['count']}× "
                f"(conf: {info['max_conf']:.2f}, avg: {info['avg_conf']:.2f})"
            )

        if len(class_info) > 3:
            lines.append(f"\n...and {len(class_info) - 3} more classes")

        return "\n".join(lines)

    def _get_class_names(self) -> Optional[dict]:
        """
        Get COCO class names from YOLO model.

        Returns:
            Dictionary mapping class_id -> class_name, or None if unavailable
        """
        if not self._detector.is_loaded:
            return None

        try:
            # Access model's class names (COCO dataset)
            model = self._detector._model
            if model and hasattr(model, "names"):
                return model.names
        except Exception as e:
            logger.warning(f"Could not load class names: {e}")

        return None

    @property
    def is_ready(self) -> bool:
        """Check if processor is ready (model loaded)."""
        return self._detector.is_loaded

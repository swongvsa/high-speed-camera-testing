"""
YOLO segmentation model wrapper.
"""

import logging
from typing import Optional

import numpy as np
import supervision as sv
from ultralytics import YOLO

from src.segmentation.config import SegmentationConfig

logger = logging.getLogger(__name__)


class SegmentationDetector:
    """
    Wrapper for YOLOv8 segmentation model with supervision integration.

    Handles model loading, inference, and conversion to supervision Detections format.
    Thread-safe for single model instance usage.
    """

    def __init__(self, config: SegmentationConfig):
        """
        Initialize detector with configuration.

        Args:
            config: Segmentation configuration

        Note:
            Model is lazy-loaded on first inference call.
        """
        self._config = config
        self._model: Optional[YOLO] = None
        self._initialized = False

    def _load_model(self) -> None:
        """
        Load YOLO model (lazy initialization).

        Automatically downloads model from Ultralytics if not cached locally.
        Models are cached in ~/.ultralytics/weights/ by default.

        Raises:
            RuntimeError: Model loading failed
        """
        if self._initialized:
            return

        try:
            logger.info(f"📦 Loading YOLO model: {self._config.model_path}")

            # YOLO automatically downloads model if not found
            # Download location: ~/.ultralytics/weights/
            self._model = YOLO(self._config.model_path)

            # Warm up model with dummy inference
            dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            _ = self._model(dummy_frame, verbose=False)

            self._initialized = True
            logger.info(f"✅ YOLO model ready: {self._config.model_path}")

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise RuntimeError(
                f"Model loading failed: {e}. "
                "Check internet connection if this is first use (model needs to download)."
            )

    def detect(self, frame: np.ndarray) -> sv.Detections:
        """
        Run segmentation inference on frame.

        Args:
            frame: Input frame (H×W×3 RGB or H×W grayscale)

        Returns:
            Supervision Detections object with masks, boxes, and classes

        Raises:
            RuntimeError: Inference failed or model not loaded
        """
        # Lazy load model
        if not self._initialized:
            self._load_model()

        if self._model is None:
            raise RuntimeError("Model not initialized")

        try:
            # Log input frame info
            logger.debug(f"Input frame: shape={frame.shape}, dtype={frame.dtype}")

            # Run inference with confidence threshold
            results = self._model(
                frame,
                conf=self._config.confidence_threshold,
                verbose=False,
            )[0]

            # Log raw results before conversion
            if hasattr(results, 'boxes') and results.boxes is not None:
                num_boxes = len(results.boxes)
                logger.debug(f"Raw YOLO results: {num_boxes} boxes before filtering")
                if num_boxes > 0:
                    logger.debug(f"   Raw classes: {results.boxes.cls.tolist()}")
                    logger.debug(f"   Raw confidences: {results.boxes.conf.tolist()}")

            # Convert to supervision format
            detections = sv.Detections.from_ultralytics(results)

            logger.debug(
                f"🔍 Detected {len(detections)} objects with conf >= {self._config.confidence_threshold}"
            )

            if len(detections) > 0:
                logger.debug(f"   Classes found: {detections.class_id}")
                logger.debug(f"   Confidences: {detections.confidence}")

            return detections

        except Exception as e:
            logger.error(f"Detection failed: {e}")
            raise RuntimeError(f"Inference failed: {e}")

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        return self._initialized and self._model is not None

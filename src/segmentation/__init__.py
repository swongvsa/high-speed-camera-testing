"""
Object segmentation and annotation using Ultralytics and Supervision.

This module provides real-time object segmentation capabilities for the camera feed:
- YOLO-based instance segmentation
- Supervision-powered mask and label annotation
- Optional object tracking with ByteTrack
- Configurable confidence thresholds and visual styles
- Supports 80 COCO object classes
"""

from src.segmentation.annotator import FrameAnnotator
from src.segmentation.config import COCO_CLASSES, SegmentationConfig
from src.segmentation.detector import SegmentationDetector
from src.segmentation.processor import SegmentationProcessor

__all__ = [
    "SegmentationConfig",
    "SegmentationDetector",
    "FrameAnnotator",
    "SegmentationProcessor",
    "COCO_CLASSES",
]

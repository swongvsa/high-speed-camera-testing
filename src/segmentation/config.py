"""
Configuration for object segmentation and annotation.
"""

from dataclasses import dataclass
from typing import Literal, Optional, List

ModelSize = Literal["n", "s", "m", "l", "x"]


@dataclass(frozen=True)
class SegmentationConfig:
    """
    Immutable configuration for segmentation pipeline.

    Attributes:
        model_size: YOLOv8 model size (n=nano, s=small, m=medium, l=large, x=xlarge)
        confidence_threshold: Minimum confidence for detections (0.0-1.0)
        enable_tracking: Enable ByteTrack object tracking
        enable_smoothing: Enable detection smoothing
        show_labels: Display class labels on masks
        show_confidence: Display confidence scores
        mask_opacity: Transparency of segmentation masks (0.0-1.0)
        class_filter: Optional list of class IDs to detect (None = all classes)
    """

    model_size: ModelSize = "n"
    confidence_threshold: float = 0.5
    enable_tracking: bool = False
    enable_smoothing: bool = False
    show_labels: bool = True
    show_confidence: bool = True
    mask_opacity: float = 0.5
    class_filter: Optional[List[int]] = None

    def __post_init__(self):
        """Validate configuration values."""
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError(
                f"confidence_threshold must be 0.0-1.0, got {self.confidence_threshold}"
            )
        if not 0.0 <= self.mask_opacity <= 1.0:
            raise ValueError(f"mask_opacity must be 0.0-1.0, got {self.mask_opacity}")

    @property
    def model_path(self) -> str:
        """Get the model file path for the configured size."""
        return f"yolov8{self.model_size}-seg.pt"


# COCO dataset class names (80 classes)
COCO_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    4: "airplane",
    5: "bus",
    6: "train",
    7: "truck",
    8: "boat",
    9: "traffic light",
    10: "fire hydrant",
    11: "stop sign",
    12: "parking meter",
    13: "bench",
    14: "bird",
    15: "cat",
    16: "dog",
    17: "horse",
    18: "sheep",
    19: "cow",
    20: "elephant",
    21: "bear",
    22: "zebra",
    23: "giraffe",
    24: "backpack",
    25: "umbrella",
    26: "handbag",
    27: "tie",
    28: "suitcase",
    29: "frisbee",
    30: "skis",
    31: "snowboard",
    32: "sports ball",
    33: "kite",
    34: "baseball bat",
    35: "baseball glove",
    36: "skateboard",
    37: "surfboard",
    38: "tennis racket",
    39: "bottle",
    40: "wine glass",
    41: "cup",
    42: "fork",
    43: "knife",
    44: "spoon",
    45: "bowl",
    46: "banana",
    47: "apple",
    48: "sandwich",
    49: "orange",
    50: "broccoli",
    51: "carrot",
    52: "hot dog",
    53: "pizza",
    54: "donut",
    55: "cake",
    56: "chair",
    57: "couch",
    58: "potted plant",
    59: "bed",
    60: "dining table",
    61: "toilet",
    62: "tv",
    63: "laptop",
    64: "mouse",
    65: "remote",
    66: "keyboard",
    67: "cell phone",
    68: "microwave",
    69: "oven",
    70: "toaster",
    71: "sink",
    72: "refrigerator",
    73: "book",
    74: "clock",
    75: "vase",
    76: "scissors",
    77: "teddy bear",
    78: "hair drier",
    79: "toothbrush",
}

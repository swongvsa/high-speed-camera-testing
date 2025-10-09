"""
Configuration for face recognition module using DeepFace.
"""

from dataclasses import dataclass
from typing import Literal

# DeepFace supported models
ModelName = Literal[
    "VGG-Face",
    "Facenet",
    "Facenet512",
    "OpenFace",
    "DeepFace",
    "DeepID",
    "ArcFace",
    "Dlib",
    "SFace",
    "GhostFaceNet",
    "Buffalo_L",
]

# DeepFace supported detectors
DetectorBackend = Literal[
    "opencv",
    "ssd",
    "dlib",
    "mtcnn",
    "fastmtcnn",
    "retinaface",
    "mediapipe",
    "yolov8",
    "yunet",
    "centerface",
]

# Distance metrics for face comparison
DistanceMetric = Literal["cosine", "euclidean", "euclidean_l2", "angular"]


@dataclass(frozen=True)
class FaceRecognitionConfig:
    """
    Configuration for face recognition system.

    Attributes:
        model_name: Face recognition model (Facenet512 recommended)
        detector_backend: Face detection backend (retinaface recommended)
        distance_metric: Distance metric for comparison (cosine recommended)
        recognition_threshold: Threshold for face matching (0.0-1.0)
            - Lower = more lenient (more false positives)
            - Higher = stricter (more false negatives)
            - Recommended: 0.6 for cosine, 0.4 for euclidean_l2
        enable_anti_spoofing: Enable liveness detection (slower but more secure)
        enforce_detection: Raise error if no face detected
        align_faces: Align faces before processing (recommended)
        show_confidence: Show confidence scores on annotations
        show_labels: Show names on annotations
        bbox_color_known: Color for known faces (BGR)
        bbox_color_unknown: Color for unknown faces (BGR)
        bbox_thickness: Bounding box line thickness
        text_scale: Text size scale
        text_thickness: Text line thickness
    """

    # Model configuration
    model_name: ModelName = "Facenet512"
    detector_backend: DetectorBackend = "retinaface"
    distance_metric: DistanceMetric = "cosine"
    recognition_threshold: float = 0.6

    # Detection options
    enable_anti_spoofing: bool = False
    enforce_detection: bool = False
    align_faces: bool = True

    # Visual annotation
    show_confidence: bool = True
    show_labels: bool = True
    bbox_color_known: tuple[int, int, int] = (0, 255, 0)  # Green
    bbox_color_unknown: tuple[int, int, int] = (0, 0, 255)  # Red
    bbox_thickness: int = 2
    text_scale: float = 0.6
    text_thickness: int = 2

    def __post_init__(self):
        """Validate configuration."""
        if not 0.0 <= self.recognition_threshold <= 1.0:
            raise ValueError(
                f"recognition_threshold must be between 0.0 and 1.0, got {self.recognition_threshold}"
            )

        if self.bbox_thickness < 1:
            raise ValueError(f"bbox_thickness must be >= 1, got {self.bbox_thickness}")

        if self.text_scale <= 0:
            raise ValueError(f"text_scale must be > 0, got {self.text_scale}")

        if self.text_thickness < 1:
            raise ValueError(f"text_thickness must be >= 1, got {self.text_thickness}")


# Recommended thresholds per distance metric (from DeepFace research)
RECOMMENDED_THRESHOLDS = {
    "cosine": 0.40,  # Lower is more similar
    "euclidean": 0.55,
    "euclidean_l2": 0.75,
    "angular": 0.20,
}

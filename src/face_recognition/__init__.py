"""
Face recognition module using DeepFace.

Provides real-time face recognition capabilities for the camera feed:
- DeepFace-based face detection and recognition
- Multiple recognition models (Facenet512, ArcFace, VGG-Face, etc.)
- Face database management with enrollment
- Visual annotation with bounding boxes and labels
- Configurable confidence thresholds
- Optional anti-spoofing/liveness detection
"""

from src.face_recognition.annotator import FaceAnnotator
from src.face_recognition.config import (
    RECOMMENDED_THRESHOLDS,
    FaceRecognitionConfig,
)
from src.face_recognition.detector import FaceDetector
from src.face_recognition.embeddings_manager import EmbeddingsManager
from src.face_recognition.processor import FaceRecognitionProcessor
from src.face_recognition.recognizer import FaceRecognizer

__all__ = [
    "FaceRecognitionConfig",
    "FaceDetector",
    "FaceRecognizer",
    "FaceAnnotator",
    "FaceRecognitionProcessor",
    "EmbeddingsManager",
    "RECOMMENDED_THRESHOLDS",
]

"""
Camera Interface Contract

Defines the expected interface for camera device operations.
This contract specifies the API that the camera module must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class CameraInfo:
    """Camera device information"""
    device_index: int
    friendly_name: str
    port_type: str


@dataclass
class CameraCapabilities:
    """Camera hardware capabilities"""
    max_width: int
    max_height: int
    is_mono: bool


@dataclass
class CapturedFrame:
    """Single captured frame from camera"""
    data: np.ndarray
    width: int
    height: int
    channels: int
    timestamp: float
    sequence_number: int


class CameraInterface(ABC):
    """
    Abstract interface for camera device operations.

    Contract requirements:
    - enumerate_cameras() must return empty list if no cameras found
    - initialize() must raise CameraException on failure
    - capture_frame() must raise TimeoutError after specified timeout
    - release() must be idempotent (safe to call multiple times)
    - Context manager (__enter__/__exit__) must properly initialize/release
    """

    @abstractmethod
    def enumerate_cameras(self) -> List[CameraInfo]:
        """
        Enumerate all available cameras.

        Returns:
            List of CameraInfo objects, empty list if none found

        Contract:
            - Must not raise exceptions
            - Return value must be immutable after call
            - Order should be stable (same order on repeated calls)
        """
        pass

    @abstractmethod
    def initialize(self, device_index: int = 0) -> CameraCapabilities:
        """
        Initialize camera device.

        Args:
            device_index: Index of camera to initialize (default: 0)

        Returns:
            CameraCapabilities object with camera specs

        Raises:
            CameraException: If initialization fails
            IndexError: If device_index out of range

        Contract:
            - Must set camera to continuous capture mode
            - Must configure ISP output format (MONO8/BGR8)
            - Must start camera capture thread
            - Must be idempotent (calling twice on same device is safe)
        """
        pass

    @abstractmethod
    def capture_frame(self, timeout_ms: int = 200) -> CapturedFrame:
        """
        Capture single frame from camera.

        Args:
            timeout_ms: Maximum wait time in milliseconds (default: 200)

        Returns:
            CapturedFrame with image data and metadata

        Raises:
            TimeoutError: If no frame available within timeout
            CameraException: If capture fails (connection lost, etc.)

        Contract:
            - Frame data must be NumPy array (uint8)
            - For color: shape=(H, W, 3), BGR order
            - For mono: shape=(H, W), single channel
            - timestamp must be monotonic increasing
            - sequence_number must increment on each successful capture
        """
        pass

    @abstractmethod
    def release(self) -> None:
        """
        Release camera resources.

        Contract:
            - Must release camera handle
            - Must free allocated buffers
            - Must be safe to call multiple times (idempotent)
            - Must not raise exceptions (log errors instead)
        """
        pass

    @abstractmethod
    def __enter__(self):
        """Context manager entry - calls initialize()"""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - calls release()"""
        pass


class CameraException(Exception):
    """Base exception for camera operations"""
    def __init__(self, message: str, error_code: int = -1):
        super().__init__(message)
        self.error_code = error_code

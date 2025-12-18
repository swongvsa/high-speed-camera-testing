"""
Contract: CameraDevice Interface
Defines the contract for camera hardware interaction.
Maps to FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, FR-009, FR-010
"""

from typing import Protocol, Iterator
from dataclasses import dataclass
import numpy as np


@dataclass
class CameraInfo:
    """Camera enumeration information"""
    device_index: int
    friendly_name: str
    port_type: str


@dataclass
class CameraCapability:
    """Camera hardware capabilities"""
    is_mono: bool
    max_width: int
    max_height: int
    max_fps: float


class CameraDeviceProtocol(Protocol):
    """
    Contract for camera device operations.

    Lifecycle:
    1. enumerate_cameras() -> list of available cameras
    2. __init__(camera_info) -> create instance
    3. __enter__() -> initialize and start streaming
    4. capture_frames() -> yield frames continuously
    5. __exit__() -> cleanup resources
    """

    @staticmethod
    def enumerate_cameras() -> list[CameraInfo]:
        """
        Enumerate all connected cameras.

        Returns:
            List of CameraInfo objects (empty list if no cameras)

        Raises:
            CameraException: SDK initialization failed

        Contract:
            - FR-001: Must detect all available cameras
            - Returns empty list (not None) if no cameras
            - Device indices must be 0-based sequential
        """
        ...

    def __init__(self, camera_info: CameraInfo) -> None:
        """
        Create camera device instance (not initialized yet).

        Args:
            camera_info: Camera to connect to

        Contract:
            - Must accept CameraInfo from enumerate_cameras()
            - Does NOT initialize hardware (use __enter__)
        """
        ...

    def get_capability(self) -> CameraCapability:
        """
        Get camera hardware capabilities.

        Returns:
            CameraCapability with resolution and format info

        Contract:
            - FR-007: Must indicate mono vs color
            - FR-010: Must provide native max resolution
            - FR-009: Must provide max FPS capability
            - Only callable after __enter__()

        Raises:
            RuntimeError: Camera not initialized
        """
        ...

    def __enter__(self) -> 'CameraDeviceProtocol':
        """
        Initialize camera and start streaming.

        Returns:
            Self (for context manager)

        Contract:
            - FR-002: Must initialize camera for streaming
            - FR-003: Must start auto-capture mode
            - FR-009: Set to maximum FPS mode
            - FR-010: Use native resolution

        Raises:
            CameraException: Initialization or start failed
            CameraAccessDenied: Camera already in use
        """
        ...

    def capture_frames(self) -> Iterator[np.ndarray]:
        """
        Continuously yield frames from camera.

        Yields:
            np.ndarray: Frame data (H×W×C for color, H×W for mono)

        Contract:
            - FR-006: Must continuously update without manual refresh
            - Timeout allowed (skip frame), don't raise exception
            - Yields until camera error or __exit__()

        Raises:
            RuntimeError: Camera not initialized
            CameraException: Fatal camera error (not timeout)
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Release camera resources.

        Contract:
            - FR-005: Must release camera (available for other apps)
            - Must free allocated frame buffers
            - Must call SDK cleanup functions
            - Must not raise exceptions (log errors only)
        """
        ...


class CameraException(Exception):
    """Camera operation failed"""
    def __init__(self, message: str, error_code: int):
        super().__init__(message)
        self.error_code = error_code


class CameraAccessDenied(CameraException):
    """Camera already in use (single viewer enforcement)"""
    pass


# Contract Tests (to be implemented in tests/contract/)

def test_enumerate_returns_list():
    """Contract: enumerate_cameras() returns list, not None"""
    ...


def test_enumerate_no_cameras():
    """Contract: enumerate_cameras() returns [] when no cameras"""
    ...


def test_camera_lifecycle():
    """Contract: Can enumerate -> init -> enter -> capture -> exit"""
    ...


def test_camera_cleanup_on_error():
    """Contract: __exit__() called even if __enter__() fails"""
    ...


def test_single_access_enforcement():
    """Contract: Second __enter__() raises CameraAccessDenied"""
    ...


def test_capability_requires_init():
    """Contract: get_capability() before __enter__() raises RuntimeError"""
    ...


def test_capture_requires_init():
    """Contract: capture_frames() before __enter__() raises RuntimeError"""
    ...


def test_frame_format_color():
    """Contract: Color camera yields (H, W, 3) arrays"""
    ...


def test_frame_format_mono():
    """Contract: Mono camera yields (H, W) arrays"""
    ...


def test_native_resolution():
    """Contract: Frames match CameraCapability max_width/max_height"""
    ...

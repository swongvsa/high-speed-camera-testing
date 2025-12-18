"""
Test fixtures for camera-related testing.
Provides reusable pytest fixtures for unit and integration tests.

Reference: /Users/swong/dev/high-speed-camera-testing/specs/001-using-gradio-as/data-model.md
"""

import time

import numpy as np
import pytest

from src.camera.device import CameraCapability, CameraInfo
from src.camera.video_frame import VideoFrame


@pytest.fixture
def mock_camera_info() -> CameraInfo:
    """
    CameraInfo fixture for testing camera enumeration.

    Returns:
        CameraInfo: Standard test camera with USB connection

    Contract:
        - device_index >= 0
        - friendly_name must not be empty
        - port_type indicates connection type
    """
    return CameraInfo(device_index=0, friendly_name="Test Camera USB 3.0", port_type="USB")


@pytest.fixture
def mock_camera_info_gige() -> CameraInfo:
    """
    CameraInfo fixture for GigE camera testing.

    Returns:
        CameraInfo: GigE network camera
    """
    return CameraInfo(device_index=1, friendly_name="Test Camera GigE", port_type="GigE")


@pytest.fixture
def mock_camera_capability() -> CameraCapability:
    """
    CameraCapability fixture for color camera.

    Returns:
        CameraCapability: Standard 640x480 color camera at 60 FPS

    Contract:
        - max_width > 0 and max_height > 0
        - is_mono indicates sensor type
        - max_fps > 0
    """
    return CameraCapability(is_mono=False, max_width=640, max_height=480, max_fps=60.0)


@pytest.fixture
def mock_camera_capability_mono() -> CameraCapability:
    """
    CameraCapability fixture for monochrome camera.

    Returns:
        CameraCapability: Monochrome camera with higher resolution
    """
    return CameraCapability(is_mono=True, max_width=1280, max_height=1024, max_fps=120.0)


@pytest.fixture
def mock_mono_frame() -> np.ndarray:
    """
    Generate (480, 640) grayscale test frame.

    Returns:
        np.ndarray: Grayscale frame with shape (480, 640), dtype uint8

    Contract:
        - data.shape == (height, width)
        - data.dtype == np.uint8
        - Represents monochrome sensor output

    Note:
        Creates a gradient pattern for visual verification:
        - Top-left corner: dark (value ~0)
        - Bottom-right corner: bright (value ~255)
    """
    height, width = 480, 640

    # Create gradient pattern: diagonal gradient from top-left to bottom-right
    y_grad = np.linspace(0, 255, height, dtype=np.uint8).reshape(-1, 1)
    x_grad = np.linspace(0, 255, width, dtype=np.uint8).reshape(1, -1)

    # Combine gradients (average to keep in uint8 range)
    frame = ((y_grad.astype(np.uint16) + x_grad.astype(np.uint16)) // 2).astype(np.uint8)

    return frame


@pytest.fixture
def mock_color_frame() -> np.ndarray:
    """
    Generate (480, 640, 3) BGR test frame.

    Returns:
        np.ndarray: Color frame with shape (480, 640, 3), dtype uint8

    Contract:
        - data.shape == (height, width, channels)
        - data.dtype == np.uint8
        - channels == 3 (BGR format, OpenCV convention)

    Note:
        Creates a test pattern with distinct color channels:
        - Blue channel: horizontal gradient
        - Green channel: vertical gradient
        - Red channel: diagonal gradient
    """
    height, width = 480, 640

    # Create BGR frame
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Blue channel: horizontal gradient (left=0, right=255)
    frame[:, :, 0] = np.linspace(0, 255, width, dtype=np.uint8)

    # Green channel: vertical gradient (top=0, bottom=255)
    frame[:, :, 1] = np.linspace(0, 255, height, dtype=np.uint8).reshape(-1, 1)

    # Red channel: diagonal gradient
    y_grad = np.linspace(0, 255, height, dtype=np.uint8).reshape(-1, 1)
    x_grad = np.linspace(0, 255, width, dtype=np.uint8).reshape(1, -1)
    frame[:, :, 2] = ((y_grad.astype(np.uint16) + x_grad.astype(np.uint16)) // 2).astype(np.uint8)

    return frame


@pytest.fixture
def mock_blank_frame() -> np.ndarray:
    """
    Generate blank (all zeros) 640x480 color frame.

    Returns:
        np.ndarray: Black frame for testing edge cases
    """
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_video_frame_mono(mock_mono_frame) -> VideoFrame:
    """
    Complete VideoFrame fixture with monochrome data.

    Returns:
        VideoFrame: Validated monochrome video frame

    Contract:
        - Immutable (frozen dataclass)
        - All validation rules enforced
        - Ready for immediate use in tests
    """
    return VideoFrame(
        data=mock_mono_frame,
        width=640,
        height=480,
        channels=1,
        timestamp=time.time(),
        sequence_number=0,
        media_type=0x01000001,  # CAMERA_MEDIA_TYPE_MONO8
    )


@pytest.fixture
def mock_video_frame_color(mock_color_frame) -> VideoFrame:
    """
    Complete VideoFrame fixture with color data.

    Returns:
        VideoFrame: Validated color video frame

    Contract:
        - Immutable (frozen dataclass)
        - All validation rules enforced
        - BGR format (OpenCV/SDK convention)
    """
    return VideoFrame(
        data=mock_color_frame,
        width=640,
        height=480,
        channels=3,
        timestamp=time.time(),
        sequence_number=0,
        media_type=0x02000002,  # CAMERA_MEDIA_TYPE_BGR8
    )


@pytest.fixture
def frame_sequence_generator():
    """
    Factory fixture for generating frame sequences.

    Returns:
        Callable: Function that generates VideoFrame sequences

    Usage:
        generator = frame_sequence_generator
        frames = generator(count=10, is_mono=False)

    Useful for:
        - Testing streaming behavior
        - Validating sequence_number monotonicity
        - Performance testing with large frame counts
    """

    def generate_frames(count: int = 10, is_mono: bool = False) -> list[VideoFrame]:
        """
        Generate sequence of VideoFrame objects.

        Args:
            count: Number of frames to generate
            is_mono: True for monochrome, False for color

        Returns:
            List of VideoFrame objects with sequential numbers
        """
        frames = []
        base_time = time.time()

        for i in range(count):
            if is_mono:
                data = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
                channels = 1
                media_type = 0x01000001
            else:
                data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
                channels = 3
                media_type = 0x02000002

            frame = VideoFrame(
                data=data,
                width=640,
                height=480,
                channels=channels,
                timestamp=base_time + (i * 0.016),  # ~60 FPS timing
                sequence_number=i,
                media_type=media_type,
            )
            frames.append(frame)

        return frames

    return generate_frames


@pytest.fixture
def mock_sdk_constants():
    """
    SDK constant values for testing.

    Returns:
        dict: Common SDK constants used across tests

    Usage:
        constants = mock_sdk_constants
        assert frame.media_type == constants['MONO8']
    """
    return {
        "CAMERA_MEDIA_TYPE_MONO8": 0x01000001,
        "CAMERA_MEDIA_TYPE_BGR8": 0x02000002,
        "CAMERA_STATUS_SUCCESS": 0,
        "CAMERA_STATUS_TIME_OUT": -12,
        "CAMERA_STATUS_DEVICE_LOST": -4,
    }

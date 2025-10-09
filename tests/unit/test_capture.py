"""
Unit tests for frame capture service.
Tests T012 implementation.
"""

from unittest.mock import MagicMock

import numpy as np
import pytest

from src.camera.capture import create_frame_generator
from src.camera.device import CameraDevice, CameraException
from src.lib import mvsdk


def test_frame_generator_yields_frames(mock_camera):
    """Frame generator yields numpy arrays"""
    # Setup: Mock camera with 3 frames
    frames = [
        np.zeros((480, 640, 3), dtype=np.uint8),
        np.ones((480, 640, 3), dtype=np.uint8),
        np.full((480, 640, 3), 255, dtype=np.uint8),
    ]
    mock_camera.capture_frames.return_value = iter(frames)

    # Action: Generate frames
    gen = create_frame_generator(mock_camera)
    captured = list(gen)

    # Assert: Got all frames
    assert len(captured) == 3
    assert captured[0].shape == (480, 640, 3)
    assert captured[1].shape == (480, 640, 3)
    assert captured[2].shape == (480, 640, 3)


def test_frame_generator_handles_timeout(mock_camera):
    """Timeouts are skipped, not raised"""

    # Setup: Camera raises timeout exception
    def frame_gen_with_timeout():
        yield np.zeros((480, 640, 3), dtype=np.uint8)
        raise CameraException("Timeout", mvsdk.CAMERA_STATUS_TIME_OUT)

    mock_camera.capture_frames.return_value = frame_gen_with_timeout()

    # Action: Generate frames
    gen = create_frame_generator(mock_camera)
    frames = []
    for frame in gen:
        frames.append(frame)
        if len(frames) >= 10:  # Prevent infinite loop
            break

    # Assert: Got first frame, timeout was handled
    assert len(frames) >= 1


def test_frame_generator_propagates_fatal_errors(mock_camera):
    """Fatal errors (not timeout) are raised"""

    # Setup: Camera raises fatal error
    def frame_gen_with_error():
        yield np.zeros((480, 640, 3), dtype=np.uint8)
        raise CameraException("Fatal error", mvsdk.CAMERA_STATUS_DEVICE_LOST)

    mock_camera.capture_frames.return_value = frame_gen_with_error()

    # Action & Assert: Fatal error propagates
    gen = create_frame_generator(mock_camera)
    next(gen)  # First frame OK
    with pytest.raises(CameraException) as exc_info:
        next(gen)  # Second frame raises

    assert exc_info.value.error_code == mvsdk.CAMERA_STATUS_DEVICE_LOST


def test_frame_generator_sequence_numbering(mock_camera, caplog):
    """Frames are numbered sequentially in logs"""
    import logging

    caplog.set_level(logging.DEBUG)

    # Setup: Mock camera with frames
    frames = [np.zeros((480, 640), dtype=np.uint8) for _ in range(3)]
    mock_camera.capture_frames.return_value = iter(frames)

    # Action: Generate frames
    gen = create_frame_generator(mock_camera)
    list(gen)

    # Assert: Sequence numbers in logs
    log_messages = [rec.message for rec in caplog.records]
    assert any("sequence=1" in msg for msg in log_messages)
    assert any("sequence=2" in msg for msg in log_messages)
    assert any("sequence=3" in msg for msg in log_messages)


@pytest.fixture
def mock_camera():
    """Mock CameraDevice for testing"""
    camera = MagicMock(spec=CameraDevice)
    camera._initialized = True
    return camera

"""
Unit tests for camera initialization logic.
Tests T015 implementation.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.camera.init import initialize_camera
from src.camera.device import CameraInfo, CameraDevice, CameraException
from src.lib import mvsdk


def test_initialize_camera_success(mock_mvsdk):
    """Successful camera initialization"""
    from src.camera.device import CameraCapability

    # Setup: Mock camera available
    with patch("src.camera.device.CameraDevice.enumerate_cameras") as mock_enum:
        mock_enum.return_value = [
            CameraInfo(device_index=0, friendly_name="Test Camera", port_type="USB")
        ]

        with (
            patch("src.camera.device.CameraDevice.__enter__") as mock_enter,
            patch("src.camera.device.CameraDevice.get_capability") as mock_cap,
        ):
            mock_camera = MagicMock(spec=CameraDevice)
            mock_camera._initialized = True
            mock_enter.return_value = mock_camera

            mock_cap.return_value = CameraCapability(
                is_mono=False, max_width=640, max_height=480, max_fps=30.0
            )

            # Action: Initialize
            camera, error = initialize_camera()

            # Assert: Success
            assert camera is not None
            assert error is None


def test_initialize_camera_no_cameras():
    """No cameras available"""
    # Setup: No cameras found
    with patch("src.camera.device.CameraDevice.enumerate_cameras") as mock_enum:
        mock_enum.return_value = []

        # Action: Initialize
        camera, error = initialize_camera()

        # Assert: Error message
        assert camera is None
        assert error is not None
        assert "No camera detected" in error


def test_initialize_camera_init_failure(mock_mvsdk):
    """Camera initialization fails"""
    # Setup: Camera found but init fails
    with patch("src.camera.device.CameraDevice.enumerate_cameras") as mock_enum:
        mock_enum.return_value = [
            CameraInfo(device_index=0, friendly_name="Test Camera", port_type="USB")
        ]

        with patch("src.camera.device.CameraDevice.__enter__") as mock_enter:
            mock_enter.side_effect = CameraException("Init failed", mvsdk.CAMERA_STATUS_FAILED)

            # Action: Initialize
            camera, error = initialize_camera()

            # Assert: Error returned
            assert camera is None
            assert error is not None
            assert "Camera" in error or "failed" in error


def test_initialize_camera_access_denied():
    """Camera already in use"""
    from src.camera.device import CameraAccessDenied

    # Setup: Camera in use
    with patch("src.camera.device.CameraDevice.enumerate_cameras") as mock_enum:
        mock_enum.return_value = [
            CameraInfo(device_index=0, friendly_name="Test Camera", port_type="USB")
        ]

        with patch("src.camera.device.CameraDevice.__enter__") as mock_enter:
            mock_enter.side_effect = CameraAccessDenied(
                "Camera in use", mvsdk.CAMERA_STATUS_ACCESS_DENY
            )

            # Action: Initialize
            camera, error = initialize_camera()

            # Assert: Error about camera in use
            assert camera is None
            assert error is not None
            assert "in use" in error or "viewer" in error


def test_initialize_camera_logs_info(mock_mvsdk, caplog):
    """Initialization logs camera info"""
    import logging

    caplog.set_level(logging.INFO)

    # Setup: Mock camera
    with patch("src.camera.device.CameraDevice.enumerate_cameras") as mock_enum:
        mock_enum.return_value = [
            CameraInfo(device_index=0, friendly_name="Test Camera USB", port_type="USB")
        ]

        with patch("src.camera.device.CameraDevice.__enter__") as mock_enter:
            mock_camera = MagicMock(spec=CameraDevice)
            mock_enter.return_value = mock_camera

            # Action: Initialize
            camera, error = initialize_camera()

            # Assert: Logs contain camera info
            log_messages = " ".join([rec.message for rec in caplog.records])
            assert "Test Camera" in log_messages or "camera" in log_messages.lower()


@pytest.fixture
def mock_mvsdk():
    """Mock MVSDK module"""
    with patch("src.lib.mvsdk") as mock:
        mock.CAMERA_STATUS_FAILED = -1
        mock.CAMERA_STATUS_ACCESS_DENY = -45
        mock.CAMERA_STATUS_NO_DEVICE_FOUND = -16
        yield mock

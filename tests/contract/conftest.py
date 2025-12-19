"""
Pytest fixtures for contract tests.
Shared fixtures to avoid duplication and ensure consistency.
"""

from unittest.mock import MagicMock

import numpy as np
import pytest


@pytest.fixture
def mock_mvsdk(mocker):
    """Mock MVSDK module with reasonable defaults for color camera"""
    mock_sdk = mocker.patch("src.lib.mvsdk")

    # Mock camera enumeration
    mock_camera_info = MagicMock()
    mock_camera_info.device_index = 0
    mock_camera_info.friendly_name = "Test Camera"
    mock_camera_info.port_type = "USB"

    mock_sdk.CameraEnumerateDevice.return_value = [mock_camera_info]

    # Mock capability (color camera, 640x480)
    mock_cap = MagicMock()
    mock_cap.sIspCapacity.bMonoSensor = 0  # Color camera
    mock_cap.sResolutionRange.iWidthMax = 640
    mock_cap.sResolutionRange.iHeightMax = 480
    mock_cap.sFrameSpeed.uiMaxFrameRate = 60

    mock_sdk.CameraGetCapability.return_value = mock_cap
    mock_sdk.CameraInit.return_value = 12345  # Mock handle
    mock_sdk.CAMERA_MEDIA_TYPE_BGR8 = 0x02000002
    mock_sdk.CAMERA_MEDIA_TYPE_MONO8 = 0x01000001
    mock_sdk.CAMERA_STATUS_TIME_OUT = -12

    # Mock frame capture
    frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_frame_head = MagicMock()
    mock_frame_head.iWidth = 640
    mock_frame_head.iHeight = 480
    mock_frame_head.uiMediaType = mock_sdk.CAMERA_MEDIA_TYPE_BGR8
    mock_frame_head.uBytes = frame_data.nbytes

    mock_sdk.CameraGetImageBuffer.return_value = (frame_data.ctypes.data, mock_frame_head)
    mock_sdk.CameraReleaseImageBuffer.return_value = 0
    mock_sdk.CameraImageProcess.return_value = 0
    mock_sdk.CameraAlignMalloc.return_value = frame_data.ctypes.data
    mock_sdk.CameraAlignFree.return_value = None
    mock_sdk.CameraPlay.return_value = 0
    mock_sdk.CameraUnInit.return_value = 0

    return mock_sdk


@pytest.fixture
def mock_mvsdk_no_camera(mocker):
    """Mock MVSDK with no cameras found"""
    mock_sdk = mocker.patch("src.lib.mvsdk")
    mock_sdk.CameraEnumerateDevice.return_value = []
    return mock_sdk


@pytest.fixture
def mock_mvsdk_color(mock_mvsdk):
    """Explicitly color camera (same as default mock_mvsdk)"""
    return mock_mvsdk


@pytest.fixture
def mock_mvsdk_mono(mocker):
    """Mock MVSDK with mono camera"""
    mock_sdk = mocker.patch("src.lib.mvsdk")

    mock_camera_info = MagicMock()
    mock_camera_info.device_index = 0
    mock_camera_info.friendly_name = "Test Mono Camera"
    mock_camera_info.port_type = "USB"

    mock_sdk.CameraEnumerateDevice.return_value = [mock_camera_info]

    # Mono camera capability
    mock_cap = MagicMock()
    mock_cap.sIspCapacity.bMonoSensor = 1  # Mono camera
    mock_cap.sResolutionRange.iWidthMax = 640
    mock_cap.sResolutionRange.iHeightMax = 480

    mock_sdk.CameraGetCapability.return_value = mock_cap
    mock_sdk.CameraInit.return_value = 12345
    mock_sdk.CAMERA_MEDIA_TYPE_BGR8 = 0x02000002
    mock_sdk.CAMERA_MEDIA_TYPE_MONO8 = 0x01000001

    # Mock mono frame capture
    frame_data = np.zeros((480, 640), dtype=np.uint8)
    mock_frame_head = MagicMock()
    mock_frame_head.iWidth = 640
    mock_frame_head.iHeight = 480
    mock_frame_head.uiMediaType = mock_sdk.CAMERA_MEDIA_TYPE_MONO8
    mock_frame_head.uBytes = frame_data.nbytes

    mock_sdk.CameraGetImageBuffer.return_value = (frame_data.ctypes.data, mock_frame_head)

    return mock_sdk

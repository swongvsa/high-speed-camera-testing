"""
Integration test for Scenario 4: Resource cleanup.

Reference: specs/001-using-gradio-as/quickstart.md Scenario 4
Maps to FR-005 (camera resource cleanup)
"""

from unittest.mock import MagicMock, patch

from src.camera.device import CameraDevice, CameraInfo


def test_camera_cleanup_on_disconnect():
    """
    Scenario 4: Given streaming active, when browser closes,
    then camera resources released.
    """
    with patch("src.camera.device.mvsdk") as mock_sdk:
        # Setup mock
        mock_dev_info = MagicMock()
        mock_dev_info.GetFriendlyName.return_value = "Test Camera"
        mock_dev_info.GetPortType.return_value = "USB"
        mock_sdk.CameraEnumerateDevice.return_value = [mock_dev_info]

        mock_cap = MagicMock()
        mock_cap.sResolutionRange.iWidthMax = 640
        mock_cap.sResolutionRange.iHeightMax = 480
        mock_cap.sFrameSpeed.uiMaxFrameRate = 30.0
        mock_cap.sIspCapacity.bMonoSensor = 0

        mock_sdk.CameraInit.return_value = 1
        mock_sdk.CameraGetCapability.return_value = mock_cap
        mock_sdk.CameraAlignMalloc.return_value = 456

        # Create camera
        camera = CameraDevice(CameraInfo(0, "Test Camera", "USB"))
        camera.__enter__()

        # Verify camera is initialized
        assert camera._handle is not None
        assert camera._initialized == True

        # Cleanup
        camera.__exit__(None, None, None)

        # Verify cleanup
        assert camera._initialized == False
        assert camera._handle is None
        assert camera._frame_buffer is None

        # Verify SDK cleanup was called
        mock_sdk.CameraUnInit.assert_called_once()
        mock_sdk.CameraAlignFree.assert_called_once()


def test_camera_can_be_reinitialized_after_cleanup():
    """After cleanup, camera can be used again"""
    with patch("src.camera.device.mvsdk") as mock_sdk:
        # Setup mock (same as above)
        mock_dev_info = MagicMock()
        mock_dev_info.GetFriendlyName.return_value = "Test Camera"
        mock_dev_info.GetPortType.return_value = "USB"
        mock_sdk.CameraEnumerateDevice.return_value = [mock_dev_info]

        mock_cap = MagicMock()
        mock_cap.sResolutionRange.iWidthMax = 640
        mock_cap.sResolutionRange.iHeightMax = 480
        mock_cap.sFrameSpeed.uiMaxFrameRate = 30.0
        mock_cap.sIspCapacity.bMonoSensor = 0

        mock_sdk.CameraInit.return_value = 1
        mock_sdk.CameraGetCapability.return_value = mock_cap
        mock_sdk.CameraAlignMalloc.return_value = 456

        # First session
        camera1 = CameraDevice(CameraInfo(0, "Test Camera", "USB"))
        camera1.__enter__()
        camera1.__exit__(None, None, None)

        # Second session (can enumerate again)
        cameras = CameraDevice.enumerate_cameras()
        assert len(cameras) > 0

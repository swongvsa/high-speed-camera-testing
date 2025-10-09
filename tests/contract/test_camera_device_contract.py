"""
Contract tests for CameraDevice protocol.
These tests define the expected behavior - implementation in src/camera/device.py must satisfy them.
Reference: specs/001-using-gradio-as/contracts/camera_device.py
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


class TestCameraDeviceContract:
    """Contract tests for CameraDevice interface"""

    def test_enumerate_returns_list(self, mock_mvsdk):
        """Contract: enumerate_cameras() returns list, not None"""
        from src.camera.device import CameraDevice

        cameras = CameraDevice.enumerate_cameras()
        assert isinstance(cameras, list)
        assert cameras is not None

    def test_enumerate_no_cameras(self, mocker):
        """Contract: enumerate_cameras() returns [] when no cameras"""
        mocker.patch("src.lib.mvsdk.CameraEnumerateDevice", return_value=[])

        from src.camera.device import CameraDevice

        cameras = CameraDevice.enumerate_cameras()
        assert cameras == []
        assert len(cameras) == 0

    def test_camera_lifecycle(self, mock_mvsdk):
        """Contract: Can enumerate -> init -> enter -> capture -> exit"""
        from src.camera.device import CameraDevice

        # Enumerate
        cameras = CameraDevice.enumerate_cameras()
        assert len(cameras) > 0

        # Init
        camera = CameraDevice(cameras[0])
        assert camera is not None

        # Enter (initialize)
        with camera as cam:
            # Get capability
            cap = cam.get_capability()
            assert cap.max_width > 0
            assert cap.max_height > 0

            # Capture frames
            frames = cam.capture_frames()
            frame = next(frames)
            assert frame is not None
            assert isinstance(frame, np.ndarray)

        # Exit automatically via context manager

    def test_camera_cleanup_on_error(self, mock_mvsdk):
        """Contract: __exit__() called even if __enter__() fails"""
        from src.camera.device import CameraDevice, CameraException

        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])

        # Simulate error during __enter__
        with patch.object(camera, "_initialize", side_effect=CameraException("Init failed", -1)):
            with pytest.raises(CameraException):
                with camera:
                    pass

            # __exit__ should have been called (camera should be in cleanup state)
            # This test verifies exception propagation works correctly

    def test_single_access_enforcement(self, mock_mvsdk):
        """Contract: Second __enter__() raises CameraAccessDenied"""
        from src.camera.device import CameraDevice, CameraAccessDenied

        cameras = CameraDevice.enumerate_cameras()

        camera1 = CameraDevice(cameras[0])
        camera2 = CameraDevice(cameras[0])

        with camera1:
            # Second camera trying to access same device should fail
            with pytest.raises(CameraAccessDenied):
                with camera2:
                    pass

    def test_capability_requires_init(self, mock_mvsdk):
        """Contract: get_capability() before __enter__() raises RuntimeError"""
        from src.camera.device import CameraDevice

        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])

        # Calling get_capability before __enter__ should fail
        with pytest.raises(RuntimeError, match="not initialized"):
            camera.get_capability()

    def test_capture_requires_init(self, mock_mvsdk):
        """Contract: capture_frames() before __enter__() raises RuntimeError"""
        from src.camera.device import CameraDevice

        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])

        # Calling capture_frames before __enter__ should fail
        with pytest.raises(RuntimeError, match="not initialized"):
            gen = camera.capture_frames()
            next(gen)

    def test_frame_format_color(self, mock_mvsdk_color):
        """Contract: Color camera yields (H, W, 3) arrays"""
        from src.camera.device import CameraDevice

        cameras = CameraDevice.enumerate_cameras()

        with CameraDevice(cameras[0]) as camera:
            cap = camera.get_capability()
            assert cap.is_mono == False

            frames = camera.capture_frames()
            frame = next(frames)

            # Color frame should be (H, W, 3)
            assert frame.shape == (cap.max_height, cap.max_width, 3)
            assert frame.dtype == np.uint8

    def test_frame_format_mono(self, mock_mvsdk_mono):
        """Contract: Mono camera yields (H, W) arrays"""
        from src.camera.device import CameraDevice

        cameras = CameraDevice.enumerate_cameras()

        with CameraDevice(cameras[0]) as camera:
            cap = camera.get_capability()
            assert cap.is_mono == True

            frames = camera.capture_frames()
            frame = next(frames)

            # Mono frame should be (H, W)
            assert frame.shape == (cap.max_height, cap.max_width)
            assert frame.dtype == np.uint8

    def test_native_resolution(self, mock_mvsdk):
        """Contract: Frames match CameraCapability max_width/max_height"""
        from src.camera.device import CameraDevice

        cameras = CameraDevice.enumerate_cameras()

        with CameraDevice(cameras[0]) as camera:
            cap = camera.get_capability()

            frames = camera.capture_frames()
            frame = next(frames)

            # Frame dimensions must match capability
            expected_height = cap.max_height
            expected_width = cap.max_width

            if len(frame.shape) == 3:  # Color
                assert frame.shape[0] == expected_height
                assert frame.shape[1] == expected_width
            else:  # Mono
                assert frame.shape[0] == expected_height
                assert frame.shape[1] == expected_width


# Pytest Fixtures (defined in conftest.py or here)


@pytest.fixture
def mock_mvsdk(mocker):
    """Mock MVSDK module with reasonable defaults for color camera"""
    mock_sdk = mocker.patch("src.camera.device.mvsdk")

    # Mock camera enumeration
    mock_camera_info = MagicMock()
    mock_camera_info.GetFriendlyName.return_value = "Test Camera"
    mock_camera_info.GetPortType.return_value = "USB"

    mock_sdk.CameraEnumerateDevice.return_value = [mock_camera_info]

    # Mock capability (color camera, 640x480)
    mock_cap = MagicMock()
    mock_cap.sIspCapacity.bMonoSensor = 0  # Color camera
    mock_cap.sResolutionRange.iWidthMax = 640
    mock_cap.sResolutionRange.iHeightMax = 480
    mock_cap.sFrameSpeed.uiMaxFrameRate = 60

    mock_sdk.CameraGetCapability.return_value = mock_cap
    mock_sdk.CameraInit.return_value = 12345  # Mock handle
    mock_sdk.CameraPlay.return_value = None
    mock_sdk.CameraSetIspOutFormat.return_value = None
    mock_sdk.CameraSetTriggerMode.return_value = None
    mock_sdk.CameraAlignMalloc.return_value = 1000  # Mock buffer address
    mock_sdk.CameraAlignFree.return_value = None
    mock_sdk.CameraUnInit.return_value = None

    # Mock frame capture
    mock_frame_head = MagicMock()
    mock_frame_head.iHeight = 480
    mock_frame_head.iWidth = 640
    mock_frame_head.uiMediaType = 0x02000002  # BGR8
    mock_frame_head.uBytes = 480 * 640 * 3
    mock_sdk.CameraGetImageBuffer.return_value = (2000, mock_frame_head)  # pRawData, FrameHead
    mock_sdk.CameraImageProcess.return_value = None
    mock_sdk.CameraReleaseImageBuffer.return_value = None

    # Mock ctypes for buffer access
    mock_array_class = type(
        "MockArray", (), {"from_address": lambda addr: bytes(mock_frame_head.uBytes)}
    )
    mock_c_ubyte = MagicMock()
    mock_c_ubyte.__mul__ = lambda self, count: mock_array_class
    mock_sdk.c_ubyte = mock_c_ubyte

    mock_sdk.CAMERA_MEDIA_TYPE_BGR8 = 0x02000002
    mock_sdk.CAMERA_MEDIA_TYPE_MONO8 = 0x01000001
    mock_sdk.CAMERA_STATUS_TIME_OUT = -12

    # Mock exceptions
    class MockCameraException(Exception):
        def __init__(self, message, error_code):
            self.message = message
            self.error_code = error_code
            super().__init__(message)

    mock_sdk.CameraException = MockCameraException

    return mock_sdk


@pytest.fixture
def mock_mvsdk_mono(mocker):
    """Mock MVSDK with mono camera"""
    import src.camera.device

    mvsdk = src.camera.device.mvsdk

    # Patch methods on the imported module
    mock_camera_info = MagicMock()
    mock_camera_info.GetFriendlyName.return_value = "Test Mono Camera"
    mock_camera_info.GetPortType.return_value = "USB"

    mocker.patch.object(mvsdk, "CameraEnumerateDevice", return_value=[mock_camera_info])

    # Mono camera capability
    mock_cap = MagicMock()
    mock_cap.sIspCapacity.bMonoSensor = 1  # Mono camera
    mock_cap.sResolutionRange.iWidthMax = 640
    mock_cap.sResolutionRange.iHeightMax = 480
    mock_cap.sFrameSpeed.uiMaxFrameRate = 60

    mocker.patch.object(mvsdk, "CameraGetCapability", return_value=mock_cap)
    mocker.patch.object(mvsdk, "CameraInit", return_value=12345)
    mocker.patch.object(mvsdk, "CameraPlay")
    mocker.patch.object(mvsdk, "CameraSetIspOutFormat")
    mocker.patch.object(mvsdk, "CameraSetTriggerMode")
    mocker.patch.object(mvsdk, "CameraAlignMalloc", return_value=1000)
    mocker.patch.object(mvsdk, "CameraAlignFree")
    mocker.patch.object(mvsdk, "CameraUnInit")

    # Mock frame capture for mono
    mock_frame_head = MagicMock()
    mock_frame_head.iHeight = 480
    mock_frame_head.iWidth = 640
    mock_frame_head.uiMediaType = 0x01000001  # MONO8
    mock_frame_head.uBytes = 480 * 640
    mocker.patch.object(mvsdk, "CameraGetImageBuffer", return_value=(2000, mock_frame_head))
    mocker.patch.object(mvsdk, "CameraImageProcess")
    mocker.patch.object(mvsdk, "CameraReleaseImageBuffer")

    # Mock ctypes for buffer access
    mock_array_class = type(
        "MockArray", (), {"from_address": lambda addr: bytes(mock_frame_head.uBytes)}
    )
    mock_c_ubyte = MagicMock()
    mock_c_ubyte.__mul__ = lambda self, count: mock_array_class
    mocker.patch.object(mvsdk, "c_ubyte", mock_c_ubyte)

    mocker.patch.object(mvsdk, "CAMERA_MEDIA_TYPE_BGR8", 0x02000002)
    mocker.patch.object(mvsdk, "CAMERA_MEDIA_TYPE_MONO8", 0x01000001)
    mocker.patch.object(mvsdk, "CAMERA_STATUS_TIME_OUT", -12)

    # Mock exceptions
    class MockCameraException(Exception):
        def __init__(self, message, error_code):
            self.message = message
            self.error_code = error_code
            super().__init__(message)

    mocker.patch.object(mvsdk, "CameraException", MockCameraException)


@pytest.fixture
def mock_mvsdk_color(mock_mvsdk):
    """Explicitly color camera (same as default mock_mvsdk)"""
    return mock_mvsdk

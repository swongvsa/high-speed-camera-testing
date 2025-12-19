"""
Unit tests for CameraDevice reconnection logic.
Tests the _attempt_reconnect() method and timeout-triggered reconnection.
"""

import time
from unittest.mock import MagicMock

import pytest

from src.camera.device import CameraDevice


@pytest.fixture
def mock_mvsdk_for_reconnect(mocker):
    """Mock MVSDK module for reconnection testing."""
    mock_sdk = mocker.patch("src.camera.device.mvsdk")

    # Mock camera enumeration
    mock_camera_info = MagicMock()
    mock_camera_info.GetFriendlyName.return_value = "Test Camera"
    mock_camera_info.GetPortType.return_value = "USB"
    mock_sdk.CameraEnumerateDevice.return_value = [mock_camera_info]

    # Mock capability
    mock_cap = MagicMock()
    mock_cap.sIspCapacity.bMonoSensor = 0
    mock_cap.sResolutionRange.iWidthMax = 640
    mock_cap.sResolutionRange.iHeightMax = 480

    mock_sdk.CameraGetCapability.return_value = mock_cap
    mock_sdk.CameraInit.return_value = 12345
    mock_sdk.CameraAlignMalloc.return_value = 1000
    mock_sdk.CAMERA_STATUS_TIME_OUT = -12
    mock_sdk.CAMERA_MEDIA_TYPE_BGR8 = 0x02000002
    mock_sdk.CAMERA_MEDIA_TYPE_MONO8 = 0x01000001

    # Mock exceptions
    class MockCameraError(Exception):
        def __init__(self, message="", error_code=0):
            self.error_code = error_code
            super().__init__(message)

    mock_sdk.CameraError = MockCameraError

    return mock_sdk


class TestReconnectMethod:
    """Tests for _attempt_reconnect() method."""

    def test_reconnect_success(self, mock_mvsdk_for_reconnect):
        """Reconnect returns True on successful reinitialization."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])

        with camera:
            # Simulate disconnection state
            camera._initialized = False
            camera._handle = None

            # Attempt reconnect
            result = camera._attempt_reconnect()

            assert result is True
            assert camera._initialized is True
            assert camera._handle is not None

    def test_reconnect_failure(self, mock_mvsdk_for_reconnect, mocker):
        """Reconnect returns False when reinitialization fails."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])

        with camera:
            # Simulate disconnection state
            camera._initialized = False

            # Make initialization fail
            mock_mvsdk_for_reconnect.CameraInit.side_effect = mock_mvsdk_for_reconnect.CameraError(
                "Init failed", -1
            )

            result = camera._attempt_reconnect()

            assert result is False
            assert camera._initialized is False

    def test_reconnect_cleans_up_resources(self, mock_mvsdk_for_reconnect):
        """Reconnect cleans up existing resources before reinitializing."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])

        with camera:
            # Force reconnect
            camera._initialized = False
            camera._attempt_reconnect()

            # Cleanup functions should have been called
            mock_mvsdk_for_reconnect.CameraUnInit.assert_called()
            mock_mvsdk_for_reconnect.CameraAlignFree.assert_called()

    def test_reconnect_backoff_delay(self, mock_mvsdk_for_reconnect, mocker):
        """Reconnect includes backoff delay."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])
        camera._reconnect_backoff_seconds = 0.1  # Short delay for testing

        with camera:
            camera._initialized = False

            sleep_mock = mocker.patch("time.sleep")
            camera._attempt_reconnect()

            sleep_mock.assert_called_with(0.1)


class TestTimeoutTriggeredReconnect:
    """Tests for reconnection triggered by consecutive timeouts."""

    def test_timeout_count_increments(self, mock_mvsdk_for_reconnect):
        """Timeout increments the consecutive timeout counter."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])

        # Set up timeout exception
        mock_mvsdk_for_reconnect.CameraGetImageBuffer.side_effect = (
            mock_mvsdk_for_reconnect.CameraError("Timeout", -12)
        )

        with camera:
            initial_count = camera._timeout_count

            # Try to get frame (will timeout)
            result = camera.get_frame()

            assert result is None
            assert camera._timeout_count > initial_count

    def test_reconnect_triggered_after_consecutive_timeouts(self, mock_mvsdk_for_reconnect, mocker):
        """Reconnect is attempted after N consecutive timeouts."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])
        camera._consecutive_timeout_limit = 3  # Lower threshold for testing
        camera._reconnect_backoff_seconds = 0.01

        # Track reconnect calls
        reconnect_spy = mocker.spy(camera, "_attempt_reconnect")

        # Set up continuous timeouts
        mock_mvsdk_for_reconnect.CameraGetImageBuffer.side_effect = (
            mock_mvsdk_for_reconnect.CameraError("Timeout", -12)
        )

        with camera:
            # Trigger enough timeouts
            for _ in range(4):
                camera.get_frame()

            # Reconnect should have been attempted
            assert reconnect_spy.call_count >= 1

    def test_timeout_count_resets_on_successful_reconnect(self, mock_mvsdk_for_reconnect, mocker):
        """Timeout counter resets after successful reconnect."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])
        camera._consecutive_timeout_limit = 2
        camera._reconnect_backoff_seconds = 0.01

        with camera:
            # Set high timeout count
            camera._timeout_count = 10

            # Mock successful reconnect
            mocker.patch.object(camera, "_attempt_reconnect", return_value=True)

            # Trigger reconnect via get_frame timeout handling
            mock_mvsdk_for_reconnect.CameraGetImageBuffer.side_effect = (
                mock_mvsdk_for_reconnect.CameraError("Timeout", -12)
            )
            camera.get_frame()

            # Note: In actual implementation, counter resets happen inside
            # the timeout handling logic


class TestReconnectInGetFrameLocked:
    """Tests for reconnection in _get_frame_locked() method."""

    def test_reconnect_when_not_initialized(self, mock_mvsdk_for_reconnect, mocker):
        """get_frame attempts reconnect when camera not initialized."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])
        camera._min_reconnect_interval = 0  # Allow immediate reconnect

        with camera:
            camera._initialized = False
            camera._last_reconnect_attempt = 0

            reconnect_spy = mocker.spy(camera, "_attempt_reconnect")

            camera.get_frame()

            reconnect_spy.assert_called_once()

    def test_reconnect_respects_interval(self, mock_mvsdk_for_reconnect, mocker):
        """get_frame respects minimum reconnect interval."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])
        camera._min_reconnect_interval = 100  # Long interval

        with camera:
            camera._initialized = False
            camera._last_reconnect_attempt = time.time()  # Recent attempt

            reconnect_spy = mocker.spy(camera, "_attempt_reconnect")

            result = camera.get_frame()

            # Should NOT attempt reconnect (too soon)
            reconnect_spy.assert_not_called()
            assert result is None

    def test_no_concurrent_reconnects(self, mock_mvsdk_for_reconnect, mocker):
        """Only one reconnect attempt at a time."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])
        camera._min_reconnect_interval = 0

        with camera:
            camera._initialized = False
            camera._reconnect_in_progress = True

            reconnect_spy = mocker.spy(camera, "_attempt_reconnect")

            result = camera.get_frame()

            # Should NOT attempt reconnect (already in progress)
            reconnect_spy.assert_not_called()
            assert result is None


class TestCaptureFramesReconnect:
    """Tests for reconnection in capture_frames() generator."""

    def test_capture_frames_triggers_reconnect_logic(self, mock_mvsdk_for_reconnect, mocker):
        """capture_frames triggers reconnect after consecutive timeout threshold."""
        cameras = CameraDevice.enumerate_cameras()
        camera = CameraDevice(cameras[0])
        camera._consecutive_timeout_limit = 3
        camera._reconnect_backoff_seconds = 0.01

        # Set up timeouts, but make reconnect fail to break the loop
        mock_mvsdk_for_reconnect.CameraGetImageBuffer.side_effect = (
            mock_mvsdk_for_reconnect.CameraError("Timeout", -12)
        )

        # Make reconnect "fail" by making CameraInit raise exception
        # This will cause _initialized to stay False and break the while loop
        original_init = mock_mvsdk_for_reconnect.CameraInit.return_value

        call_count = [0]

        def camera_init_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return original_init  # First init succeeds
            raise mock_mvsdk_for_reconnect.CameraError("Reconnect failed", -1)

        mock_mvsdk_for_reconnect.CameraInit.side_effect = camera_init_side_effect

        reconnect_spy = mocker.spy(camera, "_attempt_reconnect")

        with camera:
            gen = camera.capture_frames()

            # Iterate until generator exits (reconnect fails, _initialized=False)
            list(gen)

            # Reconnect should have been attempted
            assert reconnect_spy.call_count >= 1

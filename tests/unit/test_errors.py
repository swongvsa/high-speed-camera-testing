"""
Unit tests for error message mapper.
Tests T013 implementation.
"""


from src.camera.errors import get_user_message
from src.lib import mvsdk


def test_no_device_found_message():
    """Error message for no camera detected"""
    msg = get_user_message(mvsdk.CAMERA_STATUS_NO_DEVICE_FOUND)
    assert "No camera detected" in msg
    assert "connect a camera" in msg


def test_device_lost_message():
    """Error message for connection lost"""
    msg = get_user_message(mvsdk.CAMERA_STATUS_DEVICE_LOST)
    assert "connection lost" in msg
    assert "reconnect" in msg


def test_access_denied_message():
    """Error message for camera in use"""
    msg = get_user_message(mvsdk.CAMERA_STATUS_ACCESS_DENY)
    assert "already in use" in msg
    assert "one viewer" in msg


def test_timeout_message():
    """Error message for camera timeout"""
    msg = get_user_message(mvsdk.CAMERA_STATUS_TIME_OUT)
    assert "not responding" in msg
    assert "restart" in msg


def test_network_send_error_message():
    """Error message for network communication error"""
    msg = get_user_message(mvsdk.CAMERA_STATUS_NET_SEND_ERROR)
    assert "Network send error" in msg
    assert "IP configuration" in msg or "network connection" in msg


def test_unknown_error_code():
    """Unknown error codes return default message"""
    msg = get_user_message(99999, default="Custom default")
    assert msg == "Custom default"


def test_default_message_when_not_specified():
    """Unknown error codes use default message"""
    msg = get_user_message(-9999)
    assert msg == "Camera error occurred"


def test_all_mapped_errors_are_friendly():
    """All error messages are user-friendly (no technical jargon)"""
    from src.camera.errors import ERROR_MESSAGES

    for error_code, message in ERROR_MESSAGES.items():
        # Check message is user-friendly
        assert len(message) > 20, f"Message too short: {message}"
        assert "." in message, f"Message should end with period: {message}"

        # No technical SDK codes in messages
        assert "CAMERA_STATUS" not in message
        assert "error_code" not in message
        assert str(error_code) not in message


def test_messages_provide_actionable_guidance():
    """Error messages suggest recovery actions"""
    # Check a few key errors have actionable guidance
    no_device = get_user_message(mvsdk.CAMERA_STATUS_NO_DEVICE_FOUND)
    assert "connect" in no_device or "restart" in no_device

    lost = get_user_message(mvsdk.CAMERA_STATUS_DEVICE_LOST)
    assert "check" in lost or "reconnect" in lost

    timeout = get_user_message(mvsdk.CAMERA_STATUS_TIME_OUT)
    assert "restart" in timeout

"""
Error message mapper for user-friendly error display.
Maps MVSDK error codes to human-readable messages.
Implements error handling strategy from research.md section 4.
Maps to FR-004 (friendly error messages).
"""

from src.lib import mvsdk

# Error code to user-friendly message mapping
ERROR_MESSAGES = {
    mvsdk.CAMERA_STATUS_NO_DEVICE_FOUND: (
        "No camera detected. Please connect a camera and restart."
    ),
    mvsdk.CAMERA_STATUS_DEVICE_LOST: ("Camera connection lost. Please check cable and reconnect."),
    mvsdk.CAMERA_STATUS_ACCESS_DENY: ("Camera already in use. Only one viewer allowed."),
    mvsdk.CAMERA_STATUS_TIME_OUT: ("Camera not responding. Please restart the application."),
    mvsdk.CAMERA_STATUS_FAILED: ("Camera operation failed. Please check camera connection."),
    mvsdk.CAMERA_STATUS_IO_ERROR: ("Camera I/O error. Please reconnect the camera."),
    mvsdk.CAMERA_STATUS_COMM_ERROR: ("Camera communication error. Check USB/network connection."),
    mvsdk.CAMERA_STATUS_BUS_ERROR: ("Camera bus error. Try a different USB port."),
    mvsdk.CAMERA_STATUS_DEVICE_IS_OPENED: (
        "Camera is already open. Close other applications using the camera."
    ),
    mvsdk.CAMERA_STATUS_DEVICE_IS_CLOSED: ("Camera is closed. Please restart the application."),
    mvsdk.CAMERA_STATUS_NO_MEMORY: ("Out of memory. Close other applications and try again."),
    mvsdk.CAMERA_STATUS_GRAB_FAILED: ("Failed to capture frame. Camera may have disconnected."),
    mvsdk.CAMERA_STATUS_LOST_DATA: ("Data loss detected. Camera bandwidth may be insufficient."),
    mvsdk.CAMERA_STATUS_NET_SEND_ERROR: (
        "Network send error. Check camera IP configuration and network connection."
    ),
}


def get_user_message(error_code: int, default: str = "Camera error occurred") -> str:
    """
    Convert MVSDK error code to user-friendly message.

    Args:
        error_code: MVSDK error status code
        default: Default message if error code not recognized

    Returns:
        User-friendly error message (no technical details or stack traces)

    Contract:
        - FR-004: Messages must be clear and actionable
        - No SDK error codes exposed to user
        - Messages include recovery suggestions when possible
    """
    return ERROR_MESSAGES.get(error_code, default)

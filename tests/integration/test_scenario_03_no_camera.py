"""
Integration test for Scenario 3: No camera error handling.

Reference: specs/001-using-gradio-as/quickstart.md Scenario 3
Maps to FR-004 (friendly error messages)
"""

import pytest
from unittest.mock import patch

from src.camera.init import initialize_camera


def test_no_camera_shows_error():
    """
    Scenario 3: Given no camera connected, when user accesses interface,
    then clear error message displays.
    """
    # Mock: No cameras found
    with patch("src.camera.device.CameraDevice.enumerate_cameras") as mock_enum:
        mock_enum.return_value = []

        # Action: Initialize
        camera, error = initialize_camera()

        # Assert: Error message returned
        assert camera is None
        assert error is not None
        assert "No camera detected" in error
        assert "Please connect a camera" in error


def test_error_message_is_user_friendly():
    """Error messages are clear and actionable"""
    with patch("src.camera.device.CameraDevice.enumerate_cameras") as mock_enum:
        mock_enum.return_value = []

        camera, error = initialize_camera()

        # Error should not contain technical details
        assert camera is None
        assert error is not None
        assert "error_code" not in error.lower()
        assert "exception" not in error.lower()
        assert "traceback" not in error.lower()

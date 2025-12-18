"""
Session lifecycle hooks for Gradio integration.
Implements single-session concurrency control from research.md section 3.
Maps to FR-005 (resource cleanup), FR-006a (single viewer).
"""

import logging
from typing import Optional, Union

from src.camera.device import CameraDevice, CameraInfo
from src.camera.init import initialize_camera
from src.camera.webcam import WebcamDevice
from src.ui.session import ViewerSession

logger = logging.getLogger(__name__)


class SessionLifecycle:
    """
    Handles session start/end events from Gradio interface.

    Manages:
    - Single-session enforcement (FR-006a)
    - Camera initialization on session start
    - Resource cleanup on session end (FR-005)
    """

    def __init__(self, session_manager: ViewerSession):
        """
        Initialize lifecycle manager.

        Args:
            session_manager: Session state tracker
        """
        self.session_manager = session_manager
        self.camera: Optional[Union[CameraDevice, WebcamDevice]] = None

    def on_session_start(
        self, session_hash: str, selected_camera: Optional[CameraInfo] = None
    ) -> Optional[str]:
        """
        Handle user connecting. Returns error message if blocked.

        Args:
            session_hash: Gradio session identifier (UUID)
            selected_camera: Explicitly selected camera source

        Returns:
            None if session started successfully
            Error message string if session blocked

        Contract:
            - FR-006a: Only one session allowed at a time
            - FR-002: Initialize camera on session start
            - FR-004: Return user-friendly error messages
        """
        # If camera is already initialized and it's a different one, cleanup first
        if self.camera and selected_camera:
            # Check if it's the same camera
            # (Simplification: just restart if selected_camera is provided)
            self._cleanup_camera()

        # Try to claim session slot if not already claimed
        if not self.session_manager.try_start_session(session_hash):
            # If we already have a session for this hash, it's fine
            if not self.session_manager.is_session_active(session_hash):
                return "Camera already in use. Only one viewer allowed."

        # Initialize camera
        camera, error = initialize_camera(selected_info=selected_camera)
        if error:
            # Cleanup failed session if we just tried to start it
            if self.session_manager.is_session_active(session_hash):
                self.session_manager.end_session(session_hash)
            return error

        self.camera = camera
        logger.info(f"Session started: {session_hash} with camera: {selected_camera}")
        return None

    def _cleanup_camera(self) -> None:
        """Internal helper to cleanup camera resources."""
        if self.camera:
            try:
                self.camera.__exit__(None, None, None)
            except Exception as e:
                logger.error(f"Error during camera cleanup: {e}")
            finally:
                self.camera = None

    def on_session_end(self, session_hash: str) -> None:
        """
        Handle user disconnecting. Cleanup camera resources.

        Args:
            session_hash: Gradio session identifier

        Contract:
            - FR-005: Must release camera resources
            - Must allow new sessions after cleanup
            - Must not raise exceptions (log errors only)
        """
        try:
            # Cleanup camera if active
            self._cleanup_camera()

            # Release session
            self.session_manager.end_session(session_hash)
            logger.info(f"Session ended: {session_hash}")

        except Exception as e:
            # Log but don't raise (cleanup should not fail)
            logger.error(f"Error during session cleanup: {e}")

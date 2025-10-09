"""
Session lifecycle hooks for Gradio integration.
Implements single-session concurrency control from research.md section 3.
Maps to FR-005 (resource cleanup), FR-006a (single viewer).
"""

import logging
from typing import Optional

from src.camera.device import CameraDevice, CameraException
from src.camera.errors import get_user_message
from src.camera.init import initialize_camera
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
        self.camera: Optional[CameraDevice] = None

    def on_session_start(self, session_hash: str) -> Optional[str]:
        """
        Handle user connecting. Returns error message if blocked.

        Args:
            session_hash: Gradio session identifier (UUID)

        Returns:
            None if session started successfully
            Error message string if session blocked

        Contract:
            - FR-006a: Only one session allowed at a time
            - FR-002: Initialize camera on session start
            - FR-004: Return user-friendly error messages
        """
        # Try to claim session slot
        if not self.session_manager.try_start_session(session_hash):
            return "Camera already in use. Only one viewer allowed."

        # Initialize camera
        camera, error = initialize_camera()
        if error:
            # Cleanup failed session
            self.session_manager.end_session(session_hash)
            return error

        self.camera = camera
        logger.info(f"Session started: {session_hash}")
        return None

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
            if self.camera:
                self.camera.__exit__(None, None, None)
                self.camera = None

            # Release session
            self.session_manager.end_session(session_hash)
            logger.info(f"Session ended: {session_hash}")

        except Exception as e:
            # Log but don't raise (cleanup should not fail)
            logger.error(f"Error during session cleanup: {e}")

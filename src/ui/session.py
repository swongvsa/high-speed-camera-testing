"""
ViewerSession: Single-viewer session management for camera access.
Implements the ViewerSession contract from specs/001-using-gradio-as/contracts/viewer_session.py
Maps to FR-006a, FR-005
"""

import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# ------------------------------------------------------------------
# Data Classes (from contract)
# ------------------------------------------------------------------


@dataclass
class SessionInfo:
    """Viewer session metadata"""

    session_hash: str  # Gradio session UUID
    start_time: datetime
    is_active: bool


# ------------------------------------------------------------------
# ViewerSession Implementation
# ------------------------------------------------------------------


class ViewerSession:
    """
    Thread-safe single-viewer session manager.

    Ensures only one active viewer session globally.
    Coordinates with camera device for exclusive access.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._active_session: Optional[SessionInfo] = None

    def try_start_session(self, session_hash: str) -> bool:
        """
        Attempt to start a new viewer session.

        Thread-safe implementation of contract.
        """
        with self._lock:
            # Check if session already active
            if self._active_session is not None:
                # Allow retry of same session
                if self._active_session.session_hash == session_hash:
                    return True
                # Different session active
                return False

            # Start new session
            self._active_session = SessionInfo(
                session_hash=session_hash, start_time=datetime.now(), is_active=True
            )
            return True

    def end_session(self, session_hash: str) -> None:
        """
        End an active session and release resources.

        Thread-safe implementation of contract.
        """
        with self._lock:
            if (
                self._active_session is not None
                and self._active_session.session_hash == session_hash
            ):
                self._active_session.is_active = False
                self._active_session = None

    def get_active_session(self) -> Optional[SessionInfo]:
        """
        Get currently active session info.

        Returns snapshot copy for thread safety.
        """
        with self._lock:
            if self._active_session is None:
                return None

            # Return snapshot copy
            return SessionInfo(
                session_hash=self._active_session.session_hash,
                start_time=self._active_session.start_time,
                is_active=self._active_session.is_active,
            )

    def is_session_active(self, session_hash: str) -> bool:
        """
        Check if specific session is active.
        """
        with self._lock:
            return (
                self._active_session is not None
                and self._active_session.session_hash == session_hash
                and self._active_session.is_active
            )


# ------------------------------------------------------------------
# StreamState Implementation
# ------------------------------------------------------------------


class StreamState:
    """
    Global streaming state management.

    Coordinates with ViewerSession for resource control.
    Thread-safe counters and state tracking.
    """

    def __init__(self, session_manager: ViewerSession) -> None:
        self._session_manager = session_manager
        self._lock = threading.RLock()
        self._is_streaming = False
        self._frame_count = 0
        self._error_count = 0

    def start_streaming(self, session_id: str) -> None:
        """
        Mark streaming as active for session.
        """
        if not self._session_manager.is_session_active(session_id):
            raise ValueError(f"Session {session_id} is not active")

        with self._lock:
            self._is_streaming = True

    def stop_streaming(self, session_id: str) -> None:
        """
        Mark streaming as inactive.
        """
        with self._lock:
            self._is_streaming = False
            self._error_count = 0  # Reset error counter

    def is_streaming(self) -> bool:
        """
        Check if streaming is currently active.
        """
        with self._lock:
            return self._is_streaming

    def increment_frame_count(self) -> int:
        """
        Record successful frame capture.
        """
        with self._lock:
            self._frame_count += 1
            return self._frame_count

    def increment_error_count(self) -> int:
        """
        Record frame capture error.
        """
        with self._lock:
            self._error_count += 1
            return self._error_count

    def reset_error_count(self) -> None:
        """
        Clear error counter after successful frame.
        """
        with self._lock:
            self._error_count = 0


# ------------------------------------------------------------------
# Global Instances
# ------------------------------------------------------------------

# Singleton instances for global coordination
_viewer_session = ViewerSession()
_stream_state = StreamState(_viewer_session)


def get_viewer_session() -> ViewerSession:
    """Get global viewer session manager"""
    return _viewer_session


def get_stream_state() -> StreamState:
    """Get global stream state manager"""
    return _stream_state

"""
Session Manager Contract

Defines the expected interface for viewer session management.
Ensures single concurrent viewer requirement (FR-006a).
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SessionInfo:
    """Viewer session information"""
    session_hash: str
    start_time: datetime
    is_active: bool


class SessionManagerInterface(ABC):
    """
    Abstract interface for managing viewer sessions.

    Contract requirements:
    - Only one session can be active at a time
    - Attempting second session must raise SessionBlockedError
    - Session cleanup must release camera resources
    - Thread-safe: concurrent calls must be handled safely
    """

    @abstractmethod
    def start_session(self, session_hash: str) -> SessionInfo:
        """
        Start a new viewer session.

        Args:
            session_hash: Unique session identifier from Gradio

        Returns:
            SessionInfo object for the started session

        Raises:
            SessionBlockedError: If another session is active
            ValueError: If session_hash is empty/invalid

        Contract:
            - Must check for active session before starting
            - Must be atomic (thread-safe)
            - Must set is_active=True on returned SessionInfo
            - Must initialize camera for this session
        """
        pass

    @abstractmethod
    def end_session(self, session_hash: str) -> None:
        """
        End an active viewer session.

        Args:
            session_hash: Session identifier to terminate

        Contract:
            - Must release camera resources
            - Must set is_active=False
            - Must be idempotent (safe to call multiple times)
            - Must not raise if session doesn't exist (log warning)
            - Must be atomic (thread-safe)
        """
        pass

    @abstractmethod
    def get_active_session(self) -> Optional[SessionInfo]:
        """
        Get currently active session info.

        Returns:
            SessionInfo if a session is active, None otherwise

        Contract:
            - Return value is snapshot (not live-updating)
            - Must be thread-safe
        """
        pass

    @abstractmethod
    def is_session_active(self, session_hash: str) -> bool:
        """
        Check if specific session is active.

        Args:
            session_hash: Session to check

        Returns:
            True if this session is active, False otherwise

        Contract:
            - Must return False if session doesn't exist
            - Must be thread-safe
        """
        pass

    @abstractmethod
    def cleanup_inactive_sessions(self, timeout_seconds: int = 30) -> int:
        """
        Clean up sessions inactive beyond timeout.

        Args:
            timeout_seconds: Inactivity threshold (default: 30)

        Returns:
            Number of sessions cleaned up

        Contract:
            - Must release resources for each cleaned session
            - Must be safe to call periodically
            - Must not affect active sessions
        """
        pass


class SessionBlockedError(Exception):
    """Raised when attempting to start session while another is active"""
    def __init__(self, active_session_hash: str):
        super().__init__(f"Camera in use by session: {active_session_hash}")
        self.active_session_hash = active_session_hash

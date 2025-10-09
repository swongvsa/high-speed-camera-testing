"""
Contract: ViewerSession Management
Defines the contract for single-viewer session control.
Maps to FR-006a (single viewer restriction), FR-005 (cleanup)
"""

from typing import Protocol, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SessionInfo:
    """Viewer session metadata"""
    session_hash: str  # Gradio session UUID
    start_time: datetime
    is_active: bool


class ViewerSessionProtocol(Protocol):
    """
    Contract for single-viewer session management.

    Invariants:
        - At most one active session globally
        - Active session holds exclusive camera access
        - Session cleanup releases camera resources
    """

    def try_start_session(self, session_hash: str) -> bool:
        """
        Attempt to start a new viewer session.

        Args:
            session_hash: Gradio session identifier

        Returns:
            True if session started successfully
            False if another session is already active

        Contract:
            - FR-006a: Only one active session permitted
            - Returns False (not exception) if blocked
            - Idempotent: Same session_hash can retry

        Thread Safety:
            - Must be thread-safe (use lock internally)
        """
        ...

    def end_session(self, session_hash: str) -> None:
        """
        End an active session and release resources.

        Args:
            session_hash: Session to terminate

        Contract:
            - FR-005: Must release camera resources
            - Idempotent: Ending non-existent session is no-op
            - Must clear active session flag
            - Must allow new sessions after cleanup

        Thread Safety:
            - Must be thread-safe (use lock internally)
        """
        ...

    def get_active_session(self) -> Optional[SessionInfo]:
        """
        Get currently active session info.

        Returns:
            SessionInfo if session active, None otherwise

        Contract:
            - Returns None if no active session
            - Returned info is snapshot (not live object)

        Thread Safety:
            - Must be thread-safe (read under lock)
        """
        ...

    def is_session_active(self, session_hash: str) -> bool:
        """
        Check if specific session is active.

        Args:
            session_hash: Session to check

        Returns:
            True if this session is currently active

        Contract:
            - Returns False for unknown session_hash
            - Consistent with get_active_session()

        Thread Safety:
            - Must be thread-safe (read under lock)
        """
        ...


class StreamStateProtocol(Protocol):
    """
    Contract for global streaming state management.

    Coordinates with ViewerSession for resource control.
    """

    def start_streaming(self, session_id: str) -> None:
        """
        Mark streaming as active for session.

        Args:
            session_id: Session initiating stream

        Contract:
            - Must verify session is active first
            - Sets global streaming flag
            - Increments stream start counter

        Raises:
            ValueError: Session not active
        """
        ...

    def stop_streaming(self, session_id: str) -> None:
        """
        Mark streaming as inactive.

        Args:
            session_id: Session stopping stream

        Contract:
            - Clears streaming flag
            - Resets frame/error counters
            - Idempotent (safe to call multiple times)
        """
        ...

    def is_streaming(self) -> bool:
        """
        Check if streaming is currently active.

        Returns:
            True if any session is streaming

        Contract:
            - Returns False if no active session
            - Consistent with start/stop calls
        """
        ...

    def increment_frame_count(self) -> int:
        """
        Record successful frame capture.

        Returns:
            New total frame count

        Contract:
            - Thread-safe increment
            - Monotonically increasing
        """
        ...

    def increment_error_count(self) -> int:
        """
        Record frame capture error.

        Returns:
            New total error count

        Contract:
            - Thread-safe increment
            - Triggers recovery if threshold exceeded (>10 consecutive)
        """
        ...

    def reset_error_count(self) -> None:
        """
        Clear error counter after successful frame.

        Contract:
            - Called after successful frame
            - Resets consecutive error tracking
        """
        ...


# Contract Tests (to be implemented in tests/contract/)

def test_single_session_only():
    """Contract: try_start_session() returns False if session active"""
    ...


def test_session_idempotent_start():
    """Contract: Same session_hash can retry start"""
    ...


def test_session_end_releases():
    """Contract: end_session() allows new sessions"""
    ...


def test_session_end_idempotent():
    """Contract: Ending non-existent session is no-op"""
    ...


def test_active_session_info():
    """Contract: get_active_session() returns current session"""
    ...


def test_no_active_session():
    """Contract: get_active_session() returns None when no session"""
    ...


def test_is_session_active_true():
    """Contract: is_session_active() returns True for active session"""
    ...


def test_is_session_active_false():
    """Contract: is_session_active() returns False for unknown session"""
    ...


def test_streaming_requires_session():
    """Contract: start_streaming() raises ValueError if no session"""
    ...


def test_streaming_state_toggle():
    """Contract: is_streaming() matches start/stop calls"""
    ...


def test_frame_count_increments():
    """Contract: increment_frame_count() returns monotonic values"""
    ...


def test_error_count_threshold():
    """Contract: increment_error_count() triggers recovery at 10"""
    ...


def test_error_count_reset():
    """Contract: reset_error_count() clears consecutive errors"""
    ...


def test_thread_safety_concurrent_sessions():
    """Contract: Concurrent try_start_session() only allows one"""
    ...


def test_thread_safety_frame_count():
    """Contract: Concurrent increment_frame_count() is correct"""
    ...

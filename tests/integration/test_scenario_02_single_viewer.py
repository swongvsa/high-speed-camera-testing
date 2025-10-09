"""
Integration test for Scenario 2: Single viewer restriction.

Reference: specs/001-using-gradio-as/quickstart.md Scenario 2
Maps to FR-006a (single viewer enforcement)
"""

import pytest

from src.ui.session import ViewerSession


def test_second_viewer_blocked():
    """
    Scenario 2: Given first viewer active, when second viewer connects,
    then second viewer sees "camera in use" message.
    """
    manager = ViewerSession()

    # First viewer connects
    assert manager.try_start_session("session-1") == True

    # Second viewer blocked
    assert manager.try_start_session("session-2") == False

    # After first ends, second can connect
    manager.end_session("session-1")
    assert manager.try_start_session("session-2") == True


def test_first_viewer_can_reconnect():
    """Same session can retry connection (idempotent)"""
    manager = ViewerSession()

    # First connection
    assert manager.try_start_session("session-1") == True

    # Retry same session (idempotent)
    assert manager.try_start_session("session-1") == True

    # Still blocks different session
    assert manager.try_start_session("session-2") == False


def test_session_cleanup_allows_new_connections():
    """After session ends, new sessions can start"""
    manager = ViewerSession()

    # Session 1 active
    manager.try_start_session("session-1")
    assert manager.get_active_session() is not None

    # End session
    manager.end_session("session-1")
    assert manager.get_active_session() is None

    # New session can start
    assert manager.try_start_session("session-2") == True

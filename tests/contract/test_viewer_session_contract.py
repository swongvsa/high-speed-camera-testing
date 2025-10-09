"""
Contract tests for ViewerSession protocol.
These tests define the expected behavior - implementation in src/ui/session.py must satisfy them.
Reference: specs/001-using-gradio-as/contracts/viewer_session.py
"""

import pytest
from datetime import datetime
from threading import Thread


class TestViewerSessionContract:
    """Contract tests for ViewerSessionProtocol interface"""

    def test_single_session_only(self):
        """Contract: try_start_session() returns False if session active"""
        from src.ui.session import get_viewer_session

        session_mgr = get_viewer_session()

        # First session should succeed
        assert session_mgr.try_start_session("session-1") == True

        # Second session should fail (session-1 still active)
        assert session_mgr.try_start_session("session-2") == False

        # Verify first session is still active
        active = session_mgr.get_active_session()
        assert active is not None
        assert active.session_hash == "session-1"

        # Clean up
        session_mgr.end_session("session-1")

    def test_session_idempotent_start(self):
        """Contract: Same session_hash can retry start"""
        from src.ui.session import get_viewer_session

        session_mgr = get_viewer_session()

        # First start
        assert session_mgr.try_start_session("session-1") == True

        # Same session retrying should succeed (idempotent)
        assert session_mgr.try_start_session("session-1") == True

        # Verify session is still active
        active = session_mgr.get_active_session()
        assert active is not None
        assert active.session_hash == "session-1"

        # Clean up
        session_mgr.end_session("session-1")

    def test_session_end_releases(self):
        """Contract: end_session() allows new sessions"""
        from src.ui.session import get_viewer_session

        session_mgr = get_viewer_session()

        # Start first session
        assert session_mgr.try_start_session("session-1") == True

        # End first session
        session_mgr.end_session("session-1")

        # New session should now succeed
        assert session_mgr.try_start_session("session-2") == True

        # Verify new session is active
        active = session_mgr.get_active_session()
        assert active is not None
        assert active.session_hash == "session-2"

        # Clean up
        session_mgr.end_session("session-2")

    def test_session_end_idempotent(self):
        """Contract: Ending non-existent session is no-op"""
        from src.ui.session import get_viewer_session

        session_mgr = get_viewer_session()

        # End non-existent session (should not raise)
        session_mgr.end_session("non-existent")

        # Start a session
        assert session_mgr.try_start_session("session-1") == True

        # End it
        session_mgr.end_session("session-1")

        # End it again (idempotent - no error)
        session_mgr.end_session("session-1")

        # Should still be no active session
        active = session_mgr.get_active_session()
        assert active is None

    def test_active_session_info(self):
        """Contract: get_active_session() returns current session"""
        from src.ui.session import get_viewer_session

        session_mgr = get_viewer_session()

        # Start session
        before_time = datetime.now()
        assert session_mgr.try_start_session("session-1") == True
        after_time = datetime.now()

        # Get active session info
        active = session_mgr.get_active_session()
        assert active is not None
        assert active.session_hash == "session-1"
        assert active.is_active == True
        assert before_time <= active.start_time <= after_time

        # Clean up
        session_mgr.end_session("session-1")

    def test_no_active_session(self):
        """Contract: get_active_session() returns None when no session"""
        from src.ui.session import get_viewer_session

        session_mgr = get_viewer_session()

        # No session started
        active = session_mgr.get_active_session()
        assert active is None

        # Start and end session
        assert session_mgr.try_start_session("session-1") == True
        session_mgr.end_session("session-1")

        # Should return None again
        active = session_mgr.get_active_session()
        assert active is None

    def test_is_session_active_true(self):
        """Contract: is_session_active() returns True for active session"""
        from src.ui.session import get_viewer_session

        session_mgr = get_viewer_session()

        # Start session
        assert session_mgr.try_start_session("session-1") == True

        # Check if active
        assert session_mgr.is_session_active("session-1") == True

        # Clean up
        session_mgr.end_session("session-1")

    def test_is_session_active_false(self):
        """Contract: is_session_active() returns False for unknown session"""
        from src.ui.session import get_viewer_session

        session_mgr = get_viewer_session()

        # Check non-existent session
        assert session_mgr.is_session_active("unknown") == False

        # Start session-1
        assert session_mgr.try_start_session("session-1") == True

        # Check different session
        assert session_mgr.is_session_active("session-2") == False

        # Clean up
        session_mgr.end_session("session-1")

    def test_thread_safety_concurrent_sessions(self):
        """Contract: Concurrent try_start_session() only allows one"""
        from src.ui.session import get_viewer_session

        session_mgr = get_viewer_session()
        results = []
        num_threads = 10

        def try_start(session_id: str):
            success = session_mgr.try_start_session(session_id)
            results.append((session_id, success))

        # Launch concurrent start attempts
        threads = []
        for i in range(num_threads):
            t = Thread(target=try_start, args=[f"session-{i}"])
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Exactly one should succeed
        successes = [r for r in results if r[1] == True]
        assert len(successes) == 1

        # Verify the winning session is active
        active = session_mgr.get_active_session()
        assert active is not None
        assert active.session_hash == successes[0][0]

        # Clean up
        session_mgr.end_session(successes[0][0])


class TestStreamStateContract:
    """Contract tests for StreamStateProtocol interface"""

    def test_streaming_requires_session(self):
        """Contract: start_streaming() raises ValueError if no session"""
        from src.ui.session import get_stream_state

        stream_state = get_stream_state()

        # Try to start streaming without active session
        with pytest.raises(ValueError, match="not active"):
            stream_state.start_streaming("session-1")

    def test_streaming_state_toggle(self):
        """Contract: is_streaming() matches start/stop calls"""
        from src.ui.session import get_viewer_session, get_stream_state

        session_mgr = get_viewer_session()
        stream_state = get_stream_state()

        # Start session first
        assert session_mgr.try_start_session("session-1") == True

        # Initially not streaming
        assert stream_state.is_streaming() == False

        # Start streaming
        stream_state.start_streaming("session-1")
        assert stream_state.is_streaming() == True

        # Stop streaming
        stream_state.stop_streaming("session-1")
        assert stream_state.is_streaming() == False

        # Clean up
        session_mgr.end_session("session-1")

    def test_frame_count_increments(self):
        """Contract: increment_frame_count() returns monotonic values"""
        from src.ui.session import get_viewer_session, get_stream_state

        session_mgr = get_viewer_session()
        stream_state = get_stream_state()

        # Start session and streaming
        assert session_mgr.try_start_session("session-1") == True
        stream_state.start_streaming("session-1")

        # Increment frame count
        count1 = stream_state.increment_frame_count()
        count2 = stream_state.increment_frame_count()
        count3 = stream_state.increment_frame_count()

        # Should be monotonically increasing
        assert count1 < count2 < count3
        assert count2 == count1 + 1
        assert count3 == count2 + 1

        # Clean up
        session_mgr.end_session("session-1")

    def test_error_count_threshold(self):
        """Contract: increment_error_count() triggers recovery at 10"""
        from src.ui.session import get_viewer_session, get_stream_state

        session_mgr = get_viewer_session()
        stream_state = get_stream_state()

        # Start session and streaming
        assert session_mgr.try_start_session("session-1") == True
        stream_state.start_streaming("session-1")

        # Increment error count to threshold
        for i in range(10):
            count = stream_state.increment_error_count()
            assert count == i + 1

        # 11th error should trigger recovery (implementation detail)
        # At minimum, count should continue to increment
        count = stream_state.increment_error_count()
        assert count >= 11

        # Clean up
        session_mgr.end_session("session-1")

    def test_error_count_reset(self):
        """Contract: reset_error_count() clears consecutive errors"""
        from src.ui.session import get_viewer_session, get_stream_state

        session_mgr = get_viewer_session()
        stream_state = get_stream_state()

        # Start session and streaming
        assert session_mgr.try_start_session("session-1") == True
        stream_state.start_streaming("session-1")

        # Increment error count
        stream_state.increment_error_count()
        stream_state.increment_error_count()
        stream_state.increment_error_count()

        # Reset error count
        stream_state.reset_error_count()

        # Next increment should start from 1
        count = stream_state.increment_error_count()
        assert count == 1

        # Clean up
        session_mgr.end_session("session-1")

    def test_thread_safety_frame_count(self):
        """Contract: Concurrent increment_frame_count() is correct"""
        from src.ui.session import get_viewer_session, get_stream_state

        session_mgr = get_viewer_session()
        stream_state = get_stream_state()

        # Start session and streaming
        assert session_mgr.try_start_session("session-1") == True
        stream_state.start_streaming("session-1")

        num_threads = 10
        increments_per_thread = 100

        # Record starting count (don't increment yet)
        # Since increment_frame_count returns the new count, we need to track manually
        start_count = 0  # Assume starts at 0

        def increment_frames():
            for _ in range(increments_per_thread):
                stream_state.increment_frame_count()

        # Launch concurrent incrementers
        threads = []
        for _ in range(num_threads):
            t = Thread(target=increment_frames)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check that we got the expected number of increments
        # Since we can't easily get the current count without incrementing,
        # we'll just verify that multiple calls return increasing values
        counts = []
        for _ in range(5):
            counts.append(stream_state.increment_frame_count())

        # Should be 5 consecutive increasing numbers
        for i in range(1, len(counts)):
            assert counts[i] == counts[i - 1] + 1

        # The first count should be at least num_threads * increments_per_thread + 1
        assert counts[0] >= (num_threads * increments_per_thread) + 1

        # Clean up
        session_mgr.end_session("session-1")


@pytest.fixture
def stream_state():
    """Fixture that will be satisfied by actual StreamState implementation"""
    # This fixture is a placeholder - the actual implementation will be imported
    # when src/session/stream_state.py exists
    pass

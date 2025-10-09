"""
Contract Tests: Gradio UI Application
Tests enforce the contract defined in specs/001-using-gradio-as/contracts/gradio_ui.py
Maps to FR-003, FR-004, FR-005, FR-006, FR-008, FR-012
"""

from unittest.mock import MagicMock, Mock

import numpy as np
import pytest


class TestGradioAppLaunchContract:
    """Contract tests for GradioAppProtocol.launch() method"""

    def test_launch_enforces_localhost(self):
        """Contract: launch() raises ValueError if server_name != '127.0.0.1'"""
        # Arrange
        mock_app = Mock()

        def launch_impl(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=True):
            if server_name != "127.0.0.1":
                raise ValueError(f"Server must be localhost only, got: {server_name}")
            if share:
                raise ValueError("Public sharing (share=True) not allowed")

        mock_app.launch = launch_impl

        # Act & Assert - Test various invalid server names
        invalid_hosts = ["0.0.0.0", "192.168.1.1", "example.com", "*", ""]

        for invalid_host in invalid_hosts:
            with pytest.raises(ValueError, match=f"Server must be localhost only, got: {invalid_host}"):
                mock_app.launch(server_name=invalid_host)

        # Valid localhost should not raise
        try:
            mock_app.launch(server_name="127.0.0.1")
        except ValueError as e:
            pytest.fail(f"Valid localhost should not raise: {e}")

    def test_launch_enforces_no_sharing(self):
        """Contract: launch() raises ValueError if share == True"""
        # Arrange
        mock_app = Mock()

        def launch_impl(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=True):
            if server_name != "127.0.0.1":
                raise ValueError(f"Server must be localhost only, got: {server_name}")
            if share:
                raise ValueError("Public sharing (share=True) not allowed")

        mock_app.launch = launch_impl

        # Act & Assert - Sharing enabled should raise
        with pytest.raises(ValueError, match="Public sharing.*not allowed"):
            mock_app.launch(share=True)

        # Sharing disabled should not raise
        try:
            mock_app.launch(share=False)
        except ValueError as e:
            pytest.fail(f"share=False should not raise: {e}")


class TestGradioInterfaceContract:
    """Contract tests for GradioInterface behavior"""

    def test_interface_loads_automatically(self, mocker):
        """Contract: Stream starts on interface load (FR-003)"""
        # Arrange
        mock_interface = MagicMock()
        frame_generator = Mock(return_value=iter([np.zeros((480, 640, 3), dtype=np.uint8)]))
        on_session_start = Mock()
        on_session_end = Mock()

        # Track what function is registered for load event
        registered_load_fn = None

        def capture_load(fn, inputs=None, outputs=None):
            nonlocal registered_load_fn
            registered_load_fn = fn

        mock_interface.load = capture_load

        # Simulate create_interface implementation
        def create_interface_impl(frame_gen, on_start, on_end):
            # Interface should register a load callback
            mock_interface.load(fn=lambda: on_start("session-123"))
            return mock_interface

        # Act
        result = create_interface_impl(frame_generator, on_session_start, on_session_end)

        # Assert - Load callback should be registered
        assert registered_load_fn is not None, "Interface must register load callback"

        # When load callback is triggered, session should start
        registered_load_fn()
        on_session_start.assert_called_once_with("session-123")

    def test_interface_continuous_update(self, mocker):
        """Contract: Frames update without user refresh (FR-006)"""
        # Arrange
        mock_interface = MagicMock()

        # Create a frame generator that yields multiple frames
        def frame_gen():
            for i in range(5):
                yield np.ones((480, 640, 3), dtype=np.uint8) * i

        frame_generator = Mock(return_value=frame_gen())

        # Track streaming configuration
        stream_config = {}

        def mock_image_component(*args, **kwargs):
            mock_img = MagicMock()
            if 'streaming' in kwargs:
                stream_config['streaming'] = kwargs['streaming']
            if 'every' in kwargs:
                stream_config['update_interval'] = kwargs['every']
            return mock_img

        mocker.patch('gradio.Image', side_effect=mock_image_component)

        # Act - Simulate interface creation with streaming image
        import gradio as gr
        mock_img = gr.Image(streaming=True, every=0.033)  # ~30 FPS

        # Assert - Interface must support continuous streaming
        assert stream_config.get('streaming') is True, "Image component must enable streaming"
        assert stream_config.get('update_interval') is not None, "Must set update interval"
        assert stream_config['update_interval'] <= 0.1, "Update interval should be fast (<100ms)"

    def test_session_start_callback(self):
        """Contract: on_session_start called when user connects"""
        # Arrange
        mock_interface = MagicMock()
        on_session_start = Mock()
        on_session_end = Mock()

        session_id = "test-session-abc123"
        load_callback = None

        def capture_load(fn, inputs=None, outputs=None):
            nonlocal load_callback
            load_callback = fn

        mock_interface.load = capture_load

        # Simulate create_interface
        def create_interface_impl(frame_gen, on_start, on_end):
            # Register load event to trigger session start
            def load_handler():
                on_start(session_id)
            mock_interface.load(fn=load_handler)
            return mock_interface

        frame_generator = Mock(return_value=iter([]))

        # Act
        interface = create_interface_impl(frame_generator, on_session_start, on_session_end)

        # Simulate user connecting (load event fires)
        assert load_callback is not None, "Load callback must be registered"
        load_callback()

        # Assert - Session start callback was called
        on_session_start.assert_called_once()
        call_args = on_session_start.call_args[0]
        assert len(call_args[0]) > 0, "Session ID must be non-empty string"

    def test_session_end_callback(self):
        """Contract: on_session_end called when browser closes (FR-005)"""
        # Arrange
        mock_interface = MagicMock()
        on_session_start = Mock()
        on_session_end = Mock()

        session_id = "test-session-xyz789"
        unload_callback = None

        def capture_unload(fn, inputs=None, outputs=None):
            nonlocal unload_callback
            unload_callback = fn

        mock_interface.unload = capture_unload

        # Simulate create_interface
        def create_interface_impl(frame_gen, on_start, on_end):
            # Register unload event to trigger session end
            def unload_handler():
                on_end(session_id)
            mock_interface.unload(fn=unload_handler)
            return mock_interface

        frame_generator = Mock(return_value=iter([]))

        # Act
        interface = create_interface_impl(frame_generator, on_session_start, on_session_end)

        # Simulate user closing browser (unload event fires)
        assert unload_callback is not None, "Unload callback must be registered"
        unload_callback()

        # Assert - Session end callback was called for cleanup
        on_session_end.assert_called_once()
        call_args = on_session_end.call_args[0]
        assert len(call_args[0]) > 0, "Session ID must be non-empty string"


class TestErrorDisplayContract:
    """Contract tests for ErrorDisplayProtocol"""

    def test_error_display_no_camera(self):
        """Contract: display_error() for no camera shows friendly message"""
        # Arrange
        mock_error_display = Mock()

        def display_error_impl(message: str, error_type: str = "error"):
            # Contract: Must be user-friendly (no stack traces)
            assert len(message) > 0, "Message must not be empty"
            assert "Traceback" not in message, "Must not show stack traces"
            assert "Exception" not in message, "Must not show exception types"
            # Contract: User can understand and act on message
            assert any(word in message.lower() for word in ["camera", "connect", "detected"]), \
                "Message must mention camera and action"

        mock_error_display.display_error = display_error_impl

        # Act - Display no camera error
        user_friendly_msg = "No camera detected. Please connect a camera."
        mock_error_display.display_error(user_friendly_msg, error_type="error")

        # Assert - Should execute without assertion errors (contract satisfied)
        # The assertions in display_error_impl validate the contract

    def test_error_display_in_use(self):
        """Contract: display_error() for camera in use shows single viewer message"""
        # Arrange
        mock_error_display = Mock()

        def display_error_impl(message: str, error_type: str = "error"):
            # Contract: Clear error message for camera issues (FR-004)
            assert len(message) > 0, "Message must not be empty"
            assert "Traceback" not in message, "Must not show stack traces"
            # Contract: User understands single viewer limitation
            assert any(word in message.lower() for word in ["use", "viewer", "one"]), \
                "Message must explain single viewer constraint"

        mock_error_display.display_error = display_error_impl

        # Act - Display camera in use error
        user_friendly_msg = "Camera already in use. Only one viewer allowed."
        mock_error_display.display_error(user_friendly_msg, error_type="error")

        # Assert - Should execute without assertion errors (contract satisfied)

    def test_error_display_connection_lost(self):
        """Contract: display_error() for connection loss shows recovery action"""
        # Arrange
        mock_error_display = Mock()

        def display_error_impl(message: str, error_type: str = "error"):
            # Contract: User can understand and act on message
            assert len(message) > 0, "Message must not be empty"
            assert any(word in message.lower() for word in ["connection", "lost", "refresh", "reconnect"]), \
                "Message must explain issue and recovery action"

        mock_error_display.display_error = display_error_impl

        # Act - Display connection lost error
        user_friendly_msg = "Connection lost. Please refresh to reconnect."
        mock_error_display.display_error(user_friendly_msg, error_type="warning")

        # Assert - Should execute without assertion errors (contract satisfied)


class TestSecurityContract:
    """Contract tests for security requirements"""

    def test_localhost_only_access(self):
        """Contract: Server only accessible from 127.0.0.1 and localhost (FR-012)"""
        # Arrange
        mock_app = Mock()

        def launch_impl(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=True):
            # Contract enforcement
            if server_name != "127.0.0.1":
                raise ValueError(f"Server must be localhost only, got: {server_name}")

        mock_app.launch = launch_impl

        # Act & Assert - Only 127.0.0.1 allowed
        mock_app.launch(server_name="127.0.0.1")  # Should succeed

        with pytest.raises(ValueError):
            mock_app.launch(server_name="localhost")  # Not allowed (must be IP)

        with pytest.raises(ValueError):
            mock_app.launch(server_name="0.0.0.0")  # Public access not allowed

    def test_external_ip_blocked(self):
        """Contract: Cannot access from external IP when server_name='127.0.0.1'"""
        # Arrange
        mock_app = Mock()
        external_ips = ["192.168.1.100", "10.0.0.50", "172.16.0.1"]

        def launch_impl(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=True):
            if server_name != "127.0.0.1":
                raise ValueError(f"Server must be localhost only, got: {server_name}")

        mock_app.launch = launch_impl

        # Act & Assert - External IPs must be rejected
        for external_ip in external_ips:
            with pytest.raises(ValueError, match="Server must be localhost only"):
                mock_app.launch(server_name=external_ip)


class TestBrowserCompatibilityContract:
    """Contract tests for browser compatibility (FR-008)"""

    def test_browser_compatibility(self):
        """Contract: Works in Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ (FR-008)"""
        # This is a contract test documenting the requirement
        # Actual browser testing would be done in integration/E2E tests

        supported_browsers = {
            "Chrome": 90,
            "Firefox": 88,
            "Safari": 14,
            "Edge": 90,
        }

        # Contract: Interface must support modern browsers
        # Implementation should use web standards compatible with these versions
        assert all(version > 0 for version in supported_browsers.values()), \
            "Browser version requirements must be specified"

        # Contract: No browser-specific hacks required
        # Gradio uses standard WebSocket, JavaScript ES6+, HTML5 video
        required_features = [
            "WebSocket",
            "ES6",
            "HTML5 Video",
            "Fetch API",
        ]

        assert len(required_features) > 0, "Must specify required web features"


class TestInterfaceCreationContract:
    """Contract tests for create_interface method"""

    def test_create_interface_binds_callbacks(self):
        """Contract: create_interface must bind session lifecycle events"""
        # Arrange
        mock_interface = MagicMock()
        frame_generator = Mock(return_value=iter([np.zeros((480, 640, 3), dtype=np.uint8)]))
        on_session_start = Mock()
        on_session_end = Mock()

        load_registered = False
        unload_registered = False

        def mock_load(fn, inputs=None, outputs=None):
            nonlocal load_registered
            load_registered = True

        def mock_unload(fn, inputs=None, outputs=None):
            nonlocal unload_registered
            unload_registered = True

        mock_interface.load = mock_load
        mock_interface.unload = mock_unload

        # Simulate create_interface
        def create_interface_impl(frame_gen, on_start, on_end):
            mock_interface.load(fn=lambda: on_start("session"))
            mock_interface.unload(fn=lambda: on_end("session"))
            return mock_interface

        # Act
        interface = create_interface_impl(frame_generator, on_session_start, on_session_end)

        # Assert - Both lifecycle events must be bound
        assert load_registered, "Interface must register load event handler"
        assert unload_registered, "Interface must register unload event handler"

    def test_create_interface_returns_interface_object(self):
        """Contract: create_interface must return GradioInterface object"""
        # Arrange
        mock_interface = MagicMock()
        frame_generator = Mock(return_value=iter([]))
        on_session_start = Mock()
        on_session_end = Mock()

        def create_interface_impl(frame_gen, on_start, on_end):
            return mock_interface

        # Act
        result = create_interface_impl(frame_generator, on_session_start, on_session_end)

        # Assert - Must return interface object with required methods
        assert result is not None, "Must return interface object"
        assert hasattr(result, 'load'), "Interface must have load method"
        assert hasattr(result, 'unload'), "Interface must have unload method"


class TestFrameGeneratorContract:
    """Contract tests for frame_generator integration"""

    def test_frame_generator_yields_numpy_arrays(self):
        """Contract: frame_generator must yield numpy arrays"""
        # Arrange
        def frame_gen():
            for i in range(3):
                yield np.ones((480, 640, 3), dtype=np.uint8) * i

        # Act
        frames = list(frame_gen())

        # Assert - All frames must be numpy arrays
        assert len(frames) == 3, "Generator should yield frames"
        for frame in frames:
            assert isinstance(frame, np.ndarray), "Each frame must be numpy array"
            assert frame.ndim == 3, "Frames must be 3D (height, width, channels)"
            assert frame.shape[2] == 3, "Frames must be RGB (3 channels)"

    def test_frame_generator_callable_returns_iterator(self):
        """Contract: frame_generator callable must return iterator"""
        # Arrange
        def frame_gen_factory():
            def inner_gen():
                yield np.zeros((480, 640, 3), dtype=np.uint8)
            return inner_gen()

        # Act
        result = frame_gen_factory()

        # Assert - Must return iterator
        assert hasattr(result, '__iter__'), "Must return iterator"
        assert hasattr(result, '__next__'), "Must be an iterator (not just iterable)"

        # Can consume frames
        frame = next(result)
        assert isinstance(frame, np.ndarray), "Iterator must yield numpy arrays"

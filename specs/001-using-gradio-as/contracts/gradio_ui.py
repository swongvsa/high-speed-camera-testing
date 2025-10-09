"""
Contract: Gradio UI Application
Defines the contract for web interface behavior.
Maps to FR-008, FR-012 (browser access, localhost-only)
"""

from typing import Protocol, Callable, Iterator
import numpy as np


class GradioAppProtocol(Protocol):
    """
    Contract for Gradio application interface.

    Lifecycle:
        1. create_interface() -> Gradio Blocks/Interface
        2. launch(server_name="127.0.0.1") -> Start server
        3. User connects -> session events trigger
        4. User disconnects -> cleanup via session end
    """

    def create_interface(
        self,
        frame_generator: Callable[[], Iterator[np.ndarray]],
        on_session_start: Callable[[str], None],
        on_session_end: Callable[[str], None],
    ) -> 'GradioInterface':
        """
        Create Gradio interface with camera stream.

        Args:
            frame_generator: Function that yields camera frames
            on_session_start: Callback when user connects
            on_session_end: Callback when user disconnects

        Returns:
            Gradio Interface/Blocks object

        Contract:
            - FR-008: Must support modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
            - FR-003: Auto-start stream on interface load
            - FR-006: Continuous update without manual refresh
            - Must bind session lifecycle events
        """
        ...

    def launch(
        self,
        server_name: str = "127.0.0.1",
        server_port: int = 7860,
        share: bool = False,
        inbrowser: bool = True,
    ) -> None:
        """
        Launch Gradio web server.

        Args:
            server_name: Host to bind (default localhost)
            server_port: Port number
            share: Enable public URL (default False)
            inbrowser: Auto-open browser (default True)

        Contract:
            - FR-012: server_name MUST be "127.0.0.1" (localhost only)
            - share MUST be False (no public URLs)
            - Must start server and block until shutdown

        Raises:
            ValueError: If server_name != "127.0.0.1"
            ValueError: If share == True
        """
        if server_name != "127.0.0.1":
            raise ValueError(f"Server must be localhost only, got: {server_name}")
        if share:
            raise ValueError("Public sharing (share=True) not allowed")
        ...


class GradioInterface(Protocol):
    """
    Contract for Gradio interface object.
    """

    def load(self, fn: Callable, inputs=None, outputs=None) -> None:
        """
        Register callback for interface load event.

        Args:
            fn: Function to call on load
            inputs: Input components (optional)
            outputs: Output components (optional)

        Contract:
            - Called when user opens interface
            - Used for session initialization
        """
        ...

    def unload(self, fn: Callable, inputs=None, outputs=None) -> None:
        """
        Register callback for interface unload event.

        Args:
            fn: Function to call on unload
            inputs: Input components (optional)
            outputs: Output components (optional)

        Contract:
            - FR-005: Called when browser closes/navigates away
            - Used for camera cleanup
        """
        ...


class ErrorDisplayProtocol(Protocol):
    """
    Contract for displaying errors to user.
    """

    def display_error(self, message: str, error_type: str = "error") -> None:
        """
        Show user-friendly error message in UI.

        Args:
            message: Error message to display
            error_type: Severity ("error", "warning", "info")

        Contract:
            - FR-004: Clear error messages for camera issues
            - No stack traces shown to user
            - User can understand and act on message

        Examples:
            - "No camera detected. Please connect a camera."
            - "Camera already in use. Only one viewer allowed."
            - "Connection lost. Please refresh to reconnect."
        """
        ...


# Contract Tests (to be implemented in tests/contract/)

def test_launch_enforces_localhost():
    """Contract: launch() raises ValueError if server_name != '127.0.0.1'"""
    ...


def test_launch_enforces_no_sharing():
    """Contract: launch() raises ValueError if share == True"""
    ...


def test_interface_loads_automatically():
    """Contract: Stream starts on interface load (FR-003)"""
    ...


def test_interface_continuous_update():
    """Contract: Frames update without user refresh (FR-006)"""
    ...


def test_session_start_callback():
    """Contract: on_session_start called when user connects"""
    ...


def test_session_end_callback():
    """Contract: on_session_end called when browser closes (FR-005)"""
    ...


def test_error_display_no_camera():
    """Contract: display_error() for no camera shows friendly message"""
    ...


def test_error_display_in_use():
    """Contract: display_error() for camera in use shows single viewer message"""
    ...


def test_browser_compatibility():
    """Contract: Works in Chrome 90+, Firefox 88+, Safari 14+, Edge 90+"""
    ...


def test_localhost_only_access():
    """Contract: Server only accessible from 127.0.0.1 and localhost"""
    ...


def test_external_ip_blocked():
    """Contract: Cannot access from external IP when server_name='127.0.0.1'"""
    ...

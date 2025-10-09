"""
UI Interface Contract

Defines the expected interface for Gradio web interface.
Specifies how UI components interact with camera and session management.
"""

from abc import ABC, abstractmethod
from typing import Generator, Optional
import numpy as np


class UIInterface(ABC):
    """
    Abstract interface for Gradio UI operations.

    Contract requirements:
    - Must provide real-time video stream via generator
    - Must handle session lifecycle (start/end)
    - Must display errors to user (no silent failures)
    - Must work with localhost-only configuration (FR-012)
    """

    @abstractmethod
    def create_interface(self) -> object:
        """
        Create Gradio interface object.

        Returns:
            Gradio Blocks or Interface object

        Contract:
            - Must configure server_name="127.0.0.1" (localhost only)
            - Must set up session load/unload event handlers
            - Must create Image component for video display
            - Must connect video_stream generator to Image component
        """
        pass

    @abstractmethod
    def video_stream(self) -> Generator[np.ndarray, None, None]:
        """
        Generate continuous video frames for display.

        Yields:
            NumPy arrays (frames) in format compatible with gr.Image

        Contract:
            - Must yield frames at camera's maximum FPS
            - Must handle frame capture timeouts gracefully
            - Must stop yielding when session ends
            - Frame format: BGR (H, W, 3) for color, (H, W) for mono
            - Must be a generator (use yield, not return)
        """
        pass

    @abstractmethod
    def on_session_start(self, session_hash: str) -> None:
        """
        Handle new session connection.

        Args:
            session_hash: Gradio session identifier

        Raises:
            SessionBlockedError: If another session is active
            CameraException: If camera initialization fails

        Contract:
            - Must attempt to start session via SessionManager
            - Must initialize camera if session accepted
            - Must display error to user if session blocked
            - Must be called from Gradio's .load() event
        """
        pass

    @abstractmethod
    def on_session_end(self, session_hash: str) -> None:
        """
        Handle session disconnect.

        Args:
            session_hash: Session identifier ending

        Contract:
            - Must end session via SessionManager
            - Must release camera resources
            - Must not raise exceptions (log errors)
            - Must be called from Gradio's .unload() event
        """
        pass

    @abstractmethod
    def launch(self, **kwargs) -> None:
        """
        Launch Gradio server.

        Keyword Args:
            server_port: Port number (default: 7860)
            inbrowser: Auto-open browser (default: True)
            **kwargs: Additional Gradio launch options

        Contract:
            - Must enforce server_name="127.0.0.1"
            - Must set share=False (no public URL)
            - Must block until server stops (CTRL+C)
            - Must clean up resources on shutdown
        """
        pass

    @abstractmethod
    def display_error(self, message: str) -> None:
        """
        Display error message to user.

        Args:
            message: Error message text

        Contract:
            - Must be visible in UI (not just console log)
            - Must not interrupt other UI operations
            - Should use Gradio's error notification system
        """
        pass

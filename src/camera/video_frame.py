"""
VideoFrame entity implementation.
Maps to FR-002, FR-006, FR-007, FR-009, FR-010
Reference: specs/001-using-gradio-as/contracts/video_frame.py
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class VideoFrame:
    """
    Immutable video frame data.

    Contract:
        - Immutable (frozen=True) - safe for multi-threaded access
        - All fields required at construction
        - Frame data is read-only after creation
    """

    data: np.ndarray  # Pixel data (H×W×C or H×W)
    width: int  # Frame width in pixels
    height: int  # Frame height in pixels
    channels: int  # 1 for mono, 3 for color
    timestamp: float  # Capture time (seconds since epoch)
    sequence_number: int  # Monotonic frame counter
    media_type: int  # SDK media type constant

    def __post_init__(self):
        """
        Validate frame integrity.

        Contract:
            - data.shape must match (height, width, channels) for color
            - data.shape must match (height, width) for mono
            - data.dtype must be uint8
            - width, height > 0
            - channels in [1, 3]
            - timestamp > 0
            - sequence_number >= 0

        Raises:
            ValueError: Validation failed
        """
        # Validate channels first
        if self.channels not in [1, 3]:
            raise ValueError(f"Invalid channel count: {self.channels}")

        # Validate dimensions
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Invalid dimensions: {self.width}×{self.height}")

        # Compute expected shape based on validated channels
        if self.channels == 3:
            expected_shape = (self.height, self.width, self.channels)
        else:
            expected_shape = (self.height, self.width)

        if self.data.shape != expected_shape:
            raise ValueError(f"Frame data shape {self.data.shape} != expected {expected_shape}")

        if self.data.dtype != np.uint8:
            raise ValueError(f"Frame data dtype {self.data.dtype} != uint8")

        if self.timestamp <= 0:
            raise ValueError(f"Invalid timestamp: {self.timestamp}")

        if self.sequence_number < 0:
            raise ValueError(f"Invalid sequence: {self.sequence_number}")

    @property
    def is_color(self) -> bool:
        """
        Contract: is_color == True iff channels == 3
        """
        return self.channels == 3

    @property
    def size_bytes(self) -> int:
        """
        Contract: Returns exact byte size of data array
        """
        return self.data.nbytes

    def to_gradio_format(self) -> np.ndarray:
        """
        Convert frame to Gradio-compatible format.

        Returns:
            np.ndarray ready for gr.Image component

        Contract:
            - Color frames: Convert BGR to RGB (H×W×3)
            - Mono frames: Return (H×W) grayscale
            - Minimal copy overhead
        """
        if self.is_color:
            # Convert BGR to RGB (camera outputs BGR, Gradio expects RGB)
            return self.data[..., ::-1]
        return self.data

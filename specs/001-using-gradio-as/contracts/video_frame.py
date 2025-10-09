"""
Contract: VideoFrame Data Structure
Defines the contract for video frame representation.
Maps to FR-002, FR-006, FR-007, FR-009, FR-010
"""

from typing import Protocol
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
        if self.channels == 3:
            expected_shape = (self.height, self.width, self.channels)
        else:
            expected_shape = (self.height, self.width)

        if self.data.shape != expected_shape:
            raise ValueError(
                f"Frame data shape {self.data.shape} != expected {expected_shape}"
            )

        if self.data.dtype != np.uint8:
            raise ValueError(f"Frame data dtype {self.data.dtype} != uint8")

        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Invalid dimensions: {self.width}×{self.height}")

        if self.channels not in [1, 3]:
            raise ValueError(f"Invalid channel count: {self.channels}")

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
            - Color frames: Return as-is (H×W×3 BGR)
            - Mono frames: Return (H×W) grayscale
            - No data copy (return view if possible)
        """
        return self.data


class VideoFrameProtocol(Protocol):
    """
    Protocol for objects that can produce VideoFrames.
    """

    def create_frame(
        self,
        data: np.ndarray,
        width: int,
        height: int,
        channels: int,
        timestamp: float,
        sequence_number: int,
        media_type: int,
    ) -> VideoFrame:
        """
        Factory method for creating validated frames.

        Contract:
            - Must validate all parameters
            - Must return immutable VideoFrame
            - Raises ValueError on invalid data
        """
        return VideoFrame(
            data=data,
            width=width,
            height=height,
            channels=channels,
            timestamp=timestamp,
            sequence_number=sequence_number,
            media_type=media_type,
        )


# Contract Tests (to be implemented in tests/contract/)

def test_frame_immutable():
    """Contract: VideoFrame is immutable (frozen)"""
    ...


def test_frame_color_shape():
    """Contract: Color frame has shape (H, W, 3)"""
    ...


def test_frame_mono_shape():
    """Contract: Mono frame has shape (H, W)"""
    ...


def test_frame_dtype():
    """Contract: Frame data is uint8"""
    ...


def test_frame_validates_shape_mismatch():
    """Contract: Raises ValueError if data.shape != (height, width, channels)"""
    ...


def test_frame_validates_channels():
    """Contract: Raises ValueError if channels not in [1, 3]"""
    ...


def test_frame_validates_dimensions():
    """Contract: Raises ValueError if width or height <= 0"""
    ...


def test_frame_validates_timestamp():
    """Contract: Raises ValueError if timestamp <= 0"""
    ...


def test_frame_validates_sequence():
    """Contract: Raises ValueError if sequence_number < 0"""
    ...


def test_is_color_property():
    """Contract: is_color == True iff channels == 3"""
    ...


def test_size_bytes_property():
    """Contract: size_bytes == data.nbytes"""
    ...


def test_to_gradio_format_color():
    """Contract: Color frames return BGR (H×W×3)"""
    ...


def test_to_gradio_format_mono():
    """Contract: Mono frames return grayscale (H×W)"""
    ...


def test_to_gradio_format_no_copy():
    """Contract: to_gradio_format() returns view when possible"""
    ...

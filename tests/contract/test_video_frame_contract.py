"""
Contract tests for VideoFrame data structure.
Reference: specs/001-using-gradio-as/contracts/video_frame.py
"""

import time

import numpy as np
import pytest


class TestVideoFrameContract:
    """Contract tests for VideoFrame dataclass"""

    def test_frame_immutable(self):
        """Contract: VideoFrame is immutable (frozen)"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = VideoFrame(
            data=frame_data,
            width=640,
            height=480,
            channels=3,
            timestamp=time.time(),
            sequence_number=0,
            media_type=0x02000002,
        )

        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            frame.width = 800

    def test_frame_color_shape(self):
        """Contract: Color frame has shape (H, W, 3)"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = VideoFrame(
            data=frame_data,
            width=640,
            height=480,
            channels=3,
            timestamp=time.time(),
            sequence_number=0,
            media_type=0x02000002,
        )

        assert frame.data.shape == (480, 640, 3)
        assert frame.channels == 3

    def test_frame_mono_shape(self):
        """Contract: Mono frame has shape (H, W)"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640), dtype=np.uint8)
        frame = VideoFrame(
            data=frame_data,
            width=640,
            height=480,
            channels=1,
            timestamp=time.time(),
            sequence_number=0,
            media_type=0x01000001,
        )

        assert frame.data.shape == (480, 640)
        assert frame.channels == 1

    def test_frame_dtype(self):
        """Contract: Frame data is uint8"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = VideoFrame(
            data=frame_data,
            width=640,
            height=480,
            channels=3,
            timestamp=time.time(),
            sequence_number=0,
            media_type=0x02000002,
        )

        assert frame.data.dtype == np.uint8

    def test_frame_validates_shape_mismatch(self):
        """Contract: Raises ValueError if data.shape != (height, width, channels)"""
        from src.camera.video_frame import VideoFrame

        # Wrong shape for color (should be 480x640x3, not 640x480x3)
        wrong_data = np.zeros((640, 480, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="shape.*expected"):
            VideoFrame(
                data=wrong_data,
                width=640,
                height=480,
                channels=3,
                timestamp=time.time(),
                sequence_number=0,
                media_type=0x02000002,
            )

    def test_frame_validates_channels(self):
        """Contract: Raises ValueError if channels not in [1, 3]"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640, 4), dtype=np.uint8)

        with pytest.raises(ValueError, match="Invalid channel count"):
            VideoFrame(
                data=frame_data,
                width=640,
                height=480,
                channels=4,  # Invalid
                timestamp=time.time(),
                sequence_number=0,
                media_type=0,
            )

    def test_frame_validates_dimensions(self):
        """Contract: Raises ValueError if width or height <= 0"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="Invalid dimensions"):
            VideoFrame(
                data=frame_data,
                width=0,  # Invalid
                height=480,
                channels=3,
                timestamp=time.time(),
                sequence_number=0,
                media_type=0,
            )

    def test_frame_validates_timestamp(self):
        """Contract: Raises ValueError if timestamp <= 0"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="Invalid timestamp"):
            VideoFrame(
                data=frame_data,
                width=640,
                height=480,
                channels=3,
                timestamp=0,  # Invalid
                sequence_number=0,
                media_type=0,
            )

    def test_frame_validates_sequence(self):
        """Contract: Raises ValueError if sequence_number < 0"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="Invalid sequence"):
            VideoFrame(
                data=frame_data,
                width=640,
                height=480,
                channels=3,
                timestamp=time.time(),
                sequence_number=-1,  # Invalid
                media_type=0,
            )

    def test_is_color_property(self):
        """Contract: is_color == True iff channels == 3"""
        from src.camera.video_frame import VideoFrame

        # Color frame
        color_data = np.zeros((480, 640, 3), dtype=np.uint8)
        color_frame = VideoFrame(
            data=color_data,
            width=640,
            height=480,
            channels=3,
            timestamp=time.time(),
            sequence_number=0,
            media_type=0x02000002,
        )
        assert color_frame.is_color == True

        # Mono frame
        mono_data = np.zeros((480, 640), dtype=np.uint8)
        mono_frame = VideoFrame(
            data=mono_data,
            width=640,
            height=480,
            channels=1,
            timestamp=time.time(),
            sequence_number=0,
            media_type=0x01000001,
        )
        assert mono_frame.is_color == False

    def test_size_bytes_property(self):
        """Contract: size_bytes == data.nbytes"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = VideoFrame(
            data=frame_data,
            width=640,
            height=480,
            channels=3,
            timestamp=time.time(),
            sequence_number=0,
            media_type=0x02000002,
        )

        assert frame.size_bytes == frame_data.nbytes
        assert frame.size_bytes == 480 * 640 * 3

    def test_to_gradio_format_color(self):
        """Contract: Color frames return BGR (H,W,3)"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = VideoFrame(
            data=frame_data,
            width=640,
            height=480,
            channels=3,
            timestamp=time.time(),
            sequence_number=0,
            media_type=0x02000002,
        )

        gradio_format = frame.to_gradio_format()
        assert gradio_format.shape == (480, 640, 3)

    def test_to_gradio_format_mono(self):
        """Contract: Mono frames return grayscale (H�W)"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640), dtype=np.uint8)
        frame = VideoFrame(
            data=frame_data,
            width=640,
            height=480,
            channels=1,
            timestamp=time.time(),
            sequence_number=0,
            media_type=0x01000001,
        )

        gradio_format = frame.to_gradio_format()
        assert gradio_format.shape == (480, 640)

    def test_to_gradio_format_no_copy(self):
        """Contract: to_gradio_format() returns view when possible"""
        from src.camera.video_frame import VideoFrame

        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = VideoFrame(
            data=frame_data,
            width=640,
            height=480,
            channels=3,
            timestamp=time.time(),
            sequence_number=0,
            media_type=0x02000002,
        )

        gradio_format = frame.to_gradio_format()

        # Should be same underlying data (view, not copy)
        assert gradio_format is frame.data or np.shares_memory(gradio_format, frame.data)

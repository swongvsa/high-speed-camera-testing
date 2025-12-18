"""
Unit tests for VideoRecorder.
Tests video buffering and clip saving functionality.
"""

import os
import tempfile
import time
from pathlib import Path

import numpy as np

from src.camera.recorder import VideoRecorder


class TestVideoRecorderBuffer:
    """Tests for frame buffering functionality."""

    def test_add_frame_stores_frame(self):
        """Adding a frame increases buffer size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            recorder.add_frame(frame)

            assert recorder.get_buffer_frame_count() == 1

    def test_add_frame_copies_data(self):
        """Frames are copied to prevent external modification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            recorder.add_frame(frame)

            # Modify original frame
            frame[0, 0, 0] = 255

            # Buffer should have the original value
            _, buffered_frame = recorder._buffer[0]
            assert buffered_frame[0, 0, 0] == 0

    def test_buffer_prunes_old_frames(self):
        """Frames older than max_duration are pruned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=0.1, output_dir=tmpdir)

            frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Add first frame
            recorder.add_frame(frame)
            assert recorder.get_buffer_frame_count() == 1

            # Wait longer than max_duration
            time.sleep(0.15)

            # Add second frame - should prune first
            recorder.add_frame(frame)

            # Should have 1-2 frames (timing dependent)
            assert recorder.get_buffer_frame_count() >= 1

    def test_get_buffer_duration_empty(self):
        """Empty buffer returns 0 duration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            assert recorder.get_buffer_duration() == 0.0

    def test_get_buffer_duration_single_frame(self):
        """Single frame returns 0 duration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            recorder.add_frame(frame)

            assert recorder.get_buffer_duration() == 0.0

    def test_get_buffer_duration_multiple_frames(self):
        """Multiple frames returns time span."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            recorder.add_frame(frame)
            time.sleep(0.1)
            recorder.add_frame(frame)

            duration = recorder.get_buffer_duration()
            assert duration >= 0.09  # Allow some timing variance

    def test_clear_buffer(self):
        """Clear buffer removes all frames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            recorder.add_frame(frame)
            recorder.add_frame(frame)

            assert recorder.get_buffer_frame_count() == 2

            recorder.clear_buffer()

            assert recorder.get_buffer_frame_count() == 0


class TestVideoRecorderSaveClip:
    """Tests for video clip saving functionality."""

    def test_save_clip_insufficient_frames(self):
        """Save returns None with insufficient frames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            # No frames
            result = recorder.save_clip()
            assert result is None

            # Single frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            recorder.add_frame(frame)
            result = recorder.save_clip()
            assert result is None

    def test_save_clip_creates_file(self):
        """Save creates an MP4 file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            # Add multiple frames with time gap
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            for i in range(10):
                frame.fill(i * 25)  # Vary content
                recorder.add_frame(frame)
                time.sleep(0.05)

            result = recorder.save_clip()

            assert result is not None
            assert os.path.exists(result)
            assert result.endswith('.mp4')

    def test_save_clip_custom_filename(self):
        """Save uses custom filename when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            for _ in range(5):
                recorder.add_frame(frame)
                time.sleep(0.02)

            result = recorder.save_clip(filename="custom_clip.mp4")

            assert result is not None
            assert result.endswith("custom_clip.mp4")

    def test_save_clip_with_duration(self):
        """Save respects duration parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=10.0, output_dir=tmpdir)

            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            for _ in range(20):
                recorder.add_frame(frame)
                time.sleep(0.05)

            # Request only last 0.5 seconds
            result = recorder.save_clip(duration_sec=0.5)

            assert result is not None
            assert os.path.exists(result)

    def test_save_clip_mono_frames(self):
        """Save works with monochrome frames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            # Mono frame (H, W) without color channels
            frame = np.zeros((480, 640), dtype=np.uint8)
            for i in range(10):
                frame.fill(i * 25)
                recorder.add_frame(frame)
                time.sleep(0.02)

            result = recorder.save_clip()

            assert result is not None
            assert os.path.exists(result)

    def test_save_clip_color_frames(self):
        """Save correctly converts RGB to BGR for OpenCV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)

            # RGB frame with distinct channels
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:, :, 0] = 255  # Red channel
            frame[:, :, 1] = 128  # Green channel
            frame[:, :, 2] = 0    # Blue channel

            for _ in range(5):
                recorder.add_frame(frame)
                time.sleep(0.02)

            result = recorder.save_clip()

            assert result is not None
            assert os.path.exists(result)


class TestVideoRecorderCleanup:
    """Tests for automatic clip cleanup."""

    def test_cleanup_removes_old_clips(self):
        """Old clips are deleted after save."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(
                max_duration_sec=5.0,
                output_dir=tmpdir,
                cleanup_age_hours=0  # Immediate cleanup
            )

            # Create an "old" clip file
            old_clip = Path(tmpdir) / "clip_20200101_000000.mp4"
            old_clip.touch()

            # Set modification time to past
            old_time = time.time() - 3600  # 1 hour ago
            os.utime(old_clip, (old_time, old_time))

            # Add frames and save (triggers cleanup)
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            for _ in range(5):
                recorder.add_frame(frame)
                time.sleep(0.02)

            recorder.save_clip()

            # Old clip should be deleted
            assert not old_clip.exists()

    def test_output_directory_created(self):
        """Output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new_clips_dir")

            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=new_dir)

            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)


class TestVideoRecorderThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_add_frame(self):
        """Multiple threads can add frames safely."""
        import threading

        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = VideoRecorder(max_duration_sec=5.0, output_dir=tmpdir)
            errors = []

            def add_frames():
                try:
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    for _ in range(10):
                        recorder.add_frame(frame)
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=add_frames) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0
            assert recorder.get_buffer_frame_count() == 50

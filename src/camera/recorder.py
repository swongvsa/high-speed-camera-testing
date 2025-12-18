"""
Video recording module for buffering and saving camera frames.

Provides circular buffer for continuous frame storage with ability to save
the last N seconds as a video clip on demand.
"""

import logging
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class VideoRecorder:
    """
    Manages frame buffering and video clip generation.

    Features:
    - Circular buffer maintaining last N seconds of frames
    - Thread-safe frame addition
    - On-demand video file generation
    - Automatic file cleanup

    Usage:
        recorder = VideoRecorder(max_duration_sec=5.0, output_dir="./clips")

        # Continuously add frames during streaming
        recorder.add_frame(frame)

        # Save last 5 seconds when user clicks record
        clip_path = recorder.save_clip(duration_sec=5.0)
    """

    def __init__(
        self,
        max_duration_sec: float = 5.0,
        output_dir: str = "./clips",
        cleanup_age_hours: int = 1,
    ):
        """
        Initialize video recorder.

        Args:
            max_duration_sec: Maximum buffer duration in seconds
            output_dir: Directory for saving video clips
            cleanup_age_hours: Auto-delete clips older than this many hours
        """
        self.max_duration_sec = max_duration_sec
        self.output_dir = Path(output_dir)
        self.cleanup_age_hours = cleanup_age_hours

        # Frame buffer: [(timestamp, frame), ...]
        self._buffer: deque = deque()
        self._lock = threading.RLock()

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"VideoRecorder initialized: max_duration={max_duration_sec}s, output_dir={output_dir}")

    def add_frame(self, frame: np.ndarray) -> None:
        """
        Add frame to circular buffer with timestamp.

        Args:
            frame: Frame data (H×W×C RGB or H×W mono)
        """
        with self._lock:
            current_time = time.time()
            self._buffer.append((current_time, frame.copy()))

            # Prune old frames beyond max duration
            cutoff_time = current_time - self.max_duration_sec
            while self._buffer and self._buffer[0][0] < cutoff_time:
                self._buffer.popleft()

    def get_buffer_duration(self) -> float:
        """
        Get current buffer duration in seconds.

        Returns:
            Duration of frames currently in buffer (0 if empty)
        """
        with self._lock:
            if len(self._buffer) < 2:
                return 0.0

            oldest_time = self._buffer[0][0]
            newest_time = self._buffer[-1][0]
            return newest_time - oldest_time

    def get_buffer_frame_count(self) -> int:
        """
        Get number of frames currently in buffer.

        Returns:
            Frame count
        """
        with self._lock:
            return len(self._buffer)

    def save_clip(
        self,
        duration_sec: Optional[float] = None,
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Save buffered frames as video clip.

        Args:
            duration_sec: Duration to save (None = all buffered frames)
            filename: Output filename (None = auto-generate with timestamp)

        Returns:
            Path to saved video file, or None if insufficient frames
        """
        with self._lock:
            if len(self._buffer) < 2:
                logger.warning("Insufficient frames in buffer for video clip")
                return None

            # Determine time range to save
            if duration_sec is None:
                duration_sec = self.get_buffer_duration()

            current_time = time.time()
            cutoff_time = current_time - duration_sec

            # Extract frames within time range
            frames_to_save = [
                (ts, frame) for ts, frame in self._buffer
                if ts >= cutoff_time
            ]

            if len(frames_to_save) < 2:
                logger.warning(f"Only {len(frames_to_save)} frames in requested duration")
                return None

            # Generate output filename
            if filename is None:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"clip_{timestamp_str}.mp4"

            output_path = self.output_dir / filename

        # Write video file (outside lock to avoid blocking frame addition)
        try:
            success = self._write_video_file(frames_to_save, output_path)
            if success:
                logger.info(f"Saved video clip: {output_path} ({len(frames_to_save)} frames, {duration_sec:.1f}s)")

                # Cleanup old files
                self._cleanup_old_clips()

                return str(output_path)
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to save video clip: {e}")
            return None

    def _write_video_file(
        self,
        frames_with_timestamps: list[tuple[float, np.ndarray]],
        output_path: Path,
    ) -> bool:
        """
        Write frames to video file using OpenCV.

        Args:
            frames_with_timestamps: List of (timestamp, frame) tuples
            output_path: Output file path

        Returns:
            True if successful, False otherwise
        """
        if not frames_with_timestamps:
            return False

        # Calculate actual FPS from timestamps
        timestamps = [ts for ts, _ in frames_with_timestamps]
        if len(timestamps) > 1:
            time_span = timestamps[-1] - timestamps[0]
            fps = (len(timestamps) - 1) / time_span if time_span > 0 else 10.0
        else:
            fps = 10.0  # Fallback

        # Limit FPS to reasonable range
        fps = max(1.0, min(fps, 60.0))

        # Get frame dimensions from first frame
        first_frame = frames_with_timestamps[0][1]
        height, width = first_frame.shape[:2]

        # Convert RGB to BGR for OpenCV
        is_color = len(first_frame.shape) == 3 and first_frame.shape[2] == 3

        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            fps,
            (width, height),
            isColor=is_color
        )

        if not writer.isOpened():
            logger.error(f"Failed to open video writer for {output_path}")
            return False

        try:
            # Write all frames
            for _, frame in frames_with_timestamps:
                if is_color:
                    # Convert RGB to BGR for OpenCV
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    writer.write(frame_bgr)
                else:
                    # Mono frame: convert to 3-channel BGR
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    writer.write(frame_bgr)

            logger.debug(f"Wrote {len(frames_with_timestamps)} frames at {fps:.1f} FPS")
            return True

        finally:
            writer.release()

    def _cleanup_old_clips(self) -> None:
        """
        Delete video clips older than cleanup_age_hours.
        """
        try:
            cutoff_time = time.time() - (self.cleanup_age_hours * 3600)

            for clip_file in self.output_dir.glob("clip_*.mp4"):
                if clip_file.stat().st_mtime < cutoff_time:
                    clip_file.unlink()
                    logger.debug(f"Deleted old clip: {clip_file}")

        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

    def clear_buffer(self) -> None:
        """Clear all frames from buffer."""
        with self._lock:
            self._buffer.clear()
            logger.debug("Frame buffer cleared")

"""
High-speed video recording module for burst capture and slow-motion playback.

Captures frames at high frame rates and saves them for slow-motion playback.
Key difference from regular recorder: saves at fixed playback FPS (e.g., 30fps)
regardless of capture FPS, creating slow-motion effect.

Example:
    - Capture at 120 FPS for 2 seconds = 240 frames
    - Save at 30 FPS playback = 8 second slow-motion video (4x slower)
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


class HighSpeedRecorder:
    """
    High-speed frame capture with slow-motion video output.

    Features:
    - Configurable target capture FPS (30-200 fps)
    - Circular buffer maintaining last N seconds at capture rate
    - Slow-motion video output (playback at 30fps regardless of capture rate)
    - Real-time FPS measurement
    - Thread-safe operation

    Usage:
        recorder = HighSpeedRecorder(target_fps=120, buffer_duration_sec=3.0)

        # Add frames as fast as camera provides them
        recorder.add_frame(frame)

        # Get actual measured FPS
        actual_fps = recorder.get_actual_fps()

        # Save slow-motion clip (120fps captured, played at 30fps = 4x slow-mo)
        clip_path = recorder.save_slowmo_clip(duration_sec=2.0, playback_fps=30)
    """

    def __init__(
        self,
        target_fps: float = 60.0,
        buffer_duration_sec: float = 5.0,
        output_dir: str = "./clips",
        playback_fps: float = 30.0,
    ):
        """
        Initialize high-speed recorder.

        Args:
            target_fps: Target capture frame rate (used for buffer sizing)
            buffer_duration_sec: Maximum buffer duration in seconds
            output_dir: Directory for saving video clips
            playback_fps: Default playback frame rate for slow-motion output
        """
        self.target_fps = target_fps
        self.buffer_duration_sec = buffer_duration_sec
        self.output_dir = Path(output_dir)
        self.playback_fps = playback_fps

        # Calculate max buffer size based on target FPS and duration
        self._max_frames = int(target_fps * buffer_duration_sec * 1.2)  # 20% headroom

        # Frame buffer: [(timestamp, frame), ...]
        self._buffer: deque = deque(maxlen=self._max_frames)
        self._lock = threading.RLock()

        # FPS measurement
        self._fps_window: deque = deque(maxlen=60)  # Last 60 frame timestamps
        self._last_fps_calc = 0.0
        self._cached_fps = 0.0

        # Recording state
        self._is_recording = False
        self._recording_start_time = 0.0
        self._recording_frames: list = []

        # Latest frame for preview sampling
        self._latest_frame: Optional[np.ndarray] = None

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def set_target_fps(self, fps: float) -> None:
        """
        Update target FPS and resize buffer accordingly.

        Args:
            fps: New target frame rate
        """
        with self._lock:
            self.target_fps = fps
            new_max = int(fps * self.buffer_duration_sec * 1.2)
            # Recreate buffer with new max size
            old_frames = list(self._buffer)
            self._buffer = deque(old_frames, maxlen=new_max)
            logger.info(f"Target FPS updated to {fps}, buffer resized to {new_max} frames")

    def add_frame(self, frame: np.ndarray) -> None:
        """
        Add frame to buffer with timestamp.

        Args:
            frame: Frame data (H×W×C RGB or H×W mono)
        """
        current_time = time.time()
        frame_copy = frame.copy()

        with self._lock:
            # Update latest frame for preview
            self._latest_frame = frame_copy

            # Add to circular buffer
            self._buffer.append((current_time, frame_copy))

            # Update FPS measurement window
            self._fps_window.append(current_time)

            # If actively recording, also store in recording buffer
            if self._is_recording:
                self._recording_frames.append((current_time, frame_copy))

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent frame for UI display (thread-safe sampling).

        Returns:
            np.ndarray or None
        """
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def get_actual_fps(self) -> float:
        """
        Get measured frame rate from recent frames.

        Returns:
            Actual FPS calculated from frame timestamps
        """
        current_time = time.time()

        # Cache FPS calculation (update at most every 0.2 seconds)
        if current_time - self._last_fps_calc < 0.2:
            return self._cached_fps

        with self._lock:
            if len(self._fps_window) < 2:
                return 0.0

            # Calculate FPS from timestamp window
            oldest = self._fps_window[0]
            newest = self._fps_window[-1]
            time_span = newest - oldest

            if time_span > 0:
                self._cached_fps = (len(self._fps_window) - 1) / time_span
            else:
                self._cached_fps = 0.0

            self._last_fps_calc = current_time
            return self._cached_fps

    def get_buffer_stats(self) -> dict:
        """
        Get buffer statistics.

        Returns:
            Dict with frame_count, duration_sec, actual_fps, slowmo_factor
        """
        with self._lock:
            frame_count = len(self._buffer)
            actual_fps = self.get_actual_fps()

            if frame_count >= 2:
                oldest = self._buffer[0][0]
                newest = self._buffer[-1][0]
                duration = newest - oldest
            else:
                duration = 0.0

            # Calculate slow-motion factor (how much slower playback will be)
            slowmo_factor = actual_fps / self.playback_fps if self.playback_fps > 0 else 1.0

            return {
                "frame_count": frame_count,
                "duration_sec": duration,
                "actual_fps": actual_fps,
                "target_fps": self.target_fps,
                "slowmo_factor": slowmo_factor,
                "playback_fps": self.playback_fps,
            }

    def start_recording(self) -> None:
        """
        Start recording frames for a high-speed clip.
        Frames will be accumulated until stop_recording() is called.
        """
        with self._lock:
            self._is_recording = True
            self._recording_start_time = time.time()
            self._recording_frames = []
            logger.info("High-speed recording started")

    def stop_recording(self) -> int:
        """
        Stop recording and return frame count.

        Returns:
            Number of frames captured
        """
        with self._lock:
            self._is_recording = False
            frame_count = len(self._recording_frames)
            logger.info(f"High-speed recording stopped: {frame_count} frames")
            return frame_count

    def save_slowmo_clip(
        self,
        duration_sec: Optional[float] = None,
        playback_fps: Optional[float] = None,
        filename: Optional[str] = None,
        use_recording_buffer: bool = False,
    ) -> Optional[str]:
        """
        Save buffered frames as slow-motion video.

        The video is saved at playback_fps (default 30), so if captured at 120fps,
        the resulting video plays at 4x slow motion.

        Args:
            duration_sec: Duration of source footage to save (None = all)
            playback_fps: Output video frame rate (None = use default)
            filename: Output filename (None = auto-generate)
            use_recording_buffer: If True, use frames from start/stop_recording

        Returns:
            Path to saved video file, or None if failed
        """
        if playback_fps is None:
            playback_fps = self.playback_fps

        with self._lock:
            # Select frame source
            if use_recording_buffer and self._recording_frames:
                source_frames = self._recording_frames.copy()
            else:
                source_frames = list(self._buffer)

            if len(source_frames) < 2:
                logger.warning("Insufficient frames for slow-mo clip")
                return None

            # Filter by duration if specified
            if duration_sec is not None:
                cutoff_time = source_frames[-1][0] - duration_sec
                source_frames = [(ts, f) for ts, f in source_frames if ts >= cutoff_time]

            if len(source_frames) < 2:
                logger.warning("Insufficient frames after duration filter")
                return None

            # Calculate capture FPS and slow-mo factor
            time_span = source_frames[-1][0] - source_frames[0][0]
            capture_fps = (len(source_frames) - 1) / time_span if time_span > 0 else 30.0
            slowmo_factor = capture_fps / playback_fps

            # Generate filename
            if filename is None:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"slowmo_{int(capture_fps)}fps_{slowmo_factor:.1f}x_{timestamp_str}.mp4"

            output_path = self.output_dir / filename

        # Write video (outside lock)
        try:
            success = self._write_slowmo_video(source_frames, output_path, playback_fps)
            if success:
                logger.info(
                    f"Saved slow-mo clip: {output_path} "
                    f"({len(source_frames)} frames @ {capture_fps:.1f}fps capture, "
                    f"{playback_fps}fps playback = {slowmo_factor:.1f}x slow-mo)"
                )
                return str(output_path)
            return None

        except Exception as e:
            logger.error(f"Failed to save slow-mo clip: {e}")
            return None

    def _write_slowmo_video(
        self,
        frames_with_timestamps: list[tuple[float, np.ndarray]],
        output_path: Path,
        playback_fps: float,
    ) -> bool:
        """
        Write frames to slow-motion video file.

        Args:
            frames_with_timestamps: List of (timestamp, frame) tuples
            output_path: Output file path
            playback_fps: Playback frame rate (determines slow-mo factor)

        Returns:
            True if successful
        """
        if not frames_with_timestamps:
            return False

        # Get frame dimensions
        first_frame = frames_with_timestamps[0][1]
        height, width = first_frame.shape[:2]
        is_color = len(first_frame.shape) == 3 and first_frame.shape[2] == 3

        # Use H.264 codec for better compatibility
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
        writer = cv2.VideoWriter(
            str(output_path), fourcc, playback_fps, (width, height), isColor=is_color
        )

        if not writer.isOpened():
            logger.error(f"Failed to open video writer for {output_path}")
            return False

        try:
            for _, frame in frames_with_timestamps:
                if is_color:
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                writer.write(frame_bgr)

            return True

        finally:
            writer.release()

    def clear_buffer(self) -> None:
        """Clear frame buffer and recording buffer."""
        with self._lock:
            self._buffer.clear()
            self._recording_frames = []
            self._fps_window.clear()
            logger.debug("Buffers cleared")

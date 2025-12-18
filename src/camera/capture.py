"""
Frame capture service with error handling.

Implements performance optimization patterns from spec/llm.txt:
- Section 19.1: Reduce CPU load through zero-copy processing
- Section 19.2: Increase frame rate through optimized capture loop
- Section 23.4: Python continuous capture pattern

Maps to FR-006 (continuous updates), FR-009 (max FPS).

This module provides a high-level generator interface for continuous frame capture
with proper error handling and timeout management.
"""

import logging
import threading
import time
from typing import Iterator, Union, Optional

import numpy as np

from src.camera.device import CameraDevice, CameraException
from src.camera.webcam import WebcamDevice
from src.lib import mvsdk

logger = logging.getLogger(__name__)


class CaptureSession:
    """
    Manages a background thread for high-speed camera capture.
    Decouples hardware acquisition from UI display rate.
    """

    def __init__(self, camera: Union[CameraDevice, WebcamDevice], recorder):
        self.camera = camera
        self.recorder = recorder
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """Start background capture thread."""
        if self._running:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._capture_loop, name="CaptureThread", daemon=True
        )
        self._running = True
        self._thread.start()
        logger.info("Background capture session started")

    def stop(self):
        """Stop background capture thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._running = False
        logger.info("Background capture session stopped")

    def _capture_loop(self):
        """Infinite loop pulling frames from camera as fast as possible."""
        frame_count = 0
        last_log_time = time.time()

        logger.info("Capture loop started")

        while not self._stop_event.is_set():
            try:
                # Check if camera is still initialized and valid
                if not self.camera or not getattr(self.camera, "_initialized", False):
                    time.sleep(0.1)
                    continue

                # Use a smaller timeout in capture_frames if possible,
                # but currently it's hardcoded to 500ms in device.py.
                # We iterate over the generator.
                for frame in self.camera.capture_frames():
                    if self._stop_event.is_set():
                        break

                    # If camera became uninitialized during iteration
                    if not getattr(self.camera, "_initialized", False):
                        break

                    # Push to recorder buffer
                    self.recorder.add_frame(frame)
                    frame_count += 1

                    # Periodic logging of capture performance
                    curr_time = time.time()
                    if curr_time - last_log_time >= 5.0:
                        fps = frame_count / (curr_time - last_log_time)
                        logger.info(
                            f"Capture Thread: {fps:.1f} FPS sustained ({frame_count} frames)"
                        )
                        frame_count = 0
                        last_log_time = curr_time

            except Exception as e:
                if not self._stop_event.is_set():
                    # Avoid spamming errors if it's just a temporary initialization issue
                    if "not initialized" in str(e).lower():
                        time.sleep(0.5)
                    else:
                        logger.error(f"Error in capture loop: {e}")
                        time.sleep(1.0)  # Wait before retry

        self._running = False
        logger.info("Capture loop terminated")


def create_frame_generator(camera: Union[CameraDevice, WebcamDevice]) -> Iterator[np.ndarray]:
    """
    Generator that yields frames from camera with error handling.

    Implements zero-copy path per research.md section 4.
    Handles timeouts gracefully (skip frame, don't raise).

    Args:
        camera: Initialized CameraDevice (must be in __enter__ context)

    Yields:
        np.ndarray: Frame data (H×W×C for color, H×W for mono)

    Raises:
        RuntimeError: Camera not initialized
        CameraException: Fatal camera error (not timeout)

    Contract:
        - FR-006: Continuous frame updates
        - FR-009: Maximum FPS delivery
        - Timeouts are normal, continue streaming
        - Other errors propagate to caller
    """
    sequence = 0

    try:
        for frame in camera.capture_frames():
            sequence += 1
            logger.debug(f"Frame captured: sequence={sequence}, shape={frame.shape}")
            yield frame

    except StopIteration:
        logger.info("Frame generator stopped")

    except CameraException as e:
        # Timeouts are expected, skip frame
        if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
            logger.debug("Frame timeout, continuing...")
            return

        # Other errors are fatal
        logger.error(f"Camera error: {e}, code={e.error_code}")
        raise

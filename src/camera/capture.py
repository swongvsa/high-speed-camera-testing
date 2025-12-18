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
from typing import Iterator, Union

import numpy as np

from src.camera.device import CameraDevice, CameraException
from src.camera.webcam import WebcamDevice
from src.lib import mvsdk

logger = logging.getLogger(__name__)


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

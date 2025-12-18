"""
WebcamDevice: Hardware abstraction for standard webcams using OpenCV.
Implements the same interface as CameraDevice for MindVision cameras.
"""

import logging
import threading
import time
from typing import Iterator, Optional

import cv2
import numpy as np

from src.camera.device import CameraAccessDenied, CameraCapability, CameraException, CameraInfo

logger = logging.getLogger(__name__)


class WebcamDevice:
    """
    Hardware wrapper for webcams using OpenCV VideoCapture.
    """

    # Class-level lock for single-access enforcement
    _access_lock = threading.Lock()
    _active_devices = set()  # Track device indices currently in use

    def __init__(self, camera_info: CameraInfo) -> None:
        """
        Create webcam device instance.
        """
        self._camera_info = camera_info
        self._cap: Optional[cv2.VideoCapture] = None
        self._initialized = False
        self._frame_lock = threading.RLock()
        self._width = 0
        self._height = 0
        self._fps = 0.0

    @staticmethod
    def enumerate_cameras() -> list[CameraInfo]:
        """
        Enumerate available webcams by probing indices.
        """
        cameras = []
        # Probe first 5 indices
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # On some platforms, we can't get a friendly name easily from OpenCV
                # We'll just use "Webcam {i}"
                cameras.append(
                    CameraInfo(
                        device_index=i,
                        friendly_name=f"Webcam {i}",
                        port_type="USB/Webcam",
                        source_type="webcam",
                    )
                )
                cap.release()
        return cameras

    def get_capability(self) -> CameraCapability:
        """
        Get camera hardware capabilities.
        """
        if not self._initialized or self._cap is None:
            raise RuntimeError("Camera not initialized. Call __enter__() first.")

        return CameraCapability(
            is_mono=False,  # Most webcams are color
            max_width=self._width,
            max_height=self._height,
            max_fps=self._fps if self._fps > 0 else 30.0,
        )

    def info(self) -> str:
        """
        Get camera info string.
        """
        if not self._initialized:
            raise RuntimeError("Camera not initialized. Call __enter__() first.")

        return f"{self._camera_info.friendly_name} ({self._width}x{self._height})"

    def __enter__(self) -> "WebcamDevice":
        """
        Initialize webcam and start capture.
        """
        # Enforce single access per device
        with self._access_lock:
            # Use a unique key for webcam devices to avoid collision with MindVision
            device_key = f"webcam_{self._camera_info.device_index}"
            if device_key in self._active_devices:
                raise CameraAccessDenied(
                    "Webcam already in use. Only one viewer allowed.", error_code=-1
                )
            self._active_devices.add(device_key)

        try:
            self._cap = cv2.VideoCapture(self._camera_info.device_index)
            if not self._cap.isOpened():
                raise CameraException(
                    f"Failed to open webcam {self._camera_info.device_index}", error_code=-1
                )

            # Get actual resolution
            self._width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self._height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self._fps = self._cap.get(cv2.CAP_PROP_FPS)

            self._initialized = True
            return self
        except Exception as e:
            with self._access_lock:
                device_key = f"webcam_{self._camera_info.device_index}"
                self._active_devices.discard(device_key)
            if isinstance(e, CameraException):
                raise
            raise CameraException(f"Webcam initialization failed: {e}", error_code=-1)

    def capture_frames(self) -> Iterator[np.ndarray]:
        """
        Continuously yield frames from webcam.
        """
        if not self._initialized or self._cap is None:
            raise RuntimeError("Camera not initialized. Call __enter__() first.")

        while self._initialized:
            ret, frame = self._cap.read()
            if not ret:
                logger.warning("Failed to read frame from webcam")
                time.sleep(0.01)  # Small sleep to prevent tight loop on error
                continue

            # OpenCV returns BGR, we need RGB for Gradio
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            yield frame_rgb

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Release webcam resources.
        """
        self._initialized = False
        if self._cap:
            self._cap.release()
            self._cap = None

        with self._access_lock:
            device_key = f"webcam_{self._camera_info.device_index}"
            self._active_devices.discard(device_key)

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a single frame from the webcam (thread-safe).
        """
        with self._frame_lock:
            if not self._initialized or self._cap is None:
                return None

            ret, frame = self._cap.read()
            if not ret:
                return None

            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def set_exposure_time(self, exposure_us: float) -> None:
        """
        Set camera exposure time (best effort for webcams).
        """
        if not self._initialized or self._cap is None:
            raise RuntimeError("Camera not initialized. Call __enter__() first.")

        # OpenCV exposure is often in log scale or platform dependent
        # Many webcams don't support manual exposure through OpenCV
        # We'll just log it for now as this is dev mode
        logger.info(f"Setting webcam exposure to {exposure_us}us (best effort)")
        # Example of how it might be set, but often doesn't work:
        # self._cap.set(cv2.CAP_PROP_EXPOSURE, exposure_us / 1000.0)

"""
CameraDevice: Hardware abstraction for MindVision camera SDK.

Implements the CameraDevice contract from specs/001-using-gradio-as/contracts/camera_device.py
Maps to FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, FR-009, FR-010

Implementation follows patterns from spec/llm.txt:
- Section 2.1: Core camera operation sequence
- Section 5.1: Manual exposure control
- Section 16.1: Frame rate optimization
- Section 19: Performance optimization patterns
- Section 23.4: Python continuous capture pattern
- Section 23.9: Python best practices
- Section 23.14: Implementation checklist

Key features:
- Zero-copy frame capture using aligned memory buffers
- High-speed mode (CameraSetFrameSpeed = 2)
- Manual exposure for consistent capture
- Platform-specific handling (Windows flip)
- Comprehensive error reporting using CameraGetErrorString
"""

import logging
import platform
import threading
import time
from dataclasses import dataclass
from typing import Iterator, Optional

import numpy as np

from src.lib import mvsdk

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Data Classes (from contract)
# ------------------------------------------------------------------


@dataclass
class CameraInfo:
    """Camera enumeration information"""

    device_index: int
    friendly_name: str
    port_type: str


@dataclass
class CameraCapability:
    """Camera hardware capabilities"""

    is_mono: bool
    max_width: int
    max_height: int
    max_fps: float


# ------------------------------------------------------------------
# Exceptions (from contract)
# ------------------------------------------------------------------


class CameraException(Exception):
    """Camera operation failed"""

    def __init__(self, message: str, error_code: int):
        super().__init__(message)
        self.error_code = error_code


class CameraAccessDenied(CameraException):
    """Camera already in use (single viewer enforcement)"""

    pass


# ------------------------------------------------------------------
# CameraDevice Implementation
# ------------------------------------------------------------------


class CameraDevice:
    """
    Hardware wrapper for MindVision camera SDK.

    Lifecycle:
    1. enumerate_cameras() -> list of available cameras
    2. __init__(camera_info) -> create instance
    3. __enter__() -> initialize and start streaming
    4. capture_frames() -> yield frames continuously
    5. __exit__() -> cleanup resources
    """

    # Class-level lock for single-access enforcement (FR-006a)
    _access_lock = threading.Lock()
    _active_devices = set()  # Track device indices currently in use

    def __init__(self, camera_info: CameraInfo) -> None:
        """
        Create camera device instance (not initialized yet).

        Args:
            camera_info: Camera to connect to

        Contract:
            - Must accept CameraInfo from enumerate_cameras()
            - Does NOT initialize hardware (use __enter__)
        """
        self._camera_info = camera_info
        self._handle: Optional[int] = None
        self._capability: Optional[mvsdk.tSdkCameraCapbility] = None
        self._frame_buffer = None
        self._is_mono = False
        self._initialized = False
        # Thread safety
        self._frame_lock = threading.RLock()  # Protect frame operations
        self._reconnect_in_progress = False  # Prevent concurrent reconnects
        # Timeout / reconnect state
        self._timeout_count = 0
        self._last_timeout_log_ts = 0.0
        self._last_reconnect_attempt = 0.0  # Timestamp of last reconnect attempt
        # Tunable thresholds
        self._consecutive_timeout_limit = 10  # reconnect after this many consecutive timeouts
        self._reconnect_backoff_seconds = 2.0  # Sleep duration during reconnect
        self._min_reconnect_interval = 10.0  # Minimum seconds between reconnect attempts

    @staticmethod
    def enumerate_cameras() -> list[CameraInfo]:
        """
        Enumerate all connected cameras.

        Returns:
            List of CameraInfo objects (empty list if no cameras)

        Raises:
            CameraException: SDK initialization failed

        Contract:
            - FR-001: Must detect all available cameras
            - Returns empty list (not None) if no cameras
            - Device indices must be 0-based sequential
        """
        try:
            dev_list = mvsdk.CameraEnumerateDevice()

            cameras = []
            for i, dev_info in enumerate(dev_list):
                cameras.append(
                    CameraInfo(
                        device_index=i,
                        friendly_name=dev_info.GetFriendlyName(),
                        port_type=dev_info.GetPortType(),
                    )
                )

            return cameras

        except mvsdk.CameraException as e:
            error_str = mvsdk.CameraGetErrorString(e.error_code)
            raise CameraException(f"Camera enumeration failed: {error_str}", e.error_code)

    def get_capability(self) -> CameraCapability:
        """
        Get camera hardware capabilities.

        Returns:
            CameraCapability with resolution and format info

        Contract:
            - FR-007: Must indicate mono vs color
            - FR-010: Must provide native max resolution
            - FR-009: Must provide max FPS capability
            - Only callable after __enter__()

        Raises:
            RuntimeError: Camera not initialized
        """
        if not self._initialized or self._capability is None:
            raise RuntimeError("Camera not initialized. Call __enter__() first.")

        return CameraCapability(
            is_mono=self._is_mono,
            max_width=self._capability.sResolutionRange.iWidthMax,
            max_height=self._capability.sResolutionRange.iHeightMax,
            max_fps=200.0,
        )

    def info(self) -> str:
        """
        Get camera info string.

        Returns:
            Human-readable camera info

        Raises:
            RuntimeError: Camera not initialized
        """
        if not self._initialized or self._camera_info is None:
            raise RuntimeError("Camera not initialized. Call __enter__() first.")

        return f"{self._camera_info.friendly_name} ({self._capability.sResolutionRange.iWidthMax}x{self._capability.sResolutionRange.iHeightMax})"

    def set_exposure_time(self, exposure_us: float) -> None:
        """
        Set camera exposure time.

        Args:
            exposure_us: Exposure time in microseconds

        Raises:
            RuntimeError: Camera not initialized
            CameraException: SDK call failed

        Contract:
            - Spec section 5.1: Manual exposure control
            - Only callable after __enter__()
        """
        if not self._initialized or self._handle is None:
            raise RuntimeError("Camera not initialized. Call __enter__() first.")

        try:
            # Ensure manual exposure mode
            mvsdk.CameraSetAeState(self._handle, 0)
            # Set exposure time
            mvsdk.CameraSetExposureTime(self._handle, exposure_us)
        except mvsdk.CameraException as e:
            error_str = mvsdk.CameraGetErrorString(e.error_code)
            raise CameraException(f"Failed to set exposure time: {error_str}", e.error_code)

    def __enter__(self) -> "CameraDevice":
        """
        Initialize camera and start streaming.

        Returns:
            Self (for context manager)

        Contract:
            - FR-002: Must initialize camera for streaming
            - FR-003: Must start auto-capture mode
            - FR-009: Set to maximum FPS mode
            - FR-010: Use native resolution

        Raises:
            CameraException: Initialization or start failed
            CameraAccessDenied: Camera already in use
        """
        # Enforce single access per device (FR-006a)
        with self._access_lock:
            if self._camera_info.device_index in self._active_devices:
                raise CameraAccessDenied(
                    "Camera already in use. Only one viewer allowed.", error_code=-1
                )
            self._active_devices.add(self._camera_info.device_index)

        try:
            self._initialize()
            return self
        except Exception:
            # Cleanup on failure
            with self._access_lock:
                self._active_devices.discard(self._camera_info.device_index)
            raise

    def _initialize(self) -> None:
        """
        Internal initialization sequence.
        Based on research.md and cv_grab.py reference implementation.
        """
        try:
            # Re-enumerate to get fresh device info
            dev_list = mvsdk.CameraEnumerateDevice()
            if self._camera_info.device_index >= len(dev_list):
                raise CameraException(
                    f"Camera index {self._camera_info.device_index} not found", error_code=-1
                )

            dev_info = dev_list[self._camera_info.device_index]

            # 1. Initialize camera (FR-002)
            self._handle = mvsdk.CameraInit(dev_info, -1, -1)

            # 2. Get capability
            self._capability = mvsdk.CameraGetCapability(self._handle)

            # 3. Determine mono vs color (FR-007)
            self._is_mono = self._capability.sIspCapacity.bMonoSensor != 0

            # 4. Set output format based on camera type
            if self._is_mono:
                mvsdk.CameraSetIspOutFormat(self._handle, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
            else:
                mvsdk.CameraSetIspOutFormat(self._handle, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

            # 5. Set continuous capture mode (FR-003)
            mvsdk.CameraSetTriggerMode(self._handle, 0)

            # 5a. Optimize for max FPS (spec section 19.2)
            # Frame speed: 0=low, 1=normal, 2=high, 3=super
            mvsdk.CameraSetFrameSpeed(self._handle, 2)  # High speed mode

            # 5b. Set manual exposure for consistent frame capture (spec section 5.1)
            # Disable auto-exposure for high-speed capture
            mvsdk.CameraSetAeState(self._handle, 0)  # 0 = manual exposure
            mvsdk.CameraSetExposureTime(self._handle, 30 * 1000)  # 30ms default

            # 6. Allocate frame buffer (FR-010: native resolution)
            channels = 1 if self._is_mono else 3
            buffer_size = (
                self._capability.sResolutionRange.iWidthMax
                * self._capability.sResolutionRange.iHeightMax
                * channels
            )
            self._frame_buffer = mvsdk.CameraAlignMalloc(buffer_size, 16)

            # 7. Start streaming (FR-003, FR-009)
            mvsdk.CameraPlay(self._handle)

            self._initialized = True

        except mvsdk.CameraException as e:
            # Cleanup on initialization failure
            if self._handle is not None:
                try:
                    mvsdk.CameraUnInit(self._handle)
                except Exception:
                    pass
            if self._frame_buffer is not None:
                try:
                    mvsdk.CameraAlignFree(self._frame_buffer)
                except Exception:
                    pass

            error_str = mvsdk.CameraGetErrorString(e.error_code)
            raise CameraException(f"Camera initialization failed: {error_str}", e.error_code)

    def capture_frames(self) -> Iterator[np.ndarray]:
        """
        Continuously yield frames from camera.

        Yields:
            np.ndarray: Frame data (H×W×C for color, H×W for mono)

        Contract:
            - FR-006: Must continuously update without manual refresh
            - Timeout allowed (skip frame), don't raise exception
            - Yields until camera error or __exit__()

        Raises:
            RuntimeError: Camera not initialized
            CameraException: Fatal camera error (not timeout)
        """
        if not self._initialized:
            raise RuntimeError("Camera not initialized. Call __enter__() first.")

        while self._initialized:
            try:
                # Get raw frame from camera (500ms timeout)
                pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self._handle, 500)

                # Process raw data to RGB/MONO format
                mvsdk.CameraImageProcess(self._handle, pRawData, self._frame_buffer, FrameHead)

                # Release the raw buffer
                mvsdk.CameraReleaseImageBuffer(self._handle, pRawData)

                # Windows requires vertical flip (from research.md)
                if platform.system() == "Windows":
                    mvsdk.CameraFlipFrameBuffer(self._frame_buffer, FrameHead, 1)

                # Convert to NumPy array (zero-copy using ctypes)
                frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self._frame_buffer)
                frame = np.frombuffer(frame_data, dtype=np.uint8)

                # Reshape based on camera type (FR-007)
                if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8:
                    # Mono: (H, W)
                    frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth))
                else:
                    # Color: (H, W, 3) - convert BGR to RGB for Gradio
                    frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 3))
                    frame = frame[..., ::-1]  # BGR -> RGB

                yield frame

            except mvsdk.CameraException as e:
                # Timeout is expected and normal (FR-006 contract)
                if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
                    # Increment consecutive timeout counter
                    self._timeout_count += 1
                    now = time.time()
                    # Rate-limit debug logging to once every 5s to avoid spam
                    if now - self._last_timeout_log_ts > 5.0:
                        logger.debug("Frame timeout (streaming): waiting for next frame")
                        self._last_timeout_log_ts = now

                    # If we've seen many consecutive timeouts, try reconnect
                    if self._timeout_count >= self._consecutive_timeout_limit:
                        logger.warning(
                            "Consecutive frame timeouts (%d) reached, attempting reconnect",
                            self._timeout_count,
                        )
                        if self._attempt_reconnect():
                            # Reset counter on successful reconnect
                            self._timeout_count = 0
                            logger.info("Reconnect successful, resuming frame capture")
                            continue
                        else:
                            # Reconnect failed - reset counter and continue trying
                            # This prevents infinite reconnect attempts on each frame
                            self._timeout_count = 0
                            logger.warning("Reconnect failed, will retry after next timeout sequence")
                            continue

                    # Normal timeout: continue capturing
                    continue

                # Other errors are fatal
                error_str = mvsdk.CameraGetErrorString(e.error_code)
                raise CameraException(f"Frame capture failed: {error_str}", e.error_code)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Release camera resources.

        Contract:
            - FR-005: Must release camera (available for other apps)
            - Must free allocated frame buffers
            - Must call SDK cleanup functions
            - Must not raise exceptions (log errors only)
        """
        self._initialized = False

        # Release frame buffer
        if self._frame_buffer is not None:
            try:
                mvsdk.CameraAlignFree(self._frame_buffer)
            except Exception as e:
                # Log but don't raise (contract requirement)
                print(f"Warning: Failed to free frame buffer: {e}")
            finally:
                self._frame_buffer = None

        # Uninitialize camera
        if self._handle is not None:
            try:
                mvsdk.CameraUnInit(self._handle)
            except Exception as e:
                # Log but don't raise (contract requirement)
                print(f"Warning: Failed to uninitialize camera: {e}")
            finally:
                self._handle = None

        # Release access lock (FR-005: make available for other apps)
        with self._access_lock:
            self._active_devices.discard(self._camera_info.device_index)

        # Don't suppress exceptions (return None)
        return None

    def _attempt_reconnect(self) -> bool:
        """
        Attempt to reconnect to the camera after consecutive timeouts.

        Returns:
            bool: True if reconnect successful, False otherwise
        """
        logger.info("Attempting camera reconnect after consecutive timeouts")

        # Record attempt timestamp (in case called from other places)
        self._last_reconnect_attempt = time.time()

        # Clean up existing connection
        if self._frame_buffer is not None:
            try:
                mvsdk.CameraAlignFree(self._frame_buffer)
            except Exception as e:
                logger.warning(f"Error freeing buffer during reconnect: {e}")
            finally:
                self._frame_buffer = None

        if self._handle is not None:
            try:
                mvsdk.CameraUnInit(self._handle)
            except Exception as e:
                logger.warning(f"Error uninitializing camera during reconnect: {e}")
            finally:
                self._handle = None

        # Mark as not initialized after cleanup
        self._initialized = False

        # Wait before reconnecting (backoff)
        time.sleep(self._reconnect_backoff_seconds)

        # Re-initialize the camera
        try:
            self._initialize()
            logger.info("Camera reconnection successful")
            return True
        except CameraException as e:
            logger.error(f"Camera reconnection failed: {e}")
            # Keep initialized=False and return failure
            # Caller will handle this by returning None
            return False

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a single frame from the camera (thread-safe).

        Returns:
            np.ndarray: Frame data (H×W×C for color, H×W for mono)
            None: If camera not initialized or timeout

        Raises:
            CameraException: Frame capture failed (non-timeout error)
        """
        with self._frame_lock:
            return self._get_frame_locked()

    def _get_frame_locked(self) -> Optional[np.ndarray]:
        """
        Internal frame capture (called under lock).

        Returns:
            np.ndarray: Frame data or None on timeout
        """
        if not self._initialized:
            # Camera not initialized - check if reconnect needed
            # Prevent multiple simultaneous reconnects
            if self._reconnect_in_progress:
                return None

            now = time.time()
            time_since_last_attempt = now - self._last_reconnect_attempt

            if time_since_last_attempt >= self._min_reconnect_interval:
                self._reconnect_in_progress = True
                try:
                    logger.warning(
                        "Camera not initialized, attempting reconnect (%.1fs since last attempt)",
                        time_since_last_attempt
                    )

                    if self._attempt_reconnect():
                        self._timeout_count = 0
                        logger.info("Reconnect successful, camera reinitialized")
                    else:
                        logger.warning(
                            "Reconnect failed, will retry in %.0fs",
                            self._min_reconnect_interval
                        )
                finally:
                    self._reconnect_in_progress = False

            # Return None (don't recurse - let next call succeed if reconnect worked)
            return None

        try:
            # Get raw frame from camera (500ms timeout)
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self._handle, 500)

            # Process raw data to RGB/MONO format
            mvsdk.CameraImageProcess(self._handle, pRawData, self._frame_buffer, FrameHead)

            # Release the raw buffer
            mvsdk.CameraReleaseImageBuffer(self._handle, pRawData)

            # Windows requires vertical flip
            if platform.system() == "Windows":
                mvsdk.CameraFlipFrameBuffer(self._frame_buffer, FrameHead, 1)

            # Convert to NumPy array
            frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self._frame_buffer)
            frame = np.frombuffer(frame_data, dtype=np.uint8)

            # Reshape based on camera type
            if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8:
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth))
            else:
                # Color: convert BGR to RGB
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 3))
                frame = frame[..., ::-1]  # BGR -> RGB

            return frame

        except mvsdk.CameraException as e:
            # Treat timeout as non-fatal for single-frame capture: return None
            if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
                # Rate-limit timeout logging to avoid spam
                now = time.time()
                if now - self._last_timeout_log_ts > 5.0:
                    logger.debug("Frame timeout (single): no frame received")
                    self._last_timeout_log_ts = now

                # Increment counter and attempt reconnect on repeated timeouts
                self._timeout_count += 1
                if self._timeout_count >= self._consecutive_timeout_limit:
                    logger.warning(
                        "Consecutive timeouts (%d) reached in get_frame(); attempting reconnect",
                        self._timeout_count,
                    )
                    if self._attempt_reconnect():
                        # Reset counter on successful reconnect
                        self._timeout_count = 0
                        logger.info("Reconnect successful in get_frame()")
                    else:
                        # Reconnect failed - reset counter to allow retry later
                        self._timeout_count = 0
                        logger.warning("Reconnect failed in get_frame(), will retry later")

                return None
            error_str = mvsdk.CameraGetErrorString(e.error_code)
            raise CameraException(f"Frame capture failed: {error_str}", e.error_code)


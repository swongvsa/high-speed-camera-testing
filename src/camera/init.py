"""
Camera initialization helpers.
Provides `initialize_camera()` which supports selecting a camera by IP address
(or by environment variable `CAMERA_IP`) to accommodate dynamic link-local IPs.

This module wraps `CameraDevice` and `WebcamDevice` enumeration and initialization.
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Tuple, Union

from src.camera.device import CameraDevice, CameraError, CameraInfo
from src.camera.webcam import WebcamDevice

logger = logging.getLogger(__name__)


def enumerate_all_cameras() -> list[CameraInfo]:
    """
    Enumerate both MindVision cameras and standard webcams.

    Returns:
        Combined list of CameraInfo objects.
    """
    all_cameras = []

    # 1. Try MindVision cameras
    try:
        mv_cameras = CameraDevice.enumerate_cameras()
        all_cameras.extend(mv_cameras)
    except Exception as e:
        logger.warning(f"MindVision camera enumeration failed: {e}")

    # 2. Try Webcams
    try:
        webcams = WebcamDevice.enumerate_cameras()
        all_cameras.extend(webcams)
    except Exception as e:
        logger.warning(f"Webcam enumeration failed: {e}")

    return all_cameras


def initialize_camera(
    preferred_ip: Optional[str] = None,
    selected_info: Optional[CameraInfo] = None,
) -> Tuple[Optional[Union[CameraDevice, WebcamDevice]], Optional[str]]:
    """
    Initialize a camera based on preferred IP or specific CameraInfo.

    Args:
        preferred_ip: Optional IP address to prefer for MindVision cameras.
        selected_info: Explicitly selected CameraInfo from UI.

    Returns:
        (Device, None) on success, or (None, error_message) on failure.
    """
    if selected_info:
        selected = selected_info
    else:
        # Fallback to auto-detection logic
        all_cameras = enumerate_all_cameras()
        if not all_cameras:
            return None, "No camera detected. Please connect a camera and restart."

        # Allow env var to override preferred IP
        env_ip = os.environ.get("CAMERA_IP")
        if preferred_ip is None and env_ip:
            preferred_ip = env_ip

        selected = None
        if preferred_ip:
            # Try best-effort match for MindVision cameras
            for c in all_cameras:
                if c.source_type == "mindvision":
                    if preferred_ip in (c.friendly_name or "") or preferred_ip in (
                        c.port_type or ""
                    ):
                        selected = c
                        break

            if selected is None:
                logger.warning(
                    "Preferred camera IP %s not found. Falling back to first device.",
                    preferred_ip,
                )
                selected = all_cameras[0]
        else:
            selected = all_cameras[0]

    # Create appropriate device instance
    if selected.source_type == "webcam":
        camera = WebcamDevice(selected)
    else:
        camera = CameraDevice(selected)

    try:
        camera.__enter__()
        cap = camera.get_capability()
        logger.info(
            "Initialized camera: %s (%dx%d)", selected.friendly_name, cap.max_width, cap.max_height
        )
        return camera, None
    except CameraError as e:
        msg = f"Camera init failed: {e}"
        logger.error(msg)
        return None, msg
    except Exception as e:
        msg = f"Unexpected error initializing camera: {e}"
        logger.exception(msg)
        return None, msg

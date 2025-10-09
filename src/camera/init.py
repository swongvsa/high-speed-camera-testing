"""
Camera initialization helpers.
Provides `initialize_camera()` which supports selecting a camera by IP address
(or by environment variable `CAMERA_IP`) to accommodate dynamic link-local IPs.

This module wraps `CameraDevice` enumeration and initialization and returns a
(CameraDevice, None) tuple on success or (None, error_message) on failure.
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Tuple

from src.camera.device import CameraDevice, CameraException

logger = logging.getLogger(__name__)


def initialize_camera(
    preferred_ip: Optional[str] = None,
) -> Tuple[Optional[CameraDevice], Optional[str]]:
    """
    Enumerate and initialize a camera, optionally preferring one that matches
    `preferred_ip` or the `CAMERA_IP` environment variable.

    Args:
        preferred_ip: Optional IP address to prefer (e.g. "169.254.22.149").

    Returns:
        (CameraDevice, None) on success, or (None, error_message) on failure.

    Notes:
    - If the native MVSDK is not present this will typically fail to initialize
      a real camera; tests may mock `src.lib.mvsdk` and `CameraDevice`.
    - Matching by IP is best-effort: we look for the preferred_ip in the
      `friendly_name` or `port_type` fields returned by `CameraDevice.enumerate_cameras()`.
    """
    # Allow env var to override
    env_ip = os.environ.get("CAMERA_IP")
    if preferred_ip is None and env_ip:
        preferred_ip = env_ip

    try:
        cameras = CameraDevice.enumerate_cameras()
    except CameraException as e:
        msg = f"Camera enumeration failed: {e}"
        logger.error(msg)
        return None, msg

    if not cameras:
        return None, "No camera detected. Please connect a camera and restart."

    selected = None
    if preferred_ip:
        # Try best-effort match: check friendly_name and port_type strings for the IP
        for c in cameras:
            try:
                if preferred_ip in (c.friendly_name or "") or preferred_ip in (c.port_type or ""):
                    selected = c
                    break
            except Exception:
                # Defensive: skip if fields not present
                continue

        if selected is None:
            # No exact match; warn and fall back to first camera
            logger.warning(
                "Preferred camera IP %s not found among enumerated devices. Falling back to first device.",
                preferred_ip,
            )
            selected = cameras[0]
    else:
        selected = cameras[0]

    camera = CameraDevice(selected)
    try:
        camera.__enter__()
        cap = camera.get_capability()
        logger.info(
            "Initialized camera: %s (%dx%d)", selected.friendly_name, cap.max_width, cap.max_height
        )
        return camera, None
    except CameraException as e:
        msg = f"Camera init failed: {e}"
        logger.error(msg)
        return None, msg
    except Exception as e:
        msg = f"Unexpected error initializing camera: {e}"
        logger.exception(msg)
        return None, msg

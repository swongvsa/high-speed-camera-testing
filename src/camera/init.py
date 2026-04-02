"""
Camera initialization helpers.
Provides `initialize_camera()` which supports selecting a camera by IP address
(or by environment variable `CAMERA_IP`) to accommodate dynamic link-local IPs.

This module wraps `CameraDevice` and `WebcamDevice` enumeration and initialization.
"""

from __future__ import annotations

import ipaddress
import logging
import os
from typing import Optional, Tuple, Union

from src.camera.device import CameraDevice, CameraError, CameraInfo
from src.camera.webcam import WebcamDevice
from src.lib import mvsdk

logger = logging.getLogger(__name__)


def _are_on_same_subnet(ip1: str, ip2: str, mask: str) -> bool:
    """Check whether two IPs are on the same subnet given a netmask."""
    try:
        net1 = ipaddress.ip_address(ip1)
        net2 = ipaddress.ip_address(ip2)
        mask_int = int(ipaddress.ip_address(mask))
        return (int(net1) & mask_int) == (int(net2) & mask_int)
    except ValueError:
        return False


def _pick_compatible_ip(adapter_ip: str, adapter_mask: str) -> str:
    """Pick a link-local IP on the same subnet as the adapter, avoiding collisions."""
    try:
        adapter = ipaddress.ip_address(adapter_ip)
        mask_int = int(ipaddress.ip_address(adapter_mask))
        # Use the adapter's network with a .200 host offset
        network_part = int(adapter) & mask_int
        host_part = 200
        candidate = ipaddress.ip_address(network_part | host_part)
        if candidate == adapter:
            candidate = ipaddress.ip_address(network_part | 201)
        return str(candidate)
    except ValueError:
        return "169.254.170.200"


def auto_fix_gige_ip() -> Optional[str]:
    """Auto-detect and fix GigE camera IP subnet mismatches.

    Enumerates raw SDK devices, checks if camera and adapter are on the same
    subnet, and reassigns the camera IP if not.

    Returns:
        A status message describing what happened, or None if no GigE cameras
        were found or no fix was needed.
    """
    try:
        dev_list = mvsdk.CameraEnumerateDevice()
    except Exception as e:
        logger.debug("GigE IP auto-fix skipped (enumeration failed): %s", e)
        return None

    if not dev_list:
        return None

    for dev_info in dev_list:
        name = dev_info.GetFriendlyName()
        try:
            cam_ip, cam_mask, _cam_gw, eth_ip, eth_mask, _eth_gw = mvsdk.CameraGigeGetIp(dev_info)
        except Exception:
            # Not a GigE camera or SDK doesn't support IP queries for this device
            continue

        if not cam_ip or not eth_ip:
            continue

        # Use the adapter's mask as the authoritative subnet mask
        effective_mask = eth_mask or cam_mask or "255.255.0.0"

        if _are_on_same_subnet(cam_ip, eth_ip, effective_mask):
            logger.debug("Camera '%s' IP %s is on same subnet as adapter %s — no fix needed.", name, cam_ip, eth_ip)
            continue

        # Subnet mismatch — fix it
        new_ip = _pick_compatible_ip(eth_ip, effective_mask)
        logger.warning(
            "Camera '%s' IP %s is NOT on the same subnet as adapter %s. "
            "Reassigning camera to %s.",
            name, cam_ip, eth_ip, new_ip,
        )

        try:
            result = mvsdk.CameraGigeSetIp(dev_info, new_ip, effective_mask, "0.0.0.0", True)
            if result == 0:
                msg = f"Camera '{name}' IP corrected: {cam_ip} → {new_ip}"
                logger.info(msg)
                return msg
            else:
                logger.error("CameraGigeSetIp failed for '%s' with code %d", name, result)
        except Exception as e:
            logger.error("Failed to set camera IP for '%s': %s", name, e)

    return None


def enumerate_all_cameras() -> list[CameraInfo]:
    """
    Enumerate both MindVision cameras and standard webcams.

    Automatically fixes GigE camera IP subnet mismatches before enumeration.

    Returns:
        Combined list of CameraInfo objects.
    """
    # 0. Auto-fix GigE IP mismatches before enumeration
    fix_msg = auto_fix_gige_ip()
    if fix_msg:
        logger.info("GigE IP auto-fix: %s", fix_msg)

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

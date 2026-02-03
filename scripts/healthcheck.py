#!/usr/bin/env python3
"""
Health check script for camera connectivity validation.
Runs before app startup to warn about network issues.

Usage:
    python scripts/healthcheck.py

Exit codes:
    0 - All checks passed
    1 - Critical error (e.g., CAMERA_IP not set)
    2 - Warning (camera unreachable but not blocking)
"""

import os
import socket
import subprocess
import sys
from typing import Optional


def check_environment() -> tuple[bool, Optional[str], Optional[str]]:
    """Check if required environment variables are set.

    Returns:
        Tuple of (success, camera_ip, profile)
    """
    camera_ip = os.environ.get("CAMERA_IP")
    profile = os.environ.get("COMPOSE_PROFILES", "development")

    # Webcam mode doesn't need camera IP
    if profile == "webcam":
        print("✓ Webcam mode - skipping camera checks")
        return True, None, profile

    if not camera_ip:
        print("✗ ERROR: CAMERA_IP not set in environment")
        print("")
        print("Please set CAMERA_IP in your .env file:")
        print("  CAMERA_IP=169.254.22.149  # Replace with your camera's IP")
        return False, None, profile

    return True, camera_ip, profile


def validate_ip_address(ip: str) -> bool:
    """Validate that the IP address format is correct."""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def check_camera_reachable(ip: str) -> bool:
    """Check if camera is reachable via ping."""
    try:
        # Use ping with timeout (2 seconds)
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", ip],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # Ping not available or timeout
        return False


def main() -> int:
    """Run health checks and return exit code."""
    print("=" * 50)
    print("Camera App Health Check")
    print("=" * 50)
    print("")

    # Check environment
    success, camera_ip, profile = check_environment()
    if not success:
        return 1

    # Skip camera checks in webcam mode
    if profile == "webcam":
        print("")
        print("✓ All checks passed - ready to start in webcam mode")
        return 0

    # Validate IP format
    print(f"Checking camera IP: {camera_ip}")
    if not validate_ip_address(camera_ip):
        print(f"✗ ERROR: Invalid IP address format: {camera_ip}")
        print("")
        print("Expected format: XXX.XXX.XXX.XXX")
        print("Examples: 192.168.1.100, 169.254.22.149")
        return 1

    print("✓ IP address format is valid")

    # Check camera reachability
    print(f"Checking network connectivity to {camera_ip}...")
    if check_camera_reachable(camera_ip):
        print(f"✓ Camera is reachable at {camera_ip}")
        print("")
        print("✓ All checks passed - ready to start")
        return 0
    else:
        print(f"⚠ WARNING: Cannot reach camera at {camera_ip}")
        print("")
        print("Possible issues:")
        print("  1. Camera is not powered on")
        print("  2. Camera is not connected to network")
        print("  3. Wrong IP address in .env file")
        print("  4. Firewall is blocking ICMP ping")
        print("")
        print("The app will attempt to connect anyway.")
        print("If camera is offline, it may fall back to webcam mode.")
        print("")
        print("✓ Continuing with warnings")
        return 0  # Don't block startup, just warn


if __name__ == "__main__":
    sys.exit(main())

"""
Entry point for the high-speed camera testing app.

Usage:
  python main.py                                    # Start HTTP service on default port 7860
  python main.py --port 8080                        # Start on custom port
  python main.py --camera-ip 169.254.22.149         # Prefer specific camera IP
  python main.py --camera-ip 169.254.22.149 --check # Test camera connectivity only
"""

from __future__ import annotations

import argparse
import logging
import os
from typing import Optional

from src.camera.init import initialize_camera

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)


def main() -> None:
    """Main entry point for the camera application."""
    parser = argparse.ArgumentParser(description="Camera Feed Display Application")
    parser.add_argument("--port", type=int, default=7860, help="Server port (default: 7860)")
    parser.add_argument(
        "--camera-ip",
        type=str,
        default=None,
        help="Preferred camera IP address (e.g. 169.254.22.149)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Test camera connectivity without starting UI",
    )
    args = parser.parse_args()

    if args.camera_ip:
        os.environ["CAMERA_IP"] = args.camera_ip
        logger.info("Set CAMERA_IP=%s (from CLI)", args.camera_ip)
    elif os.environ.get("CAMERA_IP"):
        logger.info("Using CAMERA_IP=%s (from environment)", os.environ.get("CAMERA_IP"))

    if args.check:
        preferred: Optional[str] = args.camera_ip or os.environ.get("CAMERA_IP")
        camera, error = initialize_camera(preferred)
        if camera:
            logger.info("Camera initialized successfully: %s", camera)
            camera.__exit__(None, None, None)
            logger.info("Camera cleaned up after check")
        else:
            logger.error("Camera check failed: %s", error)
            logger.info(
                "Ensure the native MVSDK is installed and the camera is reachable "
                "on the same link-local network."
            )
    else:
        from src.ui.server import run_server

        logger.info("Starting camera HTTP service on port %s...", args.port)
        run_server(port=args.port)


if __name__ == "__main__":
    main()

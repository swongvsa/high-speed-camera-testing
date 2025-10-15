"""
Entry point for the high-speed camera testing app.

Usage:
  python main.py                                    # Start Gradio UI on default port 7860
  python main.py --port 8080                        # Start on custom port
  python main.py --camera-ip 169.254.22.149         # Prefer specific camera IP
  python main.py --camera-ip 169.254.22.149 --check # Test camera connectivity only

Maps to FR-001 through FR-012 functional requirements.
"""

from __future__ import annotations

import argparse
import logging
import os
from typing import Optional

from src.camera.init import initialize_camera
from src.ui.app import create_camera_app, launch_app

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress verbose third-party logs
logging.getLogger("httpx").setLevel(logging.WARNING)


def main() -> None:
    """Main entry point for the camera application.

    Parses command-line arguments and either checks camera connectivity
    or launches the Gradio UI.
    """
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

    # Set camera IP preference if provided
    if args.camera_ip:
        os.environ["CAMERA_IP"] = args.camera_ip
        logger.info("Set CAMERA_IP=%s", args.camera_ip)

    if args.check:
        # Check mode: Test camera connectivity only
        preferred: Optional[str] = args.camera_ip or os.environ.get("CAMERA_IP")
        camera, error = initialize_camera(preferred)
        if camera:
            logger.info("Camera initialized successfully: %s", camera)
            # Immediately clean up (we only checked connectivity)
            camera.__exit__(None, None, None)
            logger.info("Camera cleaned up after check")
        else:
            logger.error("Camera check failed: %s", error)
            logger.info(
                "Ensure the native MVSDK is installed and the camera is reachable "
                "on the same link-local network."
            )
    else:
        # Launch Gradio UI (FR-001 to FR-012)
        logger.info("Creating Gradio camera application...")
        app = create_camera_app()

        logger.info("Launching server on http://127.0.0.1:%s", args.port)
        launch_app(app, server_port=args.port)


if __name__ == "__main__":
    main()

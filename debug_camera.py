#!/usr/bin/env python3
"""
Camera enumeration diagnostics.
Tests MVSDK camera detection with detailed error reporting.
"""

import logging
import sys

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_mvsdk_import():
    """Test if MVSDK module can be imported."""
    try:
        from src.lib import mvsdk

        logger.info("✅ MVSDK module imported successfully")
        logger.info(f"   MVSDK location: {mvsdk.__file__}")
        return mvsdk
    except ImportError as e:
        logger.error(f"❌ Failed to import MVSDK: {e}")
        logger.error("   Ensure spec/python_demo/mvsdk.py is accessible")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error importing MVSDK: {e}")
        return None


def test_camera_enumeration(mvsdk):
    """Test camera enumeration."""
    try:
        logger.info("🔍 Calling mvsdk.CameraEnumerateDevice()...")
        dev_list = mvsdk.CameraEnumerateDevice()

        logger.info(f"📊 Found {len(dev_list)} camera(s)")

        for i, dev_info in enumerate(dev_list):
            logger.info(f"\n--- Camera {i} ---")
            try:
                logger.info(f"  Friendly Name: {dev_info.GetFriendlyName()}")
                logger.info(f"  Port Type: {dev_info.GetPortType()}")
            except Exception as e:
                logger.error(f"  Error getting camera info: {e}")

        return dev_list

    except Exception as e:
        logger.error(f"❌ Camera enumeration failed: {e}")
        if hasattr(mvsdk, "CameraGetErrorString"):
            try:
                error_code = getattr(e, "error_code", None)
                if error_code is not None:
                    error_str = mvsdk.CameraGetErrorString(error_code)
                    logger.error(f"   Error code {error_code}: {error_str}")
            except Exception:
                pass
        return []


def test_camera_init():
    """Test full camera initialization."""
    try:
        import os

        from src.camera.init import initialize_camera

        # Use environment variable if set
        camera_ip = os.environ.get("CAMERA_IP", "169.254.170.200")
        logger.info(f"🎬 Testing camera initialization with IP: {camera_ip}")

        camera, error = initialize_camera(camera_ip)

        if error:
            logger.error(f"❌ Camera initialization failed: {error}")
            return False

        if camera:
            logger.info("✅ Camera initialized successfully!")
            try:
                cap = camera.get_capability()
                logger.info(f"   Resolution: {cap.max_width}x{cap.max_height}")
                logger.info(f"   Camera info: {camera.info()}")
            except Exception as e:
                logger.error(f"   Error getting camera capabilities: {e}")

            # Cleanup
            camera.__exit__(None, None, None)
            logger.info("   Camera cleaned up")
            return True

        return False

    except Exception as e:
        logger.error(f"❌ Unexpected error during camera init test: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all diagnostics."""
    logger.info("=" * 60)
    logger.info("Camera Enumeration Diagnostics")
    logger.info("=" * 60)

    # Step 1: Import MVSDK
    logger.info("\n[1/3] Testing MVSDK import...")
    mvsdk = test_mvsdk_import()
    if not mvsdk:
        logger.error("\n❌ MVSDK import failed. Cannot proceed with diagnostics.")
        logger.error("   Check that spec/python_demo/mvsdk.py exists and is properly configured.")
        sys.exit(1)

    # Step 2: Enumerate cameras
    logger.info("\n[2/3] Testing camera enumeration...")
    devices = test_camera_enumeration(mvsdk)

    if not devices:
        logger.warning("\n⚠️  No cameras detected during enumeration!")
        logger.warning("   Possible causes:")
        logger.warning("   1. Camera is not connected or powered")
        logger.warning("   2. Camera IP is not on the same link-local network")
        logger.warning("   3. MVSDK library is not properly installed")
        logger.warning("   4. Camera is in use by another application")
        logger.warning("   5. Firewall/network configuration blocking camera")

    # Step 3: Test full initialization
    logger.info("\n[3/3] Testing full camera initialization...")
    success = test_camera_init()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Diagnostic Summary")
    logger.info("=" * 60)
    logger.info(f"MVSDK Import:        {'✅ PASS' if mvsdk else '❌ FAIL'}")
    logger.info(f"Camera Enumeration:  {'✅ PASS' if devices else '⚠️  No cameras'}")
    logger.info(f"Camera Initialization: {'✅ PASS' if success else '❌ FAIL'}")
    logger.info("=" * 60)

    if not success:
        logger.error("\n❌ Camera initialization failed!")
        logger.error("   This is why Gradio shows 'Session blocked' - no camera available.")
        sys.exit(1)
    else:
        logger.info("\n✅ All diagnostics passed! Camera should work in Gradio.")
        sys.exit(0)


if __name__ == "__main__":
    main()

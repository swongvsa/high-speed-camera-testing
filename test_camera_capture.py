#!/usr/bin/env python3
"""
Simple test script to capture frames from camera and diagnose timeout issues.
"""

import logging
import time
from src.camera.init import initialize_camera

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_camera_capture():
    """Test camera frame capture with detailed logging."""
    logger.info("Testing camera frame capture...")
    
    # Initialize camera
    camera, error = initialize_camera()
    if error:
        logger.error(f"Camera initialization failed: {error}")
        return
    
    logger.info(f"Camera initialized: {camera.info()}")
    
    try:
        # Test single frame capture
        logger.info("Testing single frame capture...")
        start_time = time.time()
        
        try:
            frame = camera.get_frame()
            capture_time = time.time() - start_time
            logger.info(f"Single frame captured successfully in {capture_time:.3f}s, shape: {frame.shape}")
        except Exception as e:
            logger.error(f"Single frame capture failed: {e}")
            return
        
        # Test continuous capture for a few frames
        logger.info("Testing continuous capture (5 frames)...")
        frame_count = 0
        timeout_count = 0
        
        for frame in camera.capture_frames():
            frame_count += 1
            logger.info(f"Frame {frame_count} captured, shape: {frame.shape}")
            
            if frame_count >= 5:
                break
                
        logger.info(f"Captured {frame_count} frames successfully")
        
    except Exception as e:
        logger.error(f"Camera test failed: {e}")
    finally:
        # Cleanup
        logger.info("Cleaning up camera...")
        camera.__exit__(None, None, None)
        logger.info("Camera test completed")

if __name__ == "__main__":
    test_camera_capture()
#!/usr/bin/env python3
"""
Test segmentation functionality without camera.

This script tests the segmentation pipeline with a sample image.
"""

import numpy as np
from PIL import Image

from src.segmentation import COCO_CLASSES, SegmentationConfig, SegmentationProcessor


def create_test_image():
    """Create a colorful test image."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)

    # Add some colorful shapes
    img[100:200, 100:300] = [255, 0, 0]  # Red rectangle
    img[250:400, 400:550] = [0, 255, 0]  # Green rectangle
    img[50:150, 450:600] = [0, 0, 255]   # Blue rectangle

    return img


def main():
    print("🧪 Testing Segmentation Pipeline")
    print("=" * 50)

    # Create processor
    print("\n1. Creating segmentation processor...")
    config = SegmentationConfig(
        model_size="n",
        confidence_threshold=0.3,
        enable_tracking=False,
    )
    processor = SegmentationProcessor(config)
    print(f"   ✅ Processor created (model: {config.model_path})")

    # Create test image
    print("\n2. Creating test image...")
    test_frame = create_test_image()
    print(f"   ✅ Test image created: {test_frame.shape}")

    # Process frame
    print("\n3. Processing frame...")
    result = processor.process_frame(test_frame)
    print(f"   ✅ Processed: {result.shape}")

    # Save result
    print("\n4. Saving result...")
    output_path = "test_segmentation_output.png"
    Image.fromarray(result).save(output_path)
    print(f"   ✅ Saved to: {output_path}")

    print("\n✨ Segmentation test complete!")
    print(f"   - Model ready: {processor.is_ready}")
    print(f"   - COCO classes: {len(COCO_CLASSES)}")
    print(f"\n💡 If you see masks/labels on the output image, segmentation is working!")


if __name__ == "__main__":
    main()

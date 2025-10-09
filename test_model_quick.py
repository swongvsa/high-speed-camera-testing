#!/usr/bin/env python3
"""
Quick test: Does YOLO model detect anything?

Downloads a test image and runs detection.
"""

import numpy as np
from ultralytics import YOLO
import supervision as sv

# Create a simple test image with some basic shapes
print("Creating test image...")
img = np.zeros((640, 640, 3), dtype=np.uint8)
img[100:300, 100:300] = [255, 255, 255]  # White square
img[400:500, 400:500] = [200, 200, 200]  # Gray square

print("Loading YOLOv8 nano segmentation model...")
model = YOLO("yolov8n-seg.pt")

print("\nTesting with different confidence thresholds...")
for conf in [0.5, 0.3, 0.25, 0.1]:
    results = model(img, conf=conf, verbose=False)[0]
    detections = sv.Detections.from_ultralytics(results)
    print(f"  conf={conf}: {len(detections)} detections")
    if len(detections) > 0:
        print(f"    Classes: {detections.class_id}")
        print(f"    Confidences: {detections.confidence}")

print("\n" + "="*50)
print("If you see 0 detections for all thresholds:")
print("  - This is normal for a blank test image")
print("  - The model works, but needs real objects to detect")
print("  - Point your camera at: person, chair, laptop, phone, bottle, etc.")
print("="*50)

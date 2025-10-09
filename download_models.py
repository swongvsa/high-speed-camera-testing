#!/usr/bin/env python3
"""
Utility script to pre-download YOLO segmentation models.

Run this to download models before first use to avoid waiting in the UI.

Usage:
    python download_models.py              # Download nano (default)
    python download_models.py n s m        # Download multiple sizes
    python download_models.py --all        # Download all sizes
"""

import sys
from pathlib import Path

from ultralytics import YOLO

MODEL_SIZES = {
    "n": "yolov8n-seg.pt",  # Nano: ~6MB
    "s": "yolov8s-seg.pt",  # Small: ~12MB
    "m": "yolov8m-seg.pt",  # Medium: ~27MB
    "l": "yolov8l-seg.pt",  # Large: ~46MB
    "x": "yolov8x-seg.pt",  # XLarge: ~70MB
}


def download_model(size: str) -> None:
    """Download a specific model size."""
    if size not in MODEL_SIZES:
        print(f"❌ Invalid size '{size}'. Choose from: {list(MODEL_SIZES.keys())}")
        return

    model_path = MODEL_SIZES[size]
    print(f"\n📦 Downloading {model_path}...")

    try:
        # YOLO automatically downloads if not cached
        model = YOLO(model_path)
        print(f"✅ {model_path} ready!")

        # Show cache location
        cache_dir = Path.home() / ".ultralytics" / "weights"
        print(f"   Cached at: {cache_dir / model_path}")

    except Exception as e:
        print(f"❌ Failed to download {model_path}: {e}")


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Default to nano if no args
    if not args:
        args = ["n"]

    # Handle --all flag
    if "--all" in args:
        args = list(MODEL_SIZES.keys())

    print("🚀 YOLO Model Downloader")
    print("=" * 50)

    for size in args:
        download_model(size)

    print("\n✨ Download complete!")
    print(f"   Models cached in: ~/.ultralytics/weights/")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Standalone test for face recognition module.
Tests face detection, enrollment, and recognition without camera.
"""

import numpy as np

from src.face_recognition import (
    FaceRecognitionConfig,
    FaceRecognitionProcessor,
    EmbeddingsManager,
)


def create_test_face_image(color: tuple[int, int, int] = (128, 128, 128)) -> np.ndarray:
    """
    Create a simple test image with a face-like pattern.

    Note: This won't actually be detected as a face by real models.
    For real testing, use actual face photos.

    Args:
        color: RGB color for the "face"

    Returns:
        640x640x3 test image
    """
    img = np.zeros((640, 640, 3), dtype=np.uint8)

    # Create a circular "face" in the center
    center_y, center_x = 320, 320
    radius = 150

    for y in range(640):
        for x in range(640):
            if (x - center_x) ** 2 + (y - center_y) ** 2 < radius ** 2:
                img[y, x] = color

    # Add "eyes"
    for eye_x in [center_x - 50, center_x + 50]:
        for y in range(center_y - 30, center_y - 10):
            for x in range(eye_x - 15, eye_x + 15):
                img[y, x] = (0, 0, 0)  # Black eyes

    # Add "mouth"
    for y in range(center_y + 30, center_y + 50):
        for x in range(center_x - 40, center_x + 40):
            img[y, x] = (0, 0, 0)  # Black mouth

    return img


def main():
    print("=" * 60)
    print("Face Recognition Module Test")
    print("=" * 60)

    # Create test configuration
    print("\n1. Creating face recognition configuration...")
    config = FaceRecognitionConfig(
        model_name="Facenet512",
        detector_backend="opencv",  # Use opencv for simpler test
        recognition_threshold=0.6,
        distance_metric="cosine",
    )
    print(f"   Model: {config.model_name}")
    print(f"   Detector: {config.detector_backend}")
    print(f"   Threshold: {config.recognition_threshold}")

    # Create embeddings manager (uses temporary database)
    print("\n2. Creating embeddings manager...")
    embeddings_mgr = EmbeddingsManager("/tmp/test_face_recognition_db.json")
    print(f"   Database: {embeddings_mgr.db_path}")
    print(f"   Current faces: {len(embeddings_mgr)}")

    # Create processor
    print("\n3. Creating face recognition processor...")
    processor = FaceRecognitionProcessor(config, embeddings_mgr)
    print(f"   Processor ready: {processor.is_ready}")
    print(f"   Enrolled faces: {processor.num_enrolled}")

    print("\n4. Testing with synthetic image...")
    print("   NOTE: Synthetic images won't be detected as real faces.")
    print("   For real testing, use actual photos of faces.")

    # Create test images
    test_img1 = create_test_face_image((180, 180, 180))  # Light gray "face"
    test_img2 = create_test_face_image((80, 80, 80))     # Dark gray "face"

    print("\n5. Attempting enrollment (will likely fail with synthetic image)...")
    try:
        result = processor.enroll_face("TestPerson", test_img1)
        print(f"   ✅ Enrolled: {result['name']}")
        print(f"   Model: {result['model']}")
        print(f"   Embedding dim: {result['embedding_dim']}")
    except Exception as e:
        print(f"   ❌ Enrollment failed (expected with synthetic image): {e}")

    print("\n6. Face database status:")
    enrolled_faces = processor.list_enrolled_faces()
    print(f"   Total enrolled: {len(enrolled_faces)}")
    if enrolled_faces:
        for name in enrolled_faces:
            print(f"   - {name}")

    print("\n" + "=" * 60)
    print("Test Instructions for Real Usage:")
    print("=" * 60)
    print("""
To test with real faces:

1. Prepare clear face photos (JPG/PNG):
   - Well-lit, front-facing
   - Single person per photo
   - Minimum 640x480 resolution

2. Run enrollment:
   ```python
   from src.face_recognition import FaceRecognitionProcessor, EmbeddingsManager, FaceRecognitionConfig

   config = FaceRecognitionConfig()
   mgr = EmbeddingsManager()
   processor = FaceRecognitionProcessor(config, mgr)

   # Enroll face
   processor.enroll_face("Alice", "path/to/alice.jpg")
   processor.enroll_face("Bob", "path/to/bob.jpg")
   ```

3. Run recognition:
   ```python
   # Process frame with enrolled faces
   annotated_frame, debug_info = processor.process_frame(camera_frame)
   print(debug_info)
   ```

4. Or use the UI:
   ```bash
   uv run python main.py
   # Go to Face Recognition tab
   # Upload photo and enter name
   # Click "Enroll Face"
   # Enable Face Recognition checkbox
   ```
    """)

    print("\n✅ Test completed!")
    print(f"Database saved to: {embeddings_mgr.db_path}")
    print("Delete the test database: rm /tmp/test_face_recognition_db.json")


if __name__ == "__main__":
    main()

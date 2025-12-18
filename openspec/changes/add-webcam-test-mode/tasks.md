## 1. Specs
- [x] 1.1 Add `camera-sources` delta spec (webcam + selection)
- [x] 1.2 Add `ui-camera-selector` delta spec (dropdown behavior)

## 2. Implementation
- [x] 2.1 Add OpenCV-backed webcam camera implementation (VideoCapture)
- [x] 2.2 Add unified camera source model (id/label/type)
- [x] 2.3 Update camera init to enumerate/select sources
- [x] 2.4 Add Gradio dropdown to choose active camera source
- [x] 2.5 Ensure recorder works for webcam frames (RGB/GRAY)
- [x] 2.6 Preserve single-viewer enforcement and cleanup guarantees

## 3. Tests & Validation
- [x] 3.1 Add unit tests for source enumeration/selection (mock MVSDK + mock cv2.VideoCapture)
- [x] 3.2 Add contract/integration test for switching sources (no hardware required)
- [x] 3.3 Run `ruff check src tests`
- [x] 3.4 Run `pytest tests/ -v` (or targeted tests while iterating)

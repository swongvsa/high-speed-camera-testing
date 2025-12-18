# Change: Add webcam test mode (OpenCV) with UI selection

## Why
Developers currently need a MindVision camera to exercise the live preview + recording workflow. This change adds a dev-focused “camera test mode” so contributors can use built-in webcams (e.g., MacBook camera) to validate the UI and clip saving without special hardware.

## What Changes
- Add a webcam-backed camera source implemented via OpenCV `cv2.VideoCapture`.
- Add a UI dropdown to choose the active camera source (MindVision device vs webcam index).
- Preserve existing behavior as the default path (MindVision-first).
- Reuse existing recording/clip saving flow so webcam mode supports viewing and saving.

## Impact
- Affected code (expected): `src/camera/`, `src/ui/`, and related tests under `tests/`.
- Affected specs (this proposal):
  - `camera-sources` (new): enumerate/select camera backends including webcams
  - `ui-camera-selector` (new): allow selecting camera source in Gradio UI

## Compatibility
- Non-breaking: default behavior remains unchanged when using MindVision cameras.
- Dev-focused: webcam support is intended for development/testing and may have different performance/controls than MindVision.

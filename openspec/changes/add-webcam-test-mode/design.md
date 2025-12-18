## Context
The application currently assumes a MindVision camera connected via the MVSDK bindings (`src/lib/mvsdk.py`) and uses a single `CameraDevice` implementation to enumerate and stream frames.

Developers without MindVision hardware cannot validate the end-to-end UI flow (streaming + clip saving) locally.

## Goals / Non-Goals
- Goals:
  - Provide a dev-friendly camera backend using OpenCV (`cv2.VideoCapture`) for built-in webcams.
  - Allow selecting camera source from the UI via a dropdown.
  - Keep frame output format consistent with existing expectations (numpy array, RGB for color).
  - Ensure clip saving works for webcam frames with the existing recorder.
- Non-Goals:
  - Full parity with MindVision controls (frame speed, manual exposure, native resolution enforcement).
  - High-FPS guarantees on webcams.
  - Multi-viewer support (single viewer enforcement remains).

## Decisions
- Decision: Introduce a camera “source” abstraction that can represent either:
  - MindVision camera device (existing MVSDK-backed implementation)
  - Webcam device index (OpenCV-backed implementation)

  The abstraction must provide:
  - Enumeration for UI display (id + friendly label)
  - Context-managed lifecycle (`__enter__`/`__exit__`) and a frame generator API compatible with existing streaming
  - `info()` and capability-like metadata where feasible

- Decision: UI dropdown drives (re)initialization.
  - When the selected source changes, the current camera instance is shut down (safe cleanup), and the new one is initialized.
  - Errors are surfaced to the user using existing Gradio error patterns.

- Decision: Keep the existing “MindVision-first” behavior.
  - If a MindVision camera is selected (or default selection resolves to MindVision), existing behavior stays unchanged.
  - Webcam mode is additive and used primarily for development.

## Alternatives considered
- Replacing the existing `CameraDevice` directly with an OpenCV-backed implementation.
  - Rejected: would blur hardware-specific assumptions and risk regressions.
- Adding a separate dev-only entrypoint.
  - Rejected: duplicates UI logic; the dropdown approach offers a single, testable path.

## Risks / Trade-offs
- Webcam enumeration is platform-dependent.
  - Mitigation: represent webcams as indices (0..N) with best-effort probing and labels like "Webcam 0".
- Webcam frame format differences (BGR vs RGB, varying sizes).
  - Mitigation: standardize to RGB numpy arrays and document that webcam resolution may vary.
- Switching sources mid-session may cause transient UI errors.
  - Mitigation: serialize source switching and reuse the existing single-session lock.

## Migration Plan
- No user migration required.
- Default behavior remains MindVision-first; webcam support is additive.

## Open Questions
- None (scope confirmed: dev mode, viewing + saving, UI dropdown, OpenCV backend).

## Why

The current UI exposes camera-physics controls (capture FPS, playback FPS, shutter speed, ROI presets) that require domain expertise to operate correctly. High school students using this tool for physics project work need to capture slow-motion footage and document their methods — they think in terms of "I want 8× slower" not "I need 240 FPS capture at 1/500s shutter." The current two-slider approach for deriving slow-motion factor also makes the save flow confusing, and the post-save experience provides no immediate documentation aid.

## What Changes

- **Replace dual FPS sliders** with a slowdown preset selector (2×, 4×, 8×, 16×, 32×) as the primary speed control
- **Auto-calculate camera settings** from the selected slowdown factor and current ROI max FPS
- **Add transparent settings disclosure** — show the resulting FPS, shutter speed, resolution and playback FPS below the selected preset
- **Add "Copy for Methods Section" button** that generates a ready-to-paste citation sentence for lab reports
- **Redesign save panel** to show output duration ("YOUR CLIP WILL BE 40 seconds") before saving
- **Add post-save state** — panel transitions to show "Saved!" with checkmark, preview tap target, Download MP4, and "↩ Save Another Clip"
- **Add Advanced Settings accordion** (collapsed by default) exposing manual Auto Exposure toggle, Shutter Speed override, and Analog Gain
- **Simplify camera source** from a dropdown to a connection status chip in the header bar

## Capabilities

### New Capabilities

- `slowdown-preset-control`: Slowdown multiplier selector that auto-derives capture FPS, shutter speed, and playback FPS; exposes settings transparently for documentation
- `methods-copy`: One-tap generation and clipboard copy of a formatted methods-section citation string
- `save-clip-flow`: Redesigned save panel with output-duration preview, post-save transition state, and clip download

### Modified Capabilities

<!-- No existing specs — this is the first formal spec pass for this UI -->

## Impact

- `src/ui/app.py` — primary change surface; UI layout, event wiring, and settings state
- `src/camera/highspeed_recorder.py` — no API changes; slowdown logic reads `target_fps` and `playback_fps` which remain
- Gradio CSS and theme — updated chip styles and new accordion/panel styles
- `interface.pen` — reference design already created

# TODOS

## Desktop Distribution

- **End-to-end test on clean ARM64 Mac** — verify `.app` launches without Python/bun/uv installed
  **Priority:** P1

- **DMG creation** — add `hdiutil create` step to `desktop/scripts/build.sh` so distributing to operators is drag-and-drop
  **Priority:** P2

- **Code signing / notarization** — unsigned app requires Security & Privacy approval on first launch; notarization removes this friction for non-developer Macs
  **Priority:** P2

## Camera Reliability

- **Camera disconnect recovery** — if GigE drops mid-session, camera auto-reconnects without operator restart
  **Priority:** P2

- **MJPEG stream reconnect** — frontend auto-retries stream URL if the `<img>` src goes blank (currently no retry logic)
  **Priority:** P3

## Completed

- Electrobun desktop wrapper replacing old Electron setup (v0.2.0)
- FastAPI server replacing Gradio (v0.2.0)
- Custom web UI with ROI presets, slowdown controls, clip save (v0.2.0)
- Persistent clip storage in `~/Movies/High Speed Camera/` (v0.2.0)
- Localhost-only binding, CORS restricted to views:// (v0.2.0)
- Atomic clip write (.tmp → rename) preventing corrupt files on SIGTERM (v0.2.0)
- Ring buffer FPS resize keeps newest frames (v0.2.0)
- Record poll 20 s timeout with idle reset (v0.2.0)

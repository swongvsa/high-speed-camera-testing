# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-04-02

### Added
- Electrobun desktop wrapper: the app ships as a native macOS `.app` bundle. Double-click to open — no Python, pip, or terminal required for non-technical operators.
- FastAPI HTTP service replaces Gradio. Serves camera API, MJPEG live preview stream, and clip file download on `127.0.0.1` only.
- Custom web UI (`src/ui/web/`) — pure HTML/JS/CSS, served via Electrobun's `views://` scheme with no browser URL bar.
- `/api/config` endpoint: single source of truth for ROI options and slowdown presets. Frontend loads hardware capabilities from the server on startup instead of duplicating constants.
- Persistent clip storage in `~/Movies/High Speed Camera/` so recordings survive app updates.
- Hermetic CPython 3.13 ARM64 runtime bundled via `python-build-standalone` — no system Python dependency.
- 19 integration tests for the FastAPI server contract (`tests/integration/test_server_api.py`).

### Changed
- Clips directory is now `~/Movies/High Speed Camera/` (previously `./clips` relative to the bundle, which was wiped on app updates).
- Server binds to `127.0.0.1` only — was previously `0.0.0.0`, which exposed the camera API to the local network.
- OpenCV dependency changed to `opencv-python-headless` (no Qt GUI libraries needed for a headless server).
- CORS policy restricts allowed origins to `views://` scheme and localhost — was previously a wildcard.

### Fixed
- Slow-motion clip is now written to a `.tmp` file and renamed atomically on success, preventing corrupt files if the process is killed mid-save.
- Recording thread is now non-daemon: the SIGTERM handler waits up to 10 s for the H.264 encoder to flush before exiting.
- MJPEG stream generator now exits cleanly on client disconnect (`GeneratorExit`), preventing leaked generator threads accumulating after reconnects.
- Record poll UI now times out after 20 s and resets to idle if Python crashes mid-save, so the operator can try again without restarting the app.
- Ring buffer correctly keeps the most recent frames when target FPS is reduced (was keeping oldest frames, causing silent data loss before an operator-triggered save).
- Settings response from `POST /api/settings` now correctly parsed from `data.settings.*` (was reading from `data.*` which is always undefined).
- Buffer bar denominator now updates dynamically from `clip_duration_sec` (was hardcoded to 10 s).
- `libmvsdk.dylib` quarantine attribute removed during build so the SDK loads on freshly-downloaded app copies without Gatekeeper blocking it.
- Port retry: added 50 ms delay after killing a failed Python process before trying the next port, preventing race where the OS hasn't released the socket yet.

### Removed
- Gradio UI (`src/ui/app.py`, `src/ui/session.py`, `src/ui/errors.py`, `src/ui/lifecycle.py`) — fully replaced by FastAPI + custom web UI.
- Old Electron wrapper (`desktop/main.js`, `desktop/electron-builder.yml`) — replaced by Electrobun.
- Stale tests importing deleted Gradio modules (`test_scenario_02_single_viewer.py`, `test_scenario_05_localhost.py`, `test_viewer_session_contract.py`, `test_gradio_ui_contract.py`).

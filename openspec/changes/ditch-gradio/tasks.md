## 1. Python HTTP Service (Phase 1)

- [x] 1.1 Create `src/ui/server.py` with FastAPI app, CORS middleware, and uvicorn launch
- [x] 1.2 Implement `GET /stream` MJPEG endpoint — generator yielding JPEG frames from capture thread with `multipart/x-mixed-replace` content type
- [x] 1.3 Implement `GET /api/cameras` endpoint — calls `enumerate_all_cameras()` and returns JSON array
- [x] 1.4 Implement `GET /api/status` endpoint — returns camera connection state, current settings, FPS metrics, buffer state as JSON
- [x] 1.5 Implement `POST /api/settings` endpoint — accepts JSON body, applies settings under RLock, returns effective settings
- [x] 1.6 Implement `POST /api/record` and `GET /api/record/status` endpoints — trigger clip save from ring buffer, poll for completion
- [x] 1.7 Implement `GET /api/record/download` endpoint — serve saved MP4 as file download
- [x] 1.8 Add SIGTERM handler for graceful camera release and server shutdown
- [x] 1.9 Simplify session model — remove multi-session tracking (`SessionLifecycle`, `ViewerSession` simplification) to single-session

## 2. Static HTML UI (Phase 2)

- [x] 2.1 Create `src/ui/web/index.html` — page structure with viewfinder, controls panel, settings panel
- [x] 2.2 Create `src/ui/web/styles.css` — port DARK_CSS (165 lines) as standalone stylesheet, strip Gradio-specific selectors
- [x] 2.3 Create `src/ui/web/app.js` — main UI logic: status polling, fetch-based settings updates, MJPEG img binding
- [x] 2.4 Implement camera source dropdown — populated from `GET /api/cameras`, selection triggers `POST /api/settings`
- [x] 2.5 Implement ROI preset dropdown — options match current presets, selection triggers `POST /api/settings`
- [x] 2.6 Implement slowdown preset buttons (2x–32x) — active state highlighting, updates local state + settings card
- [x] 2.7 Implement exposure/gain controls — auto-exposure checkbox, exposure slider, gain slider, all calling `POST /api/settings`
- [x] 2.8 Implement performance metrics display — target/capture/preview FPS updated from `GET /api/status` polling
- [x] 2.9 Implement buffer bar — progress bar + text from status polling, visual state change when full
- [x] 2.10 Implement record button + save flow — triggers `POST /api/record`, polls status, shows video preview + download link on completion
- [x] 2.11 Implement settings disclosure card — derived values (capture rate, actual slowdown, output duration) updated on state change
- [x] 2.12 Implement duration preset buttons (2s–10s) — active state highlighting, updates clip duration state
- [x] 2.13 Port methods citation card with clipboard copy button

## 3. Electrobun Integration

- [x] 3.1 Update `desktop/src/bun/index.ts` — load `views://main/index.html` instead of `http://localhost:PORT`, inject port into webview
- [x] 3.2 Update `electrobun.config.ts` — add `build.copy` entry for `src/ui/web/` → `views/main/`
- [x] 3.3 Update startup sequence — spawn Python, poll `GET /api/status` for readiness, UI shows connecting state until ready
- [x] 3.4 Remove `GRADIO_SERVER_PORT` env var, keep `--port` CLI arg for the HTTP service

## 4. Entry Point & Dependencies

- [x] 4.1 Update `main.py` — import and launch FastAPI server instead of Gradio app
- [x] 4.2 Update `pyproject.toml` — replace `gradio` with `fastapi` + `uvicorn[standard]`
- [x] 4.3 Update `desktop/scripts/build.sh` — change `uv pip install` to drop gradio, add fastapi+uvicorn, copy `src/ui/web/` into build
- [x] 4.4 Remove or replace `src/ui/errors.py` — replace `gr.Error`/`gr.Warning` with HTTP error responses in server.py

## 5. Cleanup & Verification

- [x] 5.1 Delete old `src/ui/app.py` (Gradio app factory)
- [x] 5.2 Remove or rewrite `tests/contract/test_gradio_ui_contract.py`
- [x] 5.3 Verify `src/camera/` modules are unchanged — init.py, capture.py, highspeed_recorder.py have no Gradio imports
- [ ] 5.4 Build desktop app and verify bundle size reduction (~200MB expected)
- [ ] 5.5 End-to-end test: app launches, viewfinder streams, settings apply, clip saves and downloads

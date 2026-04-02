## Context

The app runs inside Electrobun (Bun + native macOS webview). Today, the Python process boots a full Gradio server on localhost, Electrobun polls until it responds, then points the webview at `http://localhost:PORT`. The UI is built with 14+ `gr.HTML` blocks, 165 lines of CSS overrides, and a hidden-textbox bridge hack — it's already vanilla HTML/CSS/JS wearing a Gradio costume. The camera logic (`src/camera/`, `CameraDevice`, `highspeed_recorder`, `CaptureSession`) is cleanly separated and doesn't depend on Gradio.

## Goals / Non-Goals

**Goals:**
- Replace Gradio with a headless Python HTTP service exposing camera functionality via REST + MJPEG
- Serve the UI as static HTML/CSS/JS via Electrobun's `views://` scheme
- Preserve all existing camera functionality (streaming, settings, recording, clip export)
- Reduce bundle size by ~200MB
- Eliminate Gradio version churn as a maintenance burden

**Non-Goals:**
- Phase 3 Electrobun IPC (Bun↔Python direct communication) — HTTP is sufficient for now
- Redesigning the UI layout or visual design — port the existing look 1:1
- Changing camera logic (`src/camera/`) — only the interface layer changes
- Supporting browser-based access (this is now a desktop-only app)

## Decisions

### 1. FastAPI + uvicorn for the Python HTTP service

**Choice**: FastAPI with uvicorn
**Over**: Flask, raw http.server, aiohttp

**Rationale**: FastAPI is already a transitive dep of Gradio (it's in site-packages today). It's lightweight (~1.6MB vs Gradio's 154MB), has native async support for streaming responses, and its `StreamingResponse` is ideal for MJPEG. uvicorn is already present too. The dependency footprint *shrinks* by switching — we keep what Gradio was using internally and drop everything on top.

### 2. MJPEG streaming for the viewfinder

**Choice**: MJPEG over HTTP (`GET /stream`)
**Over**: WebSocket with base64 frames, Server-Sent Events

**Rationale**: MJPEG is the simplest possible streaming approach — it's just an `<img>` tag pointed at an endpoint. No JavaScript needed for frame rendering. The browser handles buffering, display, and lifecycle natively. Gradio was using WebSocket + base64 JSON internally, which is more complex and higher overhead. MJPEG is standard for camera applications and works in the webview without any client-side code.

**Format**: `multipart/x-mixed-replace; boundary=frame` with JPEG-encoded frames. The capture thread already produces numpy arrays; `cv2.imencode('.jpg', frame)` is one call.

### 3. Static HTML served via `views://` scheme

**Choice**: Electrobun's built-in `views://` scheme
**Over**: Python serving static files, Bun serving static files

**Rationale**: Electrobun already has a `views://` protocol for serving bundled HTML. The splash screen uses it today. No HTTP server needed for the UI — the webview loads `views://main/index.html` directly. This means the UI loads instantly (no waiting for a server to boot) and the Python process only needs to handle API/stream requests.

### 4. REST endpoints for settings and recording

**Choice**: Simple REST API (`POST /api/settings`, `POST /api/record`, `GET /api/status`)
**Over**: WebSocket bidirectional, Electrobun IPC

**Rationale**: The UI sends infrequent, discrete commands (change ROI, adjust exposure, start recording). REST is the simplest model for request-response interactions. The existing `current_settings` dict + `RLock` pattern maps directly to a settings endpoint. No framework-specific event system needed.

### 5. Session management via startup/shutdown lifecycle

**Choice**: Single-session model (one webview = one session)
**Over**: Multi-session with session hashes

**Rationale**: Gradio needed `gr.Request.session_hash` because it's a web server that could serve multiple browser tabs. As a desktop app, there's exactly one user and one webview. The session lifecycle simplifies to: Python starts → camera initializes → stream begins → app closes → cleanup. The `SessionLifecycle` and `ViewerSession` classes can be simplified to a single-session model.

### 6. Port communication between Bun and Python

**Choice**: Keep the current port-based approach (pass port via CLI arg + env var)
**Over**: Unix socket, stdio IPC

**Rationale**: The Electrobun host already spawns Python with `--port`. The webview's HTML will use `fetch('http://localhost:PORT/api/...')` and `<img src="http://localhost:PORT/stream">`. The port is injected into the HTML at load time via Electrobun's Bun process (or a simple template variable). This is the smallest delta from the current architecture.

## Risks / Trade-offs

**[MJPEG bandwidth]** → MJPEG sends full JPEG frames continuously, no delta compression. At 120fps full-res this could be heavy. **Mitigation**: The preview stream is already decimated to ~30fps for display; only the capture buffer runs at full speed. MJPEG quality parameter controls bandwidth.

**[CORS in views:// scheme]** → The webview loads from `views://` but makes `fetch()` calls to `http://localhost:PORT`. This is a cross-origin request. **Mitigation**: FastAPI CORS middleware with `allow_origins=["*"]` — acceptable since this is localhost-only in a desktop app.

**[No hot-reload during development]** → Gradio had built-in hot-reload. **Mitigation**: During dev, open `index.html` directly in a browser pointed at the Python service. Standard browser dev tools work. Optionally add `--reload` to uvicorn for Python changes.

**[Camera enumeration at startup]** → Currently `enumerate_all_cameras()` is called lazily when the dropdown loads. With the new model, it should be called on the `/api/cameras` endpoint. **Mitigation**: Same lazy initialization, just triggered by an API call instead of a Gradio event.

**[Cleanup on window close]** → Gradio's `.unload()` hook handled session cleanup. **Mitigation**: Electrobun's `mainWin.on("close")` already sends SIGTERM to the Python process. Add a `signal.signal(SIGTERM, cleanup)` handler in Python to release the camera gracefully.

## Open Questions

- **JPEG quality for MJPEG**: What quality level balances bandwidth and visual fidelity for the preview stream? (Likely 70-85, tunable via settings endpoint)
- **Port injection into HTML**: Should the port be injected via a Bun-side template replacement in the HTML file, or should the HTML discover it via a known convention (e.g., always try 7860)?

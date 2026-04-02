## Why

The app is a desktop application (Electrobun) serving a single native webview, yet it bundles a full web framework (Gradio, 154MB + ~50MB of transitive deps) to serve that one window. The UI is already mostly vanilla HTML/CSS/JS — 14+ `gr.HTML` blocks, 165 lines of CSS overrides, and a hidden-textbox bridge hack to escape Gradio's event model. Every Gradio version bump (5→6→7) breaks these workarounds. Removing Gradio cuts ~200MB from the bundle, eliminates framework version churn, speeds up startup, and aligns the architecture with what it actually is: a native app, not a web app.

## What Changes

- **BREAKING**: Remove Gradio entirely. `src/ui/app.py` is replaced by a headless HTTP service and static HTML/CSS/JS files.
- Python backend becomes a headless camera service exposing HTTP endpoints (MJPEG stream, settings API, recording API). Camera logic (`src/camera/init.py`, `CameraDevice`, `mvsdk.py`) is unchanged.
- UI becomes static HTML/CSS/JS served via Electrobun's `views://` scheme. No HTTP server needed for the UI — only for the camera data API.
- Electrobun host (`desktop/src/bun/index.ts`) updated to load `views://` instead of polling a Gradio server URL.
- Build script (`desktop/scripts/build.sh`) drops `gradio` and its dependency tree from `uv pip install`.
- The hidden-textbox bridge pattern, `gr.State`, `gr.update()`, and all Gradio-specific workarounds are eliminated.

## Capabilities

### New Capabilities
- `camera-http-service`: Headless Python HTTP server (FastAPI or similar) exposing MJPEG frame streaming, camera settings control, and clip recording via REST endpoints.
- `static-html-ui`: Vanilla HTML/CSS/JS frontend served by Electrobun's `views://` scheme. Replaces all Gradio components with standard DOM elements and `fetch()` calls.
- `electrobun-views-integration`: Update Electrobun host to serve UI via `views://` scheme and connect to the Python HTTP service for camera data.

### Modified Capabilities
<!-- No existing specs are changing at the requirement level — this is a complete UI/server replacement. -->

## Impact

- **`src/ui/app.py`**: Rewritten entirely — Gradio app factory replaced by FastAPI/HTTP service
- **`src/ui/errors.py`**: `gr.Error`/`gr.Warning`/`gr.Info` replaced with HTTP error responses
- **`desktop/src/bun/index.ts`**: Webview loads `views://` instead of `http://localhost:PORT`; startup polling changes
- **`desktop/electrobun.config.ts`**: `build.copy` updated to include static HTML files
- **`desktop/scripts/build.sh`**: `uv pip install` drops `gradio`, adds `fastapi`+`uvicorn` (much smaller)
- **`pyproject.toml`**: Dependencies updated
- **`main.py`**: Launch logic simplified (no Gradio server)
- **`tests/contract/test_gradio_ui_contract.py`**: Removed or rewritten
- **Bundle size**: ~200MB reduction in site-packages

## ADDED Requirements

### Requirement: UI served via views:// scheme
The Electrobun host SHALL load the main UI from `views://main/index.html` instead of `http://localhost:PORT`. The HTML, CSS, and JS files SHALL be bundled into the app via `electrobun.config.ts` build.copy configuration.

#### Scenario: App startup
- **WHEN** the Electrobun app launches
- **THEN** the main window loads `views://main/index.html` immediately (no HTTP polling required for the UI)

#### Scenario: Build includes UI files
- **WHEN** `electrobun build` runs
- **THEN** the `src/ui/web/` directory is copied into the app bundle at the `views/main/` path

### Requirement: Python service startup
The Electrobun host SHALL spawn the Python process and wait for the HTTP service to be ready before the UI attempts to connect. The port SHALL be communicated to the UI.

#### Scenario: Port injection
- **WHEN** the Python service starts on a port
- **THEN** the Electrobun host communicates the active port to the webview (via URL parameter, postMessage, or known convention)

#### Scenario: Service health check
- **WHEN** the Python service is spawning
- **THEN** the Electrobun host polls `GET /api/status` until it responds with HTTP 200

#### Scenario: Startup failure
- **WHEN** the Python service fails to start on any of the attempted ports
- **THEN** the webview displays an error message to the user

### Requirement: Simplified startup sequence
The Electrobun host SHALL load the UI immediately via `views://` and start the Python service in parallel. The UI SHALL show a connecting state until the Python service is ready.

#### Scenario: Parallel startup
- **WHEN** the app launches
- **THEN** the webview loads instantly showing a "Connecting to camera service..." state
- **AND** the Python service starts in the background
- **AND** once the service is ready, the UI transitions to the live camera view

### Requirement: Graceful shutdown
The Electrobun host SHALL send SIGTERM to the Python process when the main window closes, consistent with current behavior.

#### Scenario: Window close
- **WHEN** the user closes the main window
- **THEN** SIGTERM is sent to the Python process
- **AND** the app exits cleanly after the Python process terminates

### Requirement: Build script updates
The build script SHALL remove `gradio` from `uv pip install` dependencies and add `fastapi` and `uvicorn[standard]`. The script SHALL copy `src/ui/web/` into the build output for inclusion via `build.copy`.

#### Scenario: Reduced bundle
- **WHEN** the build script runs
- **THEN** the resulting `site-packages` does not contain `gradio`, `pandas`, `huggingface_hub`, or other Gradio-only dependencies
- **AND** `fastapi` and `uvicorn` are installed

#### Scenario: UI files bundled
- **WHEN** the build script runs
- **THEN** static HTML/CSS/JS files from `src/ui/web/` are included in `desktop/build/python/app/` or equivalent location accessible via `views://`

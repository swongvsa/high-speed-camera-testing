## ADDED Requirements

### Requirement: MJPEG frame stream endpoint
The system SHALL expose a `GET /stream` endpoint that returns a continuous MJPEG stream (`multipart/x-mixed-replace; boundary=frame`) of JPEG-encoded camera frames. The stream SHALL run at the preview frame rate (~30fps) regardless of the capture frame rate. If no camera is connected, the endpoint SHALL return a placeholder frame indicating "No Camera".

#### Scenario: Stream with connected camera
- **WHEN** a client requests `GET /stream` and a camera is connected
- **THEN** the server responds with `Content-Type: multipart/x-mixed-replace; boundary=frame` and continuously sends JPEG frames at the preview rate

#### Scenario: Stream with no camera
- **WHEN** a client requests `GET /stream` and no camera is connected
- **THEN** the server responds with a single static placeholder frame showing a "No Camera" message

#### Scenario: Stream quality
- **WHEN** frames are encoded for the MJPEG stream
- **THEN** each frame SHALL be JPEG-encoded with a configurable quality parameter (default 80)

### Requirement: Camera settings endpoint
The system SHALL expose a `POST /api/settings` endpoint accepting JSON body with camera settings. Supported settings SHALL include: `roi_preset` (string), `exposure_ms` (float), `gain` (float), `auto_exposure` (boolean). Settings SHALL be applied to the camera immediately under a thread lock. The endpoint SHALL return the current effective settings as JSON.

#### Scenario: Update ROI preset
- **WHEN** a client sends `POST /api/settings` with `{"roi_preset": "1280x1024 · 120 fps"}`
- **THEN** the camera ROI is updated and the response includes the new effective settings including actual FPS

#### Scenario: Update exposure
- **WHEN** a client sends `POST /api/settings` with `{"exposure_ms": 2.0}`
- **THEN** the camera exposure is set to 2.0ms and the response confirms the applied value

#### Scenario: Invalid setting value
- **WHEN** a client sends `POST /api/settings` with an out-of-range value
- **THEN** the server responds with HTTP 422 and an error message describing the valid range

### Requirement: Camera status endpoint
The system SHALL expose a `GET /api/status` endpoint returning JSON with current camera state: connection status, current settings (ROI, exposure, gain, auto_exposure), performance metrics (target_fps, capture_fps, preview_fps), buffer state (capacity, fill level, is_full), and slowdown factor.

#### Scenario: Status with connected camera
- **WHEN** a client requests `GET /api/status` and a camera is connected
- **THEN** the response includes all camera metrics as JSON with HTTP 200

#### Scenario: Status with no camera
- **WHEN** a client requests `GET /api/status` and no camera is connected
- **THEN** the response includes `{"connected": false}` with HTTP 200

### Requirement: Camera enumeration endpoint
The system SHALL expose a `GET /api/cameras` endpoint returning a JSON array of available camera identifiers (friendly names). This replaces the Gradio dropdown population.

#### Scenario: Cameras available
- **WHEN** a client requests `GET /api/cameras`
- **THEN** the response is a JSON array of camera name strings, e.g. `["MV-GE202GC (169.254.22.149)"]`

#### Scenario: No cameras found
- **WHEN** a client requests `GET /api/cameras` and no cameras are detected
- **THEN** the response is an empty JSON array `[]`

### Requirement: Recording endpoints
The system SHALL expose `POST /api/record` to trigger clip saving from the ring buffer, and `GET /api/record/status` to poll recording progress. The record endpoint SHALL accept JSON with `clip_duration_sec` (float) and `slowdown_factor` (int). The status endpoint SHALL return `{"state": "idle|recording|saving|done|error", "path": "...", "error": "..."}`.

#### Scenario: Save a clip
- **WHEN** a client sends `POST /api/record` with `{"clip_duration_sec": 5.0, "slowdown_factor": 8}`
- **THEN** the server begins extracting frames from the ring buffer and encoding a slow-motion MP4
- **AND** `GET /api/record/status` returns `{"state": "saving"}` while in progress

#### Scenario: Clip save complete
- **WHEN** clip encoding finishes successfully
- **THEN** `GET /api/record/status` returns `{"state": "done", "path": "/path/to/clip.mp4"}`

#### Scenario: Download saved clip
- **WHEN** a clip has been saved and the client requests `GET /api/record/download`
- **THEN** the server responds with the MP4 file as a download (`Content-Disposition: attachment`)

### Requirement: Graceful shutdown
The system SHALL register a SIGTERM handler that releases the camera device, stops the capture thread, and shuts down the HTTP server cleanly.

#### Scenario: SIGTERM received
- **WHEN** the Python process receives SIGTERM (from Electrobun window close)
- **THEN** the camera is released, capture threads are stopped, and the process exits within 3 seconds

### Requirement: CORS support
The system SHALL enable CORS for all origins on all API endpoints, since the webview loads from `views://` scheme (different origin than `http://localhost`).

#### Scenario: Cross-origin request from views://
- **WHEN** the webview at `views://main/index.html` sends a `fetch()` to `http://localhost:PORT/api/status`
- **THEN** the response includes `Access-Control-Allow-Origin: *` and the request succeeds

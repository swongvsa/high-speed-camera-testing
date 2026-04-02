## ADDED Requirements

### Requirement: Viewfinder displays MJPEG stream
The UI SHALL display the live camera feed using an `<img>` element with its `src` set to the MJPEG stream endpoint (`http://localhost:PORT/stream`). No JavaScript frame rendering logic is needed.

#### Scenario: Camera connected
- **WHEN** the page loads and a camera is streaming
- **THEN** the `<img>` element displays live frames updating at the preview frame rate

#### Scenario: Camera disconnected
- **WHEN** the MJPEG stream returns a placeholder frame
- **THEN** the `<img>` element displays the "No Camera" placeholder

### Requirement: Camera source selector
The UI SHALL include a dropdown populated by `GET /api/cameras`. Selecting a camera SHALL send `POST /api/settings` with the chosen camera identifier.

#### Scenario: Multiple cameras available
- **WHEN** `GET /api/cameras` returns multiple entries
- **THEN** the dropdown shows all camera names and defaults to the first

#### Scenario: Camera selection changes
- **WHEN** the user selects a different camera from the dropdown
- **THEN** the UI sends `POST /api/settings` with the new camera source

### Requirement: ROI preset control
The UI SHALL include a dropdown for ROI presets matching the current options (e.g., "1280x1024 - 120 fps", "640x480 - 480 fps"). Selecting a preset SHALL send `POST /api/settings` with the chosen `roi_preset`.

#### Scenario: ROI preset change
- **WHEN** the user selects a new ROI preset
- **THEN** `POST /api/settings` is sent with the new roi_preset value
- **AND** the viewfinder resolution updates accordingly

### Requirement: Slowdown preset buttons
The UI SHALL display preset buttons for slowdown factors (2x, 4x, 8x, 16x, 32x). The active preset SHALL be visually highlighted. Clicking a button SHALL update the slowdown factor state used for recording.

#### Scenario: Select slowdown factor
- **WHEN** the user clicks the "8x" preset button
- **THEN** the button becomes visually active, other buttons become inactive
- **AND** the settings card updates to show the new actual slowdown and output duration

### Requirement: Exposure and gain controls
The UI SHALL include an auto-exposure checkbox, exposure slider (0.05–100ms), and gain slider (1.0–16.0x). Changes SHALL send `POST /api/settings` with the updated values. When auto-exposure is enabled, the exposure slider SHALL be disabled.

#### Scenario: Manual exposure adjustment
- **WHEN** the user adjusts the exposure slider to 5.0ms with auto-exposure off
- **THEN** `POST /api/settings` is sent with `{"exposure_ms": 5.0, "auto_exposure": false}`

#### Scenario: Auto exposure enabled
- **WHEN** the user checks the auto-exposure checkbox
- **THEN** the exposure slider becomes disabled and `POST /api/settings` is sent with `{"auto_exposure": true}`

### Requirement: Performance metrics display
The UI SHALL display real-time performance metrics: target FPS, capture FPS, and preview FPS. These SHALL be updated by polling `GET /api/status` at a regular interval (~1 second).

#### Scenario: Metrics update
- **WHEN** the status poll returns new FPS values
- **THEN** the performance display updates to show the current target, capture, and preview FPS values

### Requirement: Buffer status display
The UI SHALL display the ring buffer fill level as a progress bar and text indicator. Buffer state SHALL be obtained from `GET /api/status` polling.

#### Scenario: Buffer filling
- **WHEN** the buffer is at 75% capacity
- **THEN** the progress bar shows 75% filled and the text shows the fill percentage

#### Scenario: Buffer full
- **WHEN** the buffer reaches 100% capacity
- **THEN** the progress bar shows full with a distinct visual style and the record button becomes enabled

### Requirement: Record and save clip
The UI SHALL include a record button that sends `POST /api/record` and then polls `GET /api/record/status` until completion. While saving, the button SHALL show a progress state. On completion, the UI SHALL display a video preview and download link.

#### Scenario: Save clip flow
- **WHEN** the user clicks "Save Slow-Mo Clip" with the buffer full
- **THEN** `POST /api/record` is sent with current slowdown_factor and clip_duration_sec
- **AND** the button shows "Saving..." while the clip is being encoded
- **AND** on completion, a `<video>` preview and download link appear

### Requirement: Settings disclosure card
The UI SHALL display a read-only settings card showing derived values: capture rate, actual slowdown factor, and output duration. These update when slowdown factor or clip duration changes.

#### Scenario: Settings card reflects state
- **WHEN** the user selects 8x slowdown and 5s clip duration at 120fps capture
- **THEN** the settings card shows "Capture Rate: 120 fps", "Actual Slowdown: 4.0x", and computed output duration

### Requirement: Dark theme
The UI SHALL use a dark color scheme consistent with the existing design: `#0f1117` background, `#1a1d27` panels, `#e2e8f0` text. Status chips SHALL use the existing color palette (safe/warning/danger/active/idle).

#### Scenario: Visual consistency
- **WHEN** the UI loads
- **THEN** the color scheme matches the existing dark theme defined in DARK_CSS

### Requirement: Duration preset buttons
The UI SHALL display quick-select buttons for clip duration (2s, 3s, 5s, 7s, 10s). The active duration SHALL be visually highlighted. Selecting a duration updates the clip_duration_sec state.

#### Scenario: Select clip duration
- **WHEN** the user clicks the "5s" duration button
- **THEN** the button becomes active and the output duration card updates

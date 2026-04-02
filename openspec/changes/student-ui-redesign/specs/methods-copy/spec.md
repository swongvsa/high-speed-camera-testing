## ADDED Requirements

### Requirement: Methods citation card
The controls panel SHALL display a "For Your Methods Section" card showing a pre-formatted citation sentence that reflects the current camera settings.

#### Scenario: Citation updates with settings
- **WHEN** the slowdown preset or ROI changes
- **THEN** the citation card updates to reflect the new capture FPS, shutter speed, resolution, playback FPS, and slowdown factor

#### Scenario: Citation format
- **WHEN** settings are: 240 FPS capture, 1/500s shutter, 816×312 px, 30 FPS playback, 8× slowdown
- **THEN** the citation reads: "Video was captured at 240 fps using a MindVision GigE camera (816×312 px ROI) with a 1/500s shutter speed and played back at 30 fps, resulting in 8× slow motion."

### Requirement: One-tap copy to clipboard
The methods citation card SHALL include a "Copy" button that writes the citation string to the system clipboard.

#### Scenario: Successful clipboard copy
- **WHEN** a student clicks the "Copy" button
- **THEN** the citation string is written to the system clipboard via `navigator.clipboard.writeText`
- **THEN** the button briefly changes to "Copied ✓" for 2 seconds then reverts to "Copy"

#### Scenario: Clipboard unavailable (non-HTTPS)
- **WHEN** `navigator.clipboard` is unavailable (non-localhost HTTP context)
- **THEN** the citation text is displayed in a visible, user-selectable `<textarea>` as fallback
- **THEN** the button label changes to "Select All" and focuses the textarea

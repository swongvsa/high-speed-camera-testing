## ADDED Requirements

### Requirement: Output duration preview
Before saving, the save panel SHALL display the expected output duration of the slow-motion clip in large, prominent text.

#### Scenario: Output duration calculated
- **WHEN** the buffer has sufficient footage and a slowdown preset is active
- **THEN** the save panel shows "YOUR CLIP WILL BE" followed by the output duration in seconds (e.g., "40 seconds")
- **THEN** a subtext reads "of slow-motion video from Xs of real footage" where X is the selected clip duration

#### Scenario: Output duration updates with duration selector
- **WHEN** a student selects a different clip duration (2s, 5s, 10s)
- **THEN** the output duration display updates immediately (e.g., 5s × 8× = 40s)

### Requirement: Clip duration quick-select buttons
The save panel SHALL provide quick-select buttons for common clip durations (2s, 5s, 10s) replacing the continuous slider.

#### Scenario: Student selects clip duration
- **WHEN** a student taps a duration button (e.g., "5s")
- **THEN** the button highlights as selected
- **THEN** `clip_duration_sec` updates to the selected value
- **THEN** the output duration preview updates accordingly

#### Scenario: Buffer not yet full for selected duration
- **WHEN** the selected duration exceeds the current buffer fill
- **THEN** the Save button is disabled
- **THEN** the buffer status shows "buffering… X.Xs / Ys"

### Requirement: Post-save state
After a successful save, the save panel SHALL transition to a "Saved" state showing the result and download option.

#### Scenario: Successful save transition
- **WHEN** a clip is saved successfully
- **THEN** the save panel replaces its content with: a green checkmark icon, "Saved!" heading, output duration summary, a preview tap target, a "Download MP4" button, and a "↩ Save Another Clip" button
- **THEN** the header chip updates to show "✓ Saved"

#### Scenario: Preview tap target
- **WHEN** a student taps the preview area in the post-save state
- **THEN** the saved video begins playing in the `gr.Video` component (existing behavior, existing component)

#### Scenario: Save another clip
- **WHEN** a student clicks "↩ Save Another Clip"
- **THEN** the save panel resets to the buffer/duration/save state
- **THEN** the buffer progress reflects current fill (camera continues recording throughout)

### Requirement: Camera connection status chip
The header bar SHALL display a camera connection status chip showing the connected camera name or a disconnected state.

#### Scenario: Camera connected
- **WHEN** a MindVision GigE camera is detected and opened
- **THEN** the header chip shows "📷 [FriendlyName]" with an active blue style

#### Scenario: Camera not found
- **WHEN** no camera is detected on startup or the connection drops
- **THEN** the header chip shows "📷 No Camera" with a danger red style
- **THEN** a "Fix Connection" link appears that opens the IP troubleshooting guide

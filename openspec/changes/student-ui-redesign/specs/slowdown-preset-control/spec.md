## ADDED Requirements

### Requirement: Slowdown preset selector
The UI SHALL provide five slowdown preset buttons (2×, 4×, 8×, 16×, 32×) as the primary speed control, replacing the target FPS and playback FPS sliders.

#### Scenario: Student selects a slowdown preset
- **WHEN** a student clicks a slowdown preset button (e.g., 8×)
- **THEN** the selected button is highlighted as active
- **THEN** `target_fps` is set to `min(roi_max_fps[current_preset], playback_fps * 8)`
- **THEN** `playback_fps` is set to 30 (standard playback)
- **THEN** the camera begins capturing at the derived `target_fps`

#### Scenario: Preset exceeds ROI maximum FPS
- **WHEN** a student selects a preset whose derived `target_fps` exceeds the current ROI's maximum FPS
- **THEN** `target_fps` is clamped to `roi_max_fps[current_preset]`
- **THEN** the settings disclosure shows the actual achieved slowdown factor, not the selected one
- **THEN** the preset button is visually dimmed to indicate partial achievement

### Requirement: Settings disclosure card
Below the preset selector, the UI SHALL display the derived camera settings that result from the selected slowdown factor.

#### Scenario: Settings update on preset change
- **WHEN** a slowdown preset is selected
- **THEN** the disclosure card shows: Capture Rate (FPS), Shutter Speed (1/N s), Resolution (W×H px), Playback (FPS)
- **THEN** all values update within one render cycle

#### Scenario: Shutter speed auto-calculated
- **WHEN** a preset is selected
- **THEN** shutter speed is set to `1 / target_fps` seconds (one full frame time) by default unless overridden in Advanced Settings

### Requirement: Preset availability based on ROI
Presets that cannot be achieved at the current ROI setting SHALL be visually distinguished.

#### Scenario: Unavailable preset at current ROI
- **WHEN** the current ROI preset has a max FPS lower than `playback_fps * slowdown_factor` for a given preset
- **THEN** that slowdown preset button is rendered with reduced opacity
- **THEN** selecting it still works but shows the clamped actual factor

### Requirement: Advanced Settings accordion
The UI SHALL provide a collapsed accordion below the preset selector containing manual override controls for Auto Exposure, Shutter Speed, and Analog Gain.

#### Scenario: Advanced settings hidden by default
- **WHEN** the controls panel first loads
- **THEN** the Advanced Settings accordion is collapsed
- **THEN** only the label and "Exposure · Gain" hint are visible

#### Scenario: Student opens Advanced Settings
- **WHEN** a student clicks the Advanced Settings accordion header
- **THEN** the accordion expands to reveal Auto Exposure toggle, Shutter Speed value, and Analog Gain value
- **THEN** Shutter Speed shows the auto-calculated value with a note "auto-set from Nx preset · tap to override"

#### Scenario: Manual shutter override
- **WHEN** a student taps the Shutter Speed value while in manual mode
- **THEN** a slider or input appears allowing manual entry
- **THEN** the auto-calculated note is replaced with a "manual" indicator
- **THEN** the exposure safety guardrail warning activates if the entered value exceeds frame time

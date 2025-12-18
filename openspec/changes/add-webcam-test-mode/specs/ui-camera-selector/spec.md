## ADDED Requirements

### Requirement: UI dropdown for camera source selection
The UI SHALL provide a dropdown allowing the user to select the active camera source for streaming.

#### Scenario: Dropdown lists enumerated sources
- **WHEN** the UI loads
- **THEN** the dropdown SHALL be populated with the currently enumerated camera sources

#### Scenario: Dropdown selection switches active source
- **WHEN** the user selects a different camera source in the dropdown
- **THEN** the system SHALL switch streaming to the newly selected source

### Requirement: Default selection behavior
The UI SHALL default to a MindVision camera source when available, otherwise the first available webcam source.

#### Scenario: MindVision available
- **WHEN** at least one MindVision camera is available
- **THEN** the default selection SHALL be the first MindVision camera

#### Scenario: Only webcams available
- **WHEN** no MindVision cameras are available and at least one webcam source is available
- **THEN** the default selection SHALL be the first available webcam source

### Requirement: Recording works with selected source
The UI SHALL allow saving a clip from the active stream using the existing recording workflow.

#### Scenario: Save clip from webcam
- **WHEN** the active source is a webcam and the user clicks the save button
- **THEN** the system SHALL save a video clip from the buffered frames and offer it for download

#### Scenario: Save clip from MindVision camera
- **WHEN** the active source is a MindVision camera and the user clicks the save button
- **THEN** the system SHALL save a video clip from the buffered frames and offer it for download

### Requirement: Error messaging
The UI SHALL display user-friendly errors when camera initialization fails or when a source becomes unavailable.

#### Scenario: Webcam open fails
- **WHEN** a selected webcam source cannot be opened
- **THEN** the UI SHALL display an error explaining the failure and remain usable for selecting a different source

#### Scenario: Source disconnected
- **WHEN** the active camera source disconnects during streaming
- **THEN** the UI SHALL display an error and allow retry or selecting a different source

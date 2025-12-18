## ADDED Requirements

### Requirement: Enumerate camera sources (MindVision + webcam)
The system SHALL enumerate available camera sources, including MindVision cameras (via MVSDK) and webcams (via OpenCV `cv2.VideoCapture` indices), and present them as selectable items.

#### Scenario: MindVision camera present
- **WHEN** the system enumerates camera sources
- **THEN** each MVSDK-enumerated device SHALL appear as a selectable source with a stable identifier and friendly label

#### Scenario: Webcams present
- **WHEN** the system enumerates camera sources
- **THEN** each probed webcam index that can be opened SHALL appear as a selectable source with a stable identifier and friendly label

#### Scenario: No cameras present
- **WHEN** the system enumerates camera sources and finds no available devices
- **THEN** it SHALL return an empty list (not `None`) and surface a user-friendly error when attempting to start streaming

### Requirement: Select and initialize a camera source
The system SHALL allow selecting a camera source and SHALL initialize streaming for the selected source using a context-managed lifecycle.

#### Scenario: Select MindVision source
- **WHEN** a MindVision camera source is selected
- **THEN** the system SHALL initialize the MVSDK-backed camera and begin streaming frames

#### Scenario: Select webcam source
- **WHEN** a webcam source is selected
- **THEN** the system SHALL initialize an OpenCV `VideoCapture` for that index and begin streaming frames

### Requirement: Standardize frame format
The system SHALL standardize streamed frames to numpy arrays suitable for Gradio image streaming.

#### Scenario: Webcam returns BGR frames
- **WHEN** OpenCV returns a color frame in BGR format
- **THEN** the system SHALL convert it to RGB before yielding

#### Scenario: Webcam returns grayscale frames
- **WHEN** OpenCV returns a grayscale frame
- **THEN** the system SHALL yield a 2D numpy array representing grayscale pixels

### Requirement: Cleanup on session end or source switch
The system SHALL release underlying camera resources when a session ends or when switching camera sources, and SHALL NOT raise from cleanup paths.

#### Scenario: Source switch cleanup
- **WHEN** a user switches from one camera source to another
- **THEN** the system SHALL stop the previous stream and release its resources before starting the new stream

#### Scenario: Cleanup on disconnect
- **WHEN** a user disconnects or the session ends
- **THEN** the system SHALL release camera resources so other apps or subsequent sessions can use the device

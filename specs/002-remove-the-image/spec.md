# Feature Specification: Remove Image Segmentation and Face Recognition Pipelines

**Feature Branch**: `002-remove-the-image`  
**Created**: 2025-10-09  
**Status**: Draft  
**Input**: User description: "remove the image segmentation and face processing pipelines"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Raw Camera Feed Without Processing (Priority: P1)

As a camera operator, I want to view the raw camera feed without any image processing overlays, so that I can see the unmodified video stream and reduce system resource usage.

**Why this priority**: This is the core requirement - removing the processing pipelines to provide a clean, unprocessed camera feed. This delivers immediate value by simplifying the application and reducing computational overhead.

**Independent Test**: Can be fully tested by launching the application, verifying the camera feed displays without segmentation masks or face recognition boxes, and confirming no processing-related UI controls are visible.

**Acceptance Scenarios**:

1. **Given** the application is launched, **When** I view the camera feed, **Then** I see the raw video stream without any segmentation masks, bounding boxes, or face recognition annotations
2. **Given** the application is running, **When** I inspect the UI, **Then** I see no controls for enabling/disabling segmentation or face recognition
3. **Given** the application is displaying the camera feed, **When** I check system resource usage, **Then** CPU and memory usage is lower compared to when processing was enabled

---

### User Story 2 - Simplified UI Without Processing Controls (Priority: P2)

As a user, I want a simplified interface that only shows camera controls, so that I can focus on basic camera operations without confusion from removed features.

**Why this priority**: After removing the processing pipelines, the UI should be cleaned up to remove all related controls. This ensures a clean user experience without orphaned UI elements.

**Independent Test**: Can be fully tested by reviewing the UI and confirming that all segmentation and face recognition controls (checkboxes, sliders, dropdowns, enrollment forms) have been removed.

**Acceptance Scenarios**:

1. **Given** the application UI is loaded, **When** I scan the interface, **Then** I see no tabs or controls for "Segmentation" or "Face Recognition"
2. **Given** the application is running, **When** I look at the control panel, **Then** I only see camera-specific controls (exposure, resolution, etc.)
3. **Given** the interface is displayed, **When** I check for enrollment features, **Then** I find no face enrollment or database management UI

---

### User Story 3 - Verify Code Cleanup (Priority: P3)

As a developer, I want all segmentation and face recognition code removed from the codebase, so that the application is maintainable and doesn't contain unused dependencies or dead code.

**Why this priority**: Code cleanliness is important for long-term maintenance but doesn't affect user-facing functionality immediately.

**Independent Test**: Can be fully tested by reviewing the codebase and confirming that the `src/segmentation/` and `src/face_recognition/` directories are deleted, and all related imports and function calls are removed.

**Acceptance Scenarios**:

1. **Given** the codebase is examined, **When** I check the src directory, **Then** I find no `segmentation/` or `face_recognition/` directories
2. **Given** the main application file is reviewed, **When** I search for processing-related imports, **Then** I find no imports from segmentation or face recognition modules
3. **Given** the dependencies are checked, **When** I review `pyproject.toml`, **Then** processing-specific dependencies (ultralytics, deepface, supervision) are removed or marked as optional

---

### Edge Cases

- What happens when the application is running and processing code is removed? (Should gracefully handle missing modules without crashing)
- How does system handle if configuration files still reference removed processing features? (Should ignore or provide clear warnings)
- What if tests still reference the removed functionality? (Tests should be updated or removed to match new codebase state)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove all image segmentation processing code from the camera feed pipeline
- **FR-002**: System MUST remove all face recognition processing code from the camera feed pipeline
- **FR-003**: System MUST display the raw, unprocessed camera feed without any overlays or annotations
- **FR-004**: System MUST remove all UI controls related to segmentation (model selection, confidence threshold, class selection, tracking toggle)
- **FR-005**: System MUST remove all UI controls related to face recognition (model selection, detector selection, threshold slider, enrollment form, face database management)
- **FR-006**: System MUST remove the `src/segmentation/` directory and all its contents
- **FR-007**: System MUST remove the `src/face_recognition/` directory and all its contents
- **FR-008**: System MUST remove all imports of segmentation and face recognition modules from `src/ui/app.py`
- **FR-009**: System MUST remove processing-specific dependencies from `pyproject.toml` (ultralytics, deepface, supervision, opencv-python)
- **FR-010**: System MUST update or remove tests that reference the removed functionality
- **FR-011**: System MUST simplify the UI to show only camera controls (exposure settings, camera selection if applicable)
- **FR-012**: System MUST continue to stream camera feed at the same or better performance without processing overhead

### Key Entities

- **Camera Feed**: Raw video stream from the camera device without any processing or annotations
- **UI Controls**: Simplified control panel containing only camera-related settings (exposure, etc.)
- **Processing Pipeline**: (To be removed) The segmentation and face recognition processing stages that were previously applied to frames

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view the camera feed without any segmentation masks or face recognition boxes appearing on frames
- **SC-002**: UI loads and displays without any segmentation or face recognition controls visible
- **SC-003**: System resource usage (CPU and memory) decreases by at least 30% compared to when processing was enabled
- **SC-004**: Camera feed frame rate maintains at least 25 FPS without processing overhead
- **SC-005**: Application startup time is reduced by at least 20% due to removed model loading
- **SC-006**: Codebase size is reduced by removing at least 15 source files (segmentation + face recognition modules)
- **SC-007**: All existing tests pass after removal, or are appropriately updated/removed to reflect new functionality
- **SC-008**: Application continues to support all core camera operations (initialization, streaming, exposure control, cleanup)

## Assumptions

1. The camera feed functionality (capture, device initialization, frame generation) will remain unchanged
2. The Gradio UI framework and camera SDK (MVSDK) will continue to be used
3. Exposure controls and other camera-specific settings should be preserved
4. The application should still support the same deployment model (localhost-only access)
5. Tests for core camera functionality should remain and continue to pass
6. Dependencies that are only used for processing (ultralytics, deepface, supervision) can be safely removed without affecting core functionality

## Dependencies

- Depends on understanding which dependencies are shared vs. processing-specific (e.g., numpy/opencv may be used by both camera and processing)
- Requires review of tests to determine which need updating vs. removal
- May need to verify that no other parts of the system depend on the removed modules

## Out of Scope

- Adding new camera features or controls
- Modifying the camera capture mechanism or SDK integration
- Changing the Gradio framework or deployment model
- Performance optimization beyond what naturally results from removing processing
- Adding new video processing features to replace the removed ones

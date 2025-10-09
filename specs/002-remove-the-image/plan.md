# Implementation Plan: Remove Image Segmentation and Face Recognition Pipelines

**Branch**: `002-remove-the-image` | **Date**: 2025-10-09 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/002-remove-the-image/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Remove all image segmentation and face recognition processing pipelines from the camera application to provide a simplified, raw camera feed viewer. This involves removing the `src/segmentation/` and `src/face_recognition/` directories, cleaning up UI controls, removing processing-specific dependencies (ultralytics, deepface, supervision), and updating tests. The result is a streamlined application focused solely on camera capture and display with reduced resource usage and faster startup time.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: Gradio >=4.0, numpy >=1.24, MVSDK (camera SDK)  
**Storage**: File-based (face embeddings database to be removed)  
**Testing**: pytest with contract/integration/unit tests  
**Target Platform**: macOS (M1) with localhost-only Gradio server  
**Project Type**: Single project (desktop application with web UI)  
**Performance Goals**: 25+ FPS camera stream, <2s startup time (after removal)  
**Constraints**: Localhost-only access (127.0.0.1), single viewer session  
**Scale/Scope**: Single camera device, single user, ~15 files to remove

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: No project-specific constitution file found (template only). Using general software engineering principles:

### Quality Gates

- ✅ **Code Removal Safety**: All code removal must preserve existing camera functionality
  - **Status**: PASS - Camera capture, device initialization, and exposure controls are independent modules
  - **Verification**: Review imports and dependencies in camera modules to ensure no coupling to processing code

- ✅ **Test Coverage**: Core camera tests must continue to pass after removal
  - **Status**: PASS - Contract tests for camera device, video frame, and viewer session are independent
  - **Verification**: Run pytest after removal to ensure no regressions in core functionality

- ✅ **Dependency Safety**: Dependencies must be removed without breaking shared code
  - **Status**: NEEDS RESEARCH - Determine if opencv-python is used by camera modules or only processing
  - **Verification**: Search codebase for opencv usage in camera/ directory

- ✅ **Backward Compatibility**: Application behavior for core features must remain unchanged
  - **Status**: PASS - Camera streaming, exposure control, and session management are preserved
  - **Verification**: Integration tests verify end-to-end camera functionality

## Project Structure

### Documentation (this feature)

```
specs/002-remove-the-image/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── ui-simplified.md # Simplified UI contract (no processing controls)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── camera/              # PRESERVE - Core camera functionality
│   ├── __init__.py
│   ├── capture.py       # Frame generator (no processing)
│   ├── device.py        # Camera device interface
│   ├── errors.py        # Camera errors
│   ├── init.py          # SDK initialization
│   └── video_frame.py   # Frame data structure
├── lib/                 # PRESERVE - SDK wrapper
│   ├── __init__.py
│   └── mvsdk.py         # Camera SDK bindings
├── ui/                  # MODIFY - Remove processing UI
│   ├── __init__.py
│   ├── app.py           # EDIT: Remove segmentation/face recognition UI + imports
│   ├── errors.py        # PRESERVE
│   ├── lifecycle.py     # PRESERVE - Camera lifecycle management
│   └── session.py       # PRESERVE - Viewer session management
├── segmentation/        # DELETE - Entire directory
└── face_recognition/    # DELETE - Entire directory

tests/
├── contract/            # REVIEW - Update if needed
│   ├── test_camera_device_contract.py      # PRESERVE
│   ├── test_gradio_ui_contract.py          # EDIT: Remove processing tests
│   ├── test_video_frame_contract.py        # PRESERVE
│   └── test_viewer_session_contract.py     # PRESERVE
├── integration/         # REVIEW - Update if needed
│   ├── test_scenario_01_success.py         # EDIT: Remove processing expectations
│   ├── test_scenario_02_single_viewer.py   # PRESERVE
│   ├── test_scenario_03_no_camera.py       # PRESERVE
│   ├── test_scenario_04_cleanup.py         # PRESERVE
│   └── test_scenario_05_localhost.py       # PRESERVE
└── unit/                # REVIEW - Update if needed
    ├── test_capture.py                     # PRESERVE
    ├── test_errors.py                      # PRESERVE
    └── test_init.py                        # PRESERVE
```

**Structure Decision**: Single project structure is used. This is a desktop application with a web-based UI (Gradio). The removal process will:
1. Delete two top-level directories in `src/` (segmentation + face_recognition)
2. Simplify `src/ui/app.py` by removing processing-related code
3. Update tests to remove processing-related assertions
4. Clean up dependencies in `pyproject.toml`

## Complexity Tracking

*No constitution violations - this is a code removal/simplification task*

No entries required. This feature reduces complexity by removing ~15 source files and multiple dependencies.

---

## Phase 0: Research & Discovery

### Research Questions

Based on the Technical Context unknowns, we need to research:

1. **Dependency Analysis**: 
   - Question: Is `opencv-python` used by camera modules or only by processing modules?
   - Why: Need to determine if opencv-python can be safely removed or must be retained
   - Method: Search for `import cv2` and `opencv` usage in `src/camera/`, `src/lib/`, and `src/ui/` (excluding processing code)

2. **Test Impact Analysis**:
   - Question: Which tests reference segmentation or face recognition functionality?
   - Why: Need to identify which tests to update vs. remove
   - Method: Search test files for imports/references to `segmentation` and `face_recognition` modules

3. **UI Simplification Approach**:
   - Question: What is the minimal viable UI after removing processing controls?
   - Why: Need to ensure a clean, functional UI remains after removal
   - Method: Review current `src/ui/app.py` structure and identify camera-only controls to preserve

4. **Shared Utility Analysis**:
   - Question: Are there any shared utilities or helper functions between camera and processing code?
   - Why: Need to ensure no accidental deletion of shared code
   - Method: Review imports and cross-references between modules

### Research Tasks

**Task 1: Dependency Usage Audit**
- Search `src/camera/`, `src/lib/`, `src/ui/lifecycle.py`, `src/ui/session.py` for opencv usage
- Determine which dependencies are camera-only vs. processing-only
- Document safe-to-remove vs. must-retain dependencies

**Task 2: Test Suite Analysis**
- List all test files that import or reference processing modules
- Categorize tests as: DELETE (processing-only), UPDATE (mixed), PRESERVE (camera-only)
- Document specific test cases that need modification

**Task 3: UI Control Inventory**
- Identify all camera-specific controls in current UI (exposure, camera selection, etc.)
- Identify all processing-specific controls (segmentation, face recognition tabs)
- Design simplified UI layout with camera controls only

**Task 4: Integration Point Review**
- Review how processing pipelines are integrated into frame stream
- Identify all points in code where processing is invoked
- Document clean removal strategy (what to delete vs. what to simplify)

### Expected Outcomes

After Phase 0 research, we will have:
- ✅ Clear list of dependencies to remove vs. retain
- ✅ Test modification plan (which tests to delete, update, or preserve)
- ✅ UI simplification design (mockup/description of final UI)
- ✅ Code removal checklist (files to delete, functions to remove, imports to clean up)

---

## Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete with all research questions answered

### Data Model

For this feature, the data model simplification involves:

**Entities to Remove:**
- Face embeddings database (file-based storage)
- Segmentation detection results (transient)
- Face recognition results (transient)

**Entities to Preserve:**
- VideoFrame (raw camera frame data)
- CameraDevice (camera hardware interface)
- ViewerSession (session management)

Document in `data-model.md`:
- Simplified frame flow (camera → display, no processing)
- Preserved entities and their contracts
- Removed entities and migration notes (if any persisted data)

### API/Interface Contracts

**File: contracts/ui-simplified.md**

Define the simplified UI contract:
- Camera feed display (image component)
- Camera controls (exposure settings only)
- Session lifecycle (start/stop/cleanup)
- Debug info display (camera status, FPS, no processing metrics)

**File: contracts/frame-stream.md**

Define the simplified frame streaming contract:
- Input: None (no processing parameters)
- Output: Raw frame + camera debug info
- No processing annotations or overlays

### Quickstart Guide

**File: quickstart.md**

Provide migration guide for users:
- What changed (processing removed)
- New simplified UI overview
- Performance improvements to expect
- Migration notes (if any saved embeddings need handling)

### Agent Context Update

After generating contracts and design docs, update agent context:

```bash
cd /Users/swong/dev/high-speed-camera-testing
.specify/scripts/bash/update-agent-context.sh opencode
```

This will:
- Update `AGENTS.md` with new feature context
- Document removed technologies (ultralytics, deepface, supervision)
- Update project structure to reflect removed directories

---

## Phase 2: Task Breakdown

**Note**: Phase 2 is handled by `/speckit.tasks` command (not part of this plan output).

The tasks command will generate a detailed, prioritized task list in `tasks.md` based on:
- User stories from spec (P1: raw feed, P2: UI cleanup, P3: code cleanup)
- Research findings from Phase 0
- Design contracts from Phase 1
- Test requirements (contract tests, integration tests)

Expected task categories:
1. Code deletion (remove directories and files)
2. UI simplification (edit app.py, remove controls)
3. Dependency cleanup (edit pyproject.toml)
4. Test updates (edit/delete test files)
5. Verification (run tests, check performance)

---

## Pre-Implementation Checklist

Before running `/speckit.tasks`, verify:

- [ ] Phase 0: `research.md` exists with dependency analysis complete
- [ ] Phase 0: Test impact analysis documented
- [ ] Phase 0: UI simplification design complete
- [ ] Phase 1: `data-model.md` exists with entity changes documented
- [ ] Phase 1: `contracts/` contains simplified UI and frame stream contracts
- [ ] Phase 1: `quickstart.md` exists with migration guide
- [ ] Phase 1: Agent context updated (AGENTS.md reflects removed modules)
- [ ] Constitution re-check: All gates still passing after design

---

## Success Metrics (from spec)

After implementation, verify these success criteria:

- **SC-001**: Camera feed displays without processing annotations ✓
- **SC-002**: UI shows no segmentation/face recognition controls ✓
- **SC-003**: 30%+ reduction in CPU/memory usage ✓
- **SC-004**: 25+ FPS maintained ✓
- **SC-005**: 20%+ faster startup ✓
- **SC-006**: ~15 source files removed ✓
- **SC-007**: All camera tests pass ✓
- **SC-008**: Core camera operations unchanged ✓

---

## Notes

This is a **removal/simplification** feature, not an addition. The implementation philosophy is:
- **Delete aggressively**: Remove entire modules cleanly
- **Preserve carefully**: Keep camera functionality untouched
- **Test thoroughly**: Verify no regressions in core features
- **Document clearly**: Explain what was removed and why

The goal is a leaner, faster, more maintainable codebase focused on core camera functionality.

# Tasks: Remove Image Segmentation and Face Recognition Pipelines

**Feature Branch**: `002-remove-the-image`  
**Input**: Design documents from `/specs/002-remove-the-image/`  
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story for independent implementation and testing

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story this task belongs to (US1, US2, US3)
- File paths are absolute from repository root

---

## Phase 1: Setup & Verification

**Purpose**: Validate current state and create backup points before removal

- [X] T001 [P] Create feature branch `002-remove-the-image` and verify clean working directory
- [X] T002 [P] Run full test suite and document baseline: `pytest tests/ -v > baseline_tests.txt`
- [X] T003 [P] Measure baseline performance metrics (startup time, FPS, memory, CPU usage)
- [X] T004 Document current dependency list from `pyproject.toml` for reference

**Checkpoint**: ✅ Baseline captured - ready for removal

---

## Phase 2: User Story 1 - View Raw Camera Feed Without Processing (Priority: P1) 🎯 MVP

**Goal**: Remove all processing code and display raw camera feed without annotations

**Independent Test**: Launch application, verify camera feed displays without segmentation masks or face recognition boxes, and confirm no processing UI controls visible

### Removal Tasks for User Story 1

- [X] T005 [US1] Delete entire `src/segmentation/` directory and all its contents
- [X] T006 [US1] Delete entire `src/face_recognition/` directory and all its contents
- [X] T007 [US1] Remove processing imports from `src/ui/app.py` (lines 19-27):
  ```python
  # DELETE these lines:
  from src.face_recognition import (
      EmbeddingsManager,
      FaceRecognitionConfig,
      FaceRecognitionProcessor,
  )
  from src.segmentation import COCO_CLASSES, SegmentationConfig, SegmentationProcessor
  ```
- [X] T008 [US1] Remove processor global variables from `src/ui/app.py` (lines 56-62):
  ```python
  # DELETE:
  seg_processor: Optional[SegmentationProcessor] = None
  face_processor: Optional[FaceRecognitionProcessor] = None
  embeddings_mgr = EmbeddingsManager()
  ```
- [X] T009 [US1] Simplify `current_settings` dict in `src/ui/app.py` to keep only camera settings:
  ```python
  # KEEP only:
  current_settings = {
      "auto_exposure": False,
      "exposure_time_ms": 30.0,
  }
  # DELETE 9 processing keys
  ```
- [X] T010 [US1] Remove `_ensure_processors_initialized()` function from `src/ui/app.py` (lines 78-158)
- [X] T011 [US1] Remove processing logic from `get_single_frame()` in `src/ui/app.py`:
  ```python
  # DELETE lines 215-227 (segmentation and face recognition application)
  # KEEP camera frame capture logic
  ```
- [X] T012 [US1] Remove processing logic from `frame_stream()` in `src/ui/app.py`:
  ```python
  # DELETE:
  # - Lines 307-394: Processor initialization
  # - Lines 431-452: Processing application (segmentation + face recognition)
  # - Lines 405-424: Settings refresh for processing
  # KEEP: Camera frame capture loop and FPS calculation
  ```
- [X] T013 [US1] Simplify debug info output in `frame_stream()` to show only camera metrics:
  ```python
  # Change from "Detection & Recognition Info" to "Camera Info"
  # Remove processing metrics (segmentation/face times)
  # Keep: Camera status, FPS, frame time
  ```
- [X] T014 [US1] Update `pyproject.toml` to remove processing dependencies:
  ```toml
  # REMOVE:
  "opencv-python>=4.8"
  "ultralytics>=8.0"
  "supervision>=0.21"
  "deepface>=0.0.93"
  "tf-keras>=2.16.0"
  # KEEP:
  "gradio>=4.0"
  "numpy>=1.24"
  ```

### Verification for User Story 1

- [X] T015 [US1] Verify no import errors: `python -m src.ui.app` (should not crash)
- [X] T016 [US1] Launch application and verify raw feed displays without annotations
- [X] T017 [US1] Verify FPS improves to 25+ (from baseline ~15)
- [X] T018 [US1] Verify startup time reduces by 20%+ (measure and compare to T003)
- [X] T019 [US1] Verify CPU usage reduces by 30%+ (measure and compare to T003)

**Checkpoint**: ✅ Core processing removed - camera feed displays raw frames at high FPS

---

## Phase 3: User Story 2 - Simplified UI Without Processing Controls (Priority: P2)

**Goal**: Remove all processing-related UI controls and simplify interface to camera controls only

**Independent Test**: Review UI and confirm all segmentation/face recognition controls (checkboxes, sliders, dropdowns, tabs) are removed

### UI Cleanup Tasks for User Story 2

- [ ] T020 [US2] Remove processing enable checkboxes from `src/ui/app.py` (lines 617-629):
  ```python
  # DELETE:
  enable_seg = gr.Checkbox(label="Enable Object Segmentation", ...)
  enable_face_recog = gr.Checkbox(label="Enable Face Recognition", ...)
  ```
- [ ] T021 [US2] Remove Segmentation tab and all its controls from `src/ui/app.py` (lines 632-690):
  ```python
  # DELETE entire tab:
  # - Model Size dropdown
  # - Confidence Threshold slider
  # - Enable Tracking checkbox
  # - Class Selection dropdown + buttons
  # - Model info markdown
  ```
- [ ] T022 [US2] Remove Face Recognition tab and all its controls from `src/ui/app.py` (lines 692-776):
  ```python
  # DELETE entire tab:
  # - Recognition Model dropdown
  # - Face Detector dropdown
  # - Recognition Threshold slider
  # - Face enrollment section (image upload, name, button)
  # - Face database section (dropdown, delete button)
  # - Face tips markdown
  ```
- [ ] T023 [US2] Remove Tabs container from UI layout in `src/ui/app.py`:
  ```python
  # DELETE: with gr.Tabs(): wrapper
  # KEEP: Camera Settings section as direct controls (no tab)
  ```
- [ ] T024 [US2] Update debug display label from "Detection & Recognition Info" to "Camera Info" in `src/ui/app.py`:
  ```python
  # Change label to: "📹 Camera Info"
  # Update lines count from 8 to 4 (less info to display)
  ```
- [ ] T025 [US2] Remove face enrollment handler functions from `src/ui/app.py`:
  ```python
  # DELETE:
  # - enroll_face_handler() (lines 529-570)
  # - delete_face_handler() (lines 572-588)
  ```
- [ ] T026 [US2] Remove event handlers for processing controls from `src/ui/app.py`:
  ```python
  # DELETE event handlers for:
  # - Segmentation checkbox changes
  # - Face recognition checkbox changes
  # - Model/detector dropdown changes
  # - Threshold slider changes
  # - Class selection changes
  # - Face enrollment/deletion buttons (lines 822-833)
  # - Select All / Clear Selection buttons (lines 812-819)
  ```
- [ ] T027 [US2] Simplify `update_settings()` function to handle only camera settings:
  ```python
  # Remove processing keys from settings update
  # Keep only: auto_exposure, exposure_time_ms
  ```
- [ ] T028 [US2] Update `all_controls` list to include only camera controls:
  ```python
  # Remove processing controls from list
  # Keep: auto_exposure_checkbox, exposure_slider
  ```
- [ ] T029 [US2] Simplify Gradio state to camera settings only:
  ```python
  # settings_state = gr.State({
  #     "auto_exposure": False,
  #     "exposure_time_ms": 30.0,
  # })
  ```

### Verification for User Story 2

- [ ] T030 [US2] Launch application and verify no "Segmentation" tab visible
- [ ] T031 [US2] Launch application and verify no "Face Recognition" tab visible
- [ ] T032 [US2] Launch application and verify only camera controls visible (Auto Exposure, Shutter Speed)
- [ ] T033 [US2] Verify Camera Settings section displays without tab wrapper
- [ ] T034 [US2] Verify camera info display shows only camera metrics (no processing info)

**Checkpoint**: UI simplified - only camera controls visible, clean and focused

---

## Phase 4: User Story 3 - Verify Code Cleanup (Priority: P3)

**Goal**: Ensure all processing code and dependencies are removed, tests updated, and codebase is clean

**Independent Test**: Review codebase and confirm `src/segmentation/` and `src/face_recognition/` directories are deleted, no processing imports exist, and dependencies are removed

### Test Update Tasks for User Story 3

- [ ] T035 [P] [US3] Update `tests/contract/test_gradio_ui_contract.py` to remove processing UI tests:
  ```python
  # REMOVE (if they exist):
  # - test_segmentation_controls_exist()
  # - test_face_recognition_controls_exist()
  # - test_model_selection_dropdown()
  # - test_class_filter_controls()
  # - test_face_enrollment_ui()
  
  # ADD/UPDATE:
  # - test_no_processing_controls() - verify processing UI absent
  # - test_camera_feed_display_exists()
  # - test_camera_controls_exist()
  ```
- [ ] T036 [P] [US3] Update `tests/integration/test_scenario_01_success.py` to remove processing expectations:
  ```python
  # REMOVE assertions:
  # - assert "segmentation" in debug_info
  # - assert "face recognition" in debug_info
  # - assert frame has bounding boxes
  
  # UPDATE assertions:
  # - assert frame is not None
  # - assert frame.shape == expected_shape
  # - assert "Camera" in debug_info
  # - assert fps >= 25
  ```
- [ ] T037 [P] [US3] Run contract tests and verify they pass: `pytest tests/contract/ -v`
- [ ] T038 [P] [US3] Run integration tests and verify they pass: `pytest tests/integration/ -v`
- [ ] T039 [P] [US3] Run unit tests and verify they pass: `pytest tests/unit/ -v`
- [ ] T040 [US3] Run full test suite and verify all tests pass: `pytest tests/ -v`

### Code Verification Tasks for User Story 3

- [ ] T041 [P] [US3] Verify `src/segmentation/` directory is deleted: `ls src/segmentation/` (should not exist)
- [ ] T042 [P] [US3] Verify `src/face_recognition/` directory is deleted: `ls src/face_recognition/` (should not exist)
- [ ] T043 [P] [US3] Search for orphaned processing imports in codebase:
  ```bash
  grep -r "from src.segmentation\|from src.face_recognition" src/
  # Should return no results
  ```
- [ ] T044 [P] [US3] Verify processing dependencies removed from `pyproject.toml`:
  ```bash
  grep "ultralytics\|deepface\|supervision\|opencv-python\|tf-keras" pyproject.toml
  # Should return no results in dependencies list
  ```
- [ ] T045 [P] [US3] Count removed files and verify ~15+ files deleted:
  ```bash
  # Compare file count before (from baseline) and after
  # Expect reduction of 15+ Python files
  ```
- [ ] T046 [US3] Run linter and verify no errors: `ruff check src tests`
- [ ] T047 [US3] Reinstall dependencies and verify no processing packages: `pip install -e .`

### Documentation Tasks for User Story 3

- [ ] T048 [P] [US3] Update `README.md` if it references processing features (remove mentions of segmentation/face recognition)
- [ ] T049 [P] [US3] Update `AGENTS.md` to reflect removed technologies (already done by update-agent-context.sh, verify)
- [ ] T050 [US3] Create migration note in `specs/002-remove-the-image/quickstart.md` for users (already exists, verify completeness)

**Checkpoint**: Code cleanup complete - no orphaned code, all tests pass, dependencies clean

---

## Phase 5: Polish & Validation

**Purpose**: Final validation and performance verification

- [ ] T051 [P] Measure final performance metrics (startup, FPS, CPU, memory)
- [ ] T052 [P] Compare performance to baseline (T003) and verify improvements:
  - Startup time: 20%+ faster (SC-005)
  - FPS: 25+ (SC-004)
  - CPU/Memory: 30%+ reduction (SC-003)
- [ ] T053 Run full end-to-end manual test:
  - Launch application
  - Verify raw feed displays immediately
  - Verify no processing controls visible
  - Verify exposure controls work
  - Verify FPS is 25-30
  - Verify clean shutdown
- [ ] T054 [P] Code review: Verify no dead code remains in `src/ui/app.py`
- [ ] T055 [P] Verify application works on clean install (fresh virtual environment)
- [ ] T056 [P] Run coverage report and verify camera modules still covered: `pytest --cov=src --cov-report=term tests/`
- [ ] T057 Document final metrics in `specs/002-remove-the-image/quickstart.md` (Performance section)

**Final Checkpoint**: All success criteria met - ready for review/merge

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup - Core removal of processing code
- **User Story 2 (Phase 3)**: Depends on User Story 1 - UI cleanup after code removal
- **User Story 3 (Phase 4)**: Can start after User Story 1 completes - Test updates and verification
- **Polish (Phase 5)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent - Can start after Setup
  - Removes processing code and directories
  - Makes application functional with raw feed
- **User Story 2 (P2)**: Depends on User Story 1
  - Cleans up UI controls that reference removed code
  - Should not start until processing code is removed
- **User Story 3 (P3)**: Can run in parallel with User Story 2 after User Story 1
  - Updates tests to match new functionality
  - Verifies code cleanup

### Task Dependencies Within Each Story

**User Story 1:**
- T005-T006 (delete directories) can run in parallel
- T007-T014 (edit app.py, update deps) are sequential (same file)
- T015-T019 (verification) run after implementation

**User Story 2:**
- T020-T029 (UI cleanup) are sequential (all edit app.py)
- T030-T034 (verification) run after implementation

**User Story 3:**
- T035-T036 (test updates) can run in parallel (different files)
- T037-T040 (test execution) are sequential
- T041-T047 (code verification) can run in parallel
- T048-T050 (documentation) can run in parallel

### Parallel Opportunities

**Within Setup:**
- All T001-T004 can run in parallel

**Within User Story 1:**
- T005 and T006 (delete different directories) [P]

**Within User Story 3:**
- T035 and T036 (update different test files) [P]
- T041-T045 (verification checks on different aspects) [P]
- T048-T050 (documentation updates) [P]

**Across User Stories (after US1 complete):**
- User Story 2 and User Story 3 can proceed in parallel

---

## Parallel Execution Example

### Setup Phase (All Parallel)
```bash
Task: "Create feature branch and verify clean working directory"
Task: "Run full test suite and document baseline"
Task: "Measure baseline performance metrics"
Task: "Document current dependency list"
```

### User Story 1 - Directory Deletions (Parallel)
```bash
Task: "Delete src/segmentation/ directory"
Task: "Delete src/face_recognition/ directory"
```

### User Story 3 - Test Updates (Parallel)
```bash
Task: "Update tests/contract/test_gradio_ui_contract.py"
Task: "Update tests/integration/test_scenario_01_success.py"
```

### User Story 3 - Code Verification (Parallel)
```bash
Task: "Verify src/segmentation/ deleted"
Task: "Verify src/face_recognition/ deleted"
Task: "Search for orphaned imports"
Task: "Verify dependencies removed"
Task: "Count removed files"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (capture baseline)
2. Complete Phase 2: User Story 1 (remove processing code)
3. **STOP and VALIDATE**: Test raw camera feed works
4. Measure performance improvements
5. If satisfactory, can deploy/demo minimal version

### Incremental Delivery

1. Complete Setup → Baseline captured
2. Complete User Story 1 → Test independently → Raw feed works (MVP!)
3. Complete User Story 2 → Test independently → Clean UI
4. Complete User Story 3 → Test independently → All tests pass, code clean
5. Complete Polish → Final validation → Ready for merge

### Parallel Team Strategy

With multiple developers after User Story 1:

1. Team completes Setup together
2. Team completes User Story 1 together (foundational removal)
3. Once US1 done:
   - Developer A: User Story 2 (UI cleanup)
   - Developer B: User Story 3 (tests and verification)
4. Both converge for Polish phase

---

## Success Criteria Tracking

**From spec.md - verify each after completion:**

- [ ] **SC-001**: Users can view camera feed without segmentation masks or face recognition boxes
  - Verify: T016, T053
- [ ] **SC-002**: UI loads without segmentation/face recognition controls visible
  - Verify: T030-T034
- [ ] **SC-003**: System resource usage decreases by 30%+
  - Verify: T019, T051, T052
- [ ] **SC-004**: Camera feed maintains 25+ FPS
  - Verify: T017, T051, T052
- [ ] **SC-005**: Application startup time reduced by 20%+
  - Verify: T018, T051, T052
- [ ] **SC-006**: Codebase reduced by 15+ source files
  - Verify: T045
- [ ] **SC-007**: All existing tests pass after removal
  - Verify: T040
- [ ] **SC-008**: Application supports all core camera operations
  - Verify: T053

---

## Notes

- This is a **removal/simplification** feature - focus on clean deletion, not adding features
- **Tests already exist** - update existing tests rather than write new ones
- Each user story delivers independent value:
  - **US1**: Raw feed works (functional but UI has orphaned controls)
  - **US2**: Clean UI (professional appearance)
  - **US3**: Code quality (maintainable codebase)
- Most work is in `src/ui/app.py` (T007-T029) - sequential edits to same file
- Parallel work possible in Setup, directory deletion, test updates, and verification
- Commit after each phase for easy rollback
- Performance improvements should be dramatic (60-70% in most metrics)
- Total tasks: 57 tasks across 5 phases

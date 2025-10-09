# Tasks: Camera Feed Display Interface

**Feature**: `001-using-gradio-as`
**Branch**: `001-using-gradio-as`
**Input**: Design documents from `/specs/001-using-gradio-as/`

## Execution Flow (completed)
```
1. Loaded plan.md � Python 3.13, Gradio, MVSDK, pytest
2. Loaded design documents:
    research.md: 8 technical decisions
    data-model.md: 4 entities (CameraDevice, VideoFrame, ViewerSession, StreamState)
    contracts/: 4 protocol files (camera_device, video_frame, viewer_session, gradio_ui)
    quickstart.md: 5 validation scenarios
3. Generated tasks:
   � Setup: 3 tasks (T001-T003)
   � Contract tests: 4 tasks [P] (T004-T007)
   � Entity implementations: 4 tasks [P] (T008-T011)
   � Service layer: 5 tasks (T012-T016)
   � UI layer: 3 tasks (T017-T019)
   � Integration tests: 5 tasks [P] (T020-T024)
   � Validation: 3 tasks (T025-T027)
4. Total: 27 tasks, 13 parallel-safe [P]
```

## Task Format
- **[P]**: Parallel-safe (different files, no dependencies)
- File paths are absolute from repository root
- Dependencies noted in task descriptions

---

## Phase 3.1: Setup (T001-T003)

### T001 [x]: Create project structure
**Files**: All directories in `src/` and `tests/`
**Dependencies**: None

Create directory structure per plan.md:
```bash
mkdir -p src/camera src/ui src/lib
mkdir -p tests/contract tests/integration tests/unit tests/fixtures
touch src/__init__.py src/camera/__init__.py src/ui/__init__.py src/lib/__init__.py
touch tests/__init__.py
```

**Validation**: Directory structure matches plan.md Section "Project Structure"

---

### T002 [x]: Initialize Python project with dependencies
**Files**: `pyproject.toml`, `README.md`
**Dependencies**: T001 (directories must exist)

Update `pyproject.toml`:
```toml
[project]
name = "high-speed-camera-testing"
version = "0.1.0"
description = "Camera feed display using Gradio and MVSDK"
requires-python = ">=3.12"
dependencies = [
    "gradio>=4.0",
    "numpy>=1.24",
    "opencv-python>=4.8",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-mock>=3.12",
    "pytest-cov>=4.1",
    "ruff>=0.1",
]
```

Copy MVSDK library:
```bash
cp spec/python_demo/mvsdk.py src/lib/mvsdk.py
```

Create basic README.md with:
- Project description
- Installation instructions
- Quick start command
- Links to spec/ for SDK documentation

**Validation**: `pip install -e .[dev]` succeeds, mvsdk.py importable

---

### T003 [x]: Configure linting and formatting
**Files**: `ruff.toml`, `.gitignore`
**Dependencies**: T002 (pyproject.toml must exist)

Create `ruff.toml`:
```toml
line-length = 100
target-version = "py312"

[lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]  # Line too long (handled by formatter)

[format]
quote-style = "double"
```

Create `.gitignore`:
```
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
*.egg-info/
.venv/
venv/
```

**Validation**: `ruff check src/ tests/` runs without errors on empty files

---

## Phase 3.2: Tests First (TDD) � MUST COMPLETE BEFORE 3.3

### T004 [P] [x]: Write CameraDevice contract tests
**Files**: `tests/contract/test_camera_device_contract.py`
**Dependencies**: T001-T003 (setup complete)
**Reference**: `specs/001-using-gradio-as/contracts/camera_device.py`

Implement all contract tests from camera_device.py:
- `test_enumerate_returns_list()` - Returns list not None
- `test_enumerate_no_cameras()` - Returns [] when no cameras (use mock)
- `test_camera_lifecycle()` - enumerate � init � enter � capture � exit
- `test_camera_cleanup_on_error()` - `__exit__()` called on error
- `test_single_access_enforcement()` - Second `__enter__()` raises CameraAccessDenied
- `test_capability_requires_init()` - get_capability() before `__enter__()` raises RuntimeError
- `test_capture_requires_init()` - capture_frames() before `__enter__()` raises RuntimeError
- `test_frame_format_color()` - Color camera yields (H, W, 3) arrays
- `test_frame_format_mono()` - Mono camera yields (H, W) arrays
- `test_native_resolution()` - Frames match CameraCapability max_width/max_height

Use pytest-mock to mock `src.lib.mvsdk` module.

**Validation**: `pytest tests/contract/test_camera_device_contract.py` - all tests FAIL (no implementation yet)

---

### T005 [P] [x]: Write VideoFrame contract tests
**Files**: `tests/contract/test_video_frame_contract.py`
**Dependencies**: T001-T003 (setup complete)
**Reference**: `specs/001-using-gradio-as/contracts/video_frame.py`

Implement all contract tests from video_frame.py:
- `test_frame_immutable()` - VideoFrame is frozen
- `test_frame_color_shape()` - Color frame has shape (H, W, 3)
- `test_frame_mono_shape()` - Mono frame has shape (H, W)
- `test_frame_dtype()` - Frame data is uint8
- `test_frame_validates_shape_mismatch()` - ValueError if shape mismatch
- `test_frame_validates_channels()` - ValueError if channels not in [1, 3]
- `test_frame_validates_dimensions()` - ValueError if width/height <= 0
- `test_frame_validates_timestamp()` - ValueError if timestamp <= 0
- `test_frame_validates_sequence()` - ValueError if sequence_number < 0
- `test_is_color_property()` - is_color == True iff channels == 3
- `test_size_bytes_property()` - size_bytes == data.nbytes
- `test_to_gradio_format_color()` - Color frames return BGR (H�W�3)
- `test_to_gradio_format_mono()` - Mono frames return grayscale (H�W)
- `test_to_gradio_format_no_copy()` - Returns view when possible

Use numpy fixtures for test frame data.

**Validation**: `pytest tests/contract/test_video_frame_contract.py` - all tests FAIL (no implementation yet)

---

### T006 [P] [x]: Write ViewerSession contract tests
**Files**: `tests/contract/test_viewer_session_contract.py`
**Dependencies**: T001-T003 (setup complete)
**Reference**: `specs/001-using-gradio-as/contracts/viewer_session.py`

Implement all contract tests from viewer_session.py:
- `test_single_session_only()` - try_start_session() returns False if session active
- `test_session_idempotent_start()` - Same session_hash can retry
- `test_session_end_releases()` - end_session() allows new sessions
- `test_session_end_idempotent()` - Ending non-existent session is no-op
- `test_active_session_info()` - get_active_session() returns current session
- `test_no_active_session()` - get_active_session() returns None when no session
- `test_is_session_active_true()` - Returns True for active session
- `test_is_session_active_false()` - Returns False for unknown session
- `test_streaming_requires_session()` - start_streaming() raises ValueError if no session
- `test_streaming_state_toggle()` - is_streaming() matches start/stop calls
- `test_frame_count_increments()` - increment_frame_count() returns monotonic values
- `test_error_count_threshold()` - increment_error_count() triggers recovery at 10
- `test_error_count_reset()` - reset_error_count() clears consecutive errors
- `test_thread_safety_concurrent_sessions()` - Concurrent try_start_session() only allows one
- `test_thread_safety_frame_count()` - Concurrent increment_frame_count() is correct

Use threading fixtures to test concurrency.

**Validation**: `pytest tests/contract/test_viewer_session_contract.py` - all tests FAIL (no implementation yet)

---

### T007 [P] [x]: Write Gradio UI contract tests
**Files**: `tests/contract/test_gradio_ui_contract.py`
**Dependencies**: T001-T003 (setup complete)
**Reference**: `specs/001-using-gradio-as/contracts/gradio_ui.py`

Implement all contract tests from gradio_ui.py:
- `test_launch_enforces_localhost()` - launch() raises ValueError if server_name != '127.0.0.1'
- `test_launch_enforces_no_sharing()` - launch() raises ValueError if share == True
- `test_interface_loads_automatically()` - Stream starts on load (FR-003)
- `test_interface_continuous_update()` - Frames update without refresh (FR-006)
- `test_session_start_callback()` - on_session_start called when user connects
- `test_session_end_callback()` - on_session_end called when browser closes
- `test_error_display_no_camera()` - Friendly message for no camera
- `test_error_display_in_use()` - Single viewer message for camera in use

Use pytest-mock to mock Gradio components.

**Validation**: `pytest tests/contract/test_gradio_ui_contract.py` - all tests FAIL (no implementation yet)

---

## Phase 3.3: Core Implementation

### T008 [P] [x]: Implement VideoFrame entity
**Files**: `src/camera/video_frame.py`
**Dependencies**: T005 (contract tests written)
**Reference**: `specs/001-using-gradio-as/data-model.md` section "VideoFrame"

Implement VideoFrame dataclass from contract:
```python
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class VideoFrame:
    data: np.ndarray
    width: int
    height: int
    channels: int
    timestamp: float
    sequence_number: int
    media_type: int

    def __post_init__(self):
        # Implement all validations from contract
        ...

    @property
    def is_color(self) -> bool:
        ...

    @property
    def size_bytes(self) -> int:
        ...

    def to_gradio_format(self) -> np.ndarray:
        ...
```

**Validation**: `pytest tests/contract/test_video_frame_contract.py` - all tests PASS

---

### T009 [P] [x]: Implement CameraDevice wrapper
**Files**: `src/camera/device.py`
**Dependencies**: T004 (contract tests written), T008 (VideoFrame exists)
**Reference**: `specs/001-using-gradio-as/contracts/camera_device.py`, `specs/001-using-gradio-as/research.md` section "Camera SDK Integration"

Implement CameraDevice class:
```python
from typing import Iterator
import numpy as np
from src.lib import mvsdk
from src.camera.video_frame import VideoFrame

class CameraDevice:
    @staticmethod
    def enumerate_cameras() -> list[CameraInfo]:
        # Wrap mvsdk.CameraEnumerateDevice()
        ...

    def __init__(self, camera_info: CameraInfo):
        ...

    def get_capability(self) -> CameraCapability:
        # Call mvsdk.CameraGetCapability()
        ...

    def __enter__(self) -> 'CameraDevice':
        # Initialize camera per research.md pattern
        # Steps: CameraInit, CameraGetCapability, CameraSetIspOutFormat,
        #        CameraSetTriggerMode(0), CameraPlay
        ...

    def capture_frames(self) -> Iterator[np.ndarray]:
        # Yield frames using CameraGetImageBuffer + CameraImageProcess
        # Convert to numpy array per research.md
        ...

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup: CameraUnInit, CameraAlignFree
        ...

class CameraException(Exception):
    ...

class CameraAccessDenied(CameraException):
    ...
```

Handle mono vs color cameras per research.md decision #6.

**Validation**: `pytest tests/contract/test_camera_device_contract.py` - all tests PASS (with mocked mvsdk)

---

### T010 [P] [x]: Implement ViewerSession manager
**Files**: `src/ui/session.py`
**Dependencies**: T006 (contract tests written)
**Reference**: `specs/001-using-gradio-as/contracts/viewer_session.py`, `specs/001-using-gradio-as/data-model.md` section "ViewerSession"

Implement ViewerSession and StreamState:
```python
from typing import Optional
from datetime import datetime
import threading

class ViewerSessionManager:
    def __init__(self):
        self._active_session: Optional[SessionInfo] = None
        self._lock = threading.Lock()

    def try_start_session(self, session_hash: str) -> bool:
        # Implement single-session enforcement
        ...

    def end_session(self, session_hash: str) -> None:
        # Release session and camera
        ...

    def get_active_session(self) -> Optional[SessionInfo]:
        ...

    def is_session_active(self, session_hash: str) -> bool:
        ...

class StreamState:
    def __init__(self):
        self._is_streaming = False
        self._frame_count = 0
        self._error_count = 0
        self._lock = threading.Lock()

    def start_streaming(self, session_id: str) -> None:
        ...

    def stop_streaming(self, session_id: str) -> None:
        ...

    def increment_frame_count(self) -> int:
        ...

    def increment_error_count(self) -> int:
        # Trigger recovery if > 10 consecutive errors
        ...

    def reset_error_count(self) -> None:
        ...
```

**Validation**: `pytest tests/contract/test_viewer_session_contract.py` - all tests PASS

---

### T011 [P] [x]: Create test fixtures for mock camera
**Files**: `tests/fixtures/camera_fixtures.py`
**Dependencies**: T008 (VideoFrame exists)
**Reference**: `specs/001-using-gradio-as/data-model.md`

Create pytest fixtures for testing:
```python
import pytest
import numpy as np
from src.camera.video_frame import VideoFrame

@pytest.fixture
def mock_camera_info():
    # Mock CameraInfo for enumerate
    ...

@pytest.fixture
def mock_mono_frame():
    # Generate (480, 640) grayscale test frame
    ...

@pytest.fixture
def mock_color_frame():
    # Generate (480, 640, 3) BGR test frame
    ...

@pytest.fixture
def mock_mvsdk(mocker):
    # Mock entire mvsdk module with reasonable defaults
    ...
```

**Validation**: Import fixtures in contract tests, verify they work

---

### T012 [x]: Implement frame capture service
**Files**: `src/camera/capture.py`
**Dependencies**: T009 (CameraDevice exists), T011 (fixtures exist)
**Reference**: `specs/001-using-gradio-as/research.md` section "Performance Optimization"

Implement frame capture loop with error handling:
```python
from typing import Iterator, Optional
import logging
import numpy as np
from src.camera.device import CameraDevice, CameraException
from src.lib import mvsdk

logger = logging.getLogger(__name__)

def create_frame_generator(camera: CameraDevice) -> Iterator[np.ndarray]:
    """
    Generator that yields frames from camera with error handling.

    Implements zero-copy path per research.md section 4.
    Handles timeouts gracefully (skip frame, don't raise).
    """
    sequence = 0
    while True:
        try:
            frame = next(camera.capture_frames())
            sequence += 1
            yield frame
        except StopIteration:
            break
        except CameraException as e:
            if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
                # Normal timeout, skip frame
                continue
            else:
                logger.error(f"Camera error: {e}")
                raise
```

**Validation**: Unit test with mock camera, verify error handling

---

### T013 [x]: Implement error message mapper
**Files**: `src/camera/errors.py`
**Dependencies**: None (standalone utility)
**Reference**: `specs/001-using-gradio-as/research.md` section "Error Handling"

Map MVSDK error codes to user-friendly messages:
```python
from src.lib import mvsdk

ERROR_MESSAGES = {
    mvsdk.CAMERA_STATUS_NO_DEVICE_FOUND: "No camera detected. Please connect a camera and restart.",
    mvsdk.CAMERA_STATUS_DEVICE_LOST: "Camera connection lost. Please check cable and reconnect.",
    mvsdk.CAMERA_STATUS_ACCESS_DENY: "Camera already in use. Only one viewer allowed.",
    mvsdk.CAMERA_STATUS_TIME_OUT: "Camera not responding. Please restart the application.",
    # Add more mappings per research.md section 4
}

def get_user_message(error_code: int, default: str = "Camera error occurred") -> str:
    """Convert MVSDK error code to user-friendly message."""
    return ERROR_MESSAGES.get(error_code, default)
```

**Validation**: Unit tests for known error codes

---

### T014 [x]: Implement session lifecycle hooks
**Files**: `src/ui/lifecycle.py`
**Dependencies**: T010 (ViewerSessionManager exists)
**Reference**: `specs/001-using-gradio-as/research.md` section "Single-Session Concurrency Control"

Create session event handlers for Gradio:
```python
from typing import Callable, Optional
import logging
from src.ui.session import ViewerSessionManager
from src.camera.device import CameraDevice

logger = logging.getLogger(__name__)

class SessionLifecycle:
    def __init__(self, session_manager: ViewerSessionManager):
        self.session_manager = session_manager
        self.camera: Optional[CameraDevice] = None

    def on_session_start(self, session_hash: str) -> Optional[str]:
        """
        Handle user connecting. Returns error message if blocked.
        """
        if not self.session_manager.try_start_session(session_hash):
            return "Camera already in use. Only one viewer allowed."

        # Initialize camera here
        logger.info(f"Session started: {session_hash}")
        return None

    def on_session_end(self, session_hash: str) -> None:
        """
        Handle user disconnecting. Cleanup camera resources.
        """
        if self.camera:
            self.camera.__exit__(None, None, None)
            self.camera = None

        self.session_manager.end_session(session_hash)
        logger.info(f"Session ended: {session_hash}")
```

**Validation**: Unit tests with mock session manager and camera

---

### T015 [x]: Implement camera initialization logic
**Files**: `src/camera/init.py`
**Dependencies**: T009 (CameraDevice exists), T013 (error mapper exists)
**Reference**: `specs/001-using-gradio-as/research.md` section "Camera SDK Integration"

Implement camera discovery and initialization:
```python
from typing import Optional
import logging
from src.camera.device import CameraDevice, CameraInfo, CameraException
from src.camera.errors import get_user_message

logger = logging.getLogger(__name__)

def initialize_camera() -> tuple[Optional[CameraDevice], Optional[str]]:
    """
    Enumerate and initialize first available camera.

    Returns:
        (CameraDevice, None) on success
        (None, error_message) on failure
    """
    try:
        cameras = CameraDevice.enumerate_cameras()

        if not cameras:
            return None, "No camera detected. Please connect a camera."

        # Use first camera
        camera_info = cameras[0]
        logger.info(f"Found camera: {camera_info.friendly_name}")

        camera = CameraDevice(camera_info)
        camera.__enter__()  # Initialize

        cap = camera.get_capability()
        logger.info(f"Camera: {cap.max_width}�{cap.max_height}, "
                   f"{'mono' if cap.is_mono else 'color'}")

        return camera, None

    except CameraException as e:
        msg = get_user_message(e.error_code)
        logger.error(f"Camera init failed: {msg}")
        return None, msg
```

**Validation**: Unit test with mock cameras (success and failure cases)

---

### T016 [x]: Write unit tests for camera services
**Files**: `tests/unit/test_capture.py`, `tests/unit/test_errors.py`, `tests/unit/test_init.py`
**Dependencies**: T012-T015 (services exist), T011 (fixtures exist)

Write unit tests for:
- `test_capture.py`: Frame generator error handling, timeout handling, sequence numbers
- `test_errors.py`: Error message mapping for all known codes
- `test_init.py`: Camera enumeration, initialization success/failure paths

Use mock_mvsdk fixture from T011.

**Validation**: `pytest tests/unit/` - all tests PASS, coverage >80%

---

## Phase 3.4: UI Layer

### T017 [x]: Implement Gradio app interface
**Files**: `src/ui/app.py`
**Dependencies**: T007 (UI contract tests), T012 (frame generator), T014 (lifecycle hooks)
**Reference**: `specs/001-using-gradio-as/contracts/gradio_ui.py`, `specs/001-using-gradio-as/research.md` section "Gradio Real-Time Streaming Patterns"

Implement Gradio application:
```python
import gradio as gr
from typing import Iterator
import numpy as np
from src.camera.capture import create_frame_generator
from src.ui.lifecycle import SessionLifecycle
from src.ui.session import ViewerSessionManager

def create_camera_app() -> gr.Blocks:
    """
    Create Gradio app for camera streaming.

    Implements pattern from research.md section 1:
    - gr.Image with generator-based streaming
    - Session start/end callbacks
    - Error display
    """
    session_manager = ViewerSessionManager()
    lifecycle = SessionLifecycle(session_manager)

    def frame_stream(session_hash: str):
        # Check session, initialize camera, yield frames
        error = lifecycle.on_session_start(session_hash)
        if error:
            yield gr.Error(error)
            return

        if lifecycle.camera:
            for frame in create_frame_generator(lifecycle.camera):
                yield frame

    with gr.Blocks() as app:
        gr.Markdown("# Camera Feed")

        image = gr.Image(
            label="Live Camera Feed",
            streaming=True,
            every=0.033  # ~30fps update rate
        )

        # Bind session events
        app.load(
            fn=lambda req: frame_stream(req.session_hash),
            inputs=[],
            outputs=[image]
        )

        app.unload(
            fn=lambda req: lifecycle.on_session_end(req.session_hash),
            inputs=[],
            outputs=[]
        )

    return app

def launch_app(app: gr.Blocks) -> None:
    """
    Launch Gradio server with localhost-only access.

    Contract enforcement from gradio_ui.py:
    - server_name must be "127.0.0.1"
    - share must be False
    """
    if server_name := "127.0.0.1":  # Contract enforcement
        app.launch(
            server_name=server_name,
            server_port=7860,
            share=False,
            inbrowser=True
        )
    else:
        raise ValueError(f"Server must be localhost only")
```

**Validation**: `pytest tests/contract/test_gradio_ui_contract.py` - tests PASS

---

### T018 [x]: Implement error display component
**Files**: `src/ui/errors.py`
**Dependencies**: T017 (Gradio app exists)
**Reference**: `specs/001-using-gradio-as/contracts/gradio_ui.py`

Create error display utilities:
```python
import gradio as gr

def display_error(message: str, error_type: str = "error") -> gr.Error:
    """
    Display user-friendly error in Gradio UI.

    Args:
        message: Error message (user-friendly, no stack traces)
        error_type: "error", "warning", or "info"

    Returns:
        Gradio Error component
    """
    return gr.Error(message)

def display_info(message: str) -> gr.Info:
    """Display informational message."""
    return gr.Info(message)
```

**Validation**: Unit test that creates Error/Info components

---

### T019 [x]: Create main application entry point
**Files**: `main.py` (repository root)
**Dependencies**: T017 (Gradio app exists), T015 (camera init exists)
**Reference**: `specs/001-using-gradio-as/quickstart.md`

Create main.py:
```python
#!/usr/bin/env python3
"""
Camera Feed Display Application

Usage:
    python main.py              # Start on default port 7860
    python main.py --port 8080  # Start on custom port
"""
import argparse
import logging
from src.ui.app import create_camera_app, launch_app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description='Camera Feed Display')
    parser.add_argument('--port', type=int, default=7860, help='Server port')
    args = parser.parse_args()

    app = create_camera_app()
    launch_app(app)

if __name__ == "__main__":
    main()
```

Make executable:
```bash
chmod +x main.py
```

**Validation**: `python main.py --help` shows usage, app launches without camera

---

## Phase 3.5: Integration Tests (Quickstart Scenarios)

### T020 [P] [x]: Integration test - Successful camera feed
**Files**: `tests/integration/test_scenario_01_success.py`
**Dependencies**: T008-T019 (all core implementation complete)
**Reference**: `specs/001-using-gradio-as/quickstart.md` Scenario 1

Implement integration test for successful camera feed display:
```python
import pytest
from src.camera.device import CameraDevice
from src.camera.capture import create_frame_generator

def test_camera_feed_displays(mock_mvsdk):
    """
    Scenario 1: Given camera connected, when presenter accesses interface,
    then live feed displays immediately.
    """
    # Setup: Mock camera available
    cameras = CameraDevice.enumerate_cameras()
    assert len(cameras) > 0

    # Action: Initialize and capture
    with CameraDevice(cameras[0]) as camera:
        cap = camera.get_capability()
        assert cap.max_width > 0
        assert cap.max_height > 0

        # Verify: Can capture frames
        gen = create_frame_generator(camera)
        frame1 = next(gen)
        assert frame1 is not None
        assert frame1.shape[0] == cap.max_height
        assert frame1.shape[1] == cap.max_width
```

**Validation**: `pytest tests/integration/test_scenario_01_success.py` PASS

---

### T021 [P] [x]: Integration test - Single viewer restriction
**Files**: `tests/integration/test_scenario_02_single_viewer.py`
**Dependencies**: T008-T019 (all core implementation complete)
**Reference**: `specs/001-using-gradio-as/quickstart.md` Scenario 2

Test single viewer enforcement:
```python
from src.ui.session import ViewerSessionManager

def test_second_viewer_blocked():
    """
    Scenario 2: Given first viewer active, when second viewer connects,
    then second viewer sees "camera in use" message.
    """
    manager = ViewerSessionManager()

    # First viewer
    assert manager.try_start_session("session-1") == True

    # Second viewer blocked
    assert manager.try_start_session("session-2") == False

    # After first ends, second can connect
    manager.end_session("session-1")
    assert manager.try_start_session("session-2") == True
```

**Validation**: `pytest tests/integration/test_scenario_02_single_viewer.py` PASS

---

### T022 [P] [x]: Integration test - No camera error handling
**Files**: `tests/integration/test_scenario_03_no_camera.py`
**Dependencies**: T008-T019 (all core implementation complete)
**Reference**: `specs/001-using-gradio-as/quickstart.md` Scenario 3

Test error handling when no camera:
```python
from src.camera.init import initialize_camera

def test_no_camera_shows_error(mock_mvsdk_no_camera):
    """
    Scenario 3: Given no camera connected, when user accesses interface,
    then clear error message displays.
    """
    camera, error = initialize_camera()

    assert camera is None
    assert error is not None
    assert "No camera detected" in error
    assert "Please connect a camera" in error
```

**Validation**: `pytest tests/integration/test_scenario_03_no_camera.py` PASS

---

### T023 [P] [x]: Integration test - Resource cleanup
**Files**: `tests/integration/test_scenario_04_cleanup.py`
**Dependencies**: T008-T019 (all core implementation complete)
**Reference**: `specs/001-using-gradio-as/quickstart.md` Scenario 4

Test camera resource cleanup:
```python
def test_camera_cleanup_on_disconnect(mock_mvsdk):
    """
    Scenario 4: Given streaming active, when browser closes,
    then camera resources released.
    """
    cameras = CameraDevice.enumerate_cameras()
    camera = CameraDevice(cameras[0])

    # Start camera
    camera.__enter__()
    assert camera._handle is not None  # Camera active

    # Cleanup
    camera.__exit__(None, None, None)

    # Verify: Can enumerate cameras again (not locked)
    cameras_after = CameraDevice.enumerate_cameras()
    assert len(cameras_after) > 0
```

**Validation**: `pytest tests/integration/test_scenario_04_cleanup.py` PASS

---

### T024 [P] [x]: Integration test - Localhost-only access
**Files**: `tests/integration/test_scenario_05_localhost.py`
**Dependencies**: T017 (Gradio app exists)
**Reference**: `specs/001-using-gradio-as/quickstart.md` Scenario 5

Test localhost-only server configuration:
```python
import pytest
from src.ui.app import launch_app

def test_localhost_enforcement():
    """
    Scenario 5: Server only accepts connections from 127.0.0.1.
    """
    # Test that external server_name raises error
    with pytest.raises(ValueError, match="localhost only"):
        launch_app(None, server_name="0.0.0.0")

    # Test that share=True raises error
    with pytest.raises(ValueError, match="sharing.*not allowed"):
        launch_app(None, share=True)
```

**Validation**: `pytest tests/integration/test_scenario_05_localhost.py` PASS

---

## Phase 3.6: Validation & Polish

### T025 [x]: Run full test suite and measure coverage
**Files**: N/A (run tests)
**Dependencies**: T020-T024 (all integration tests complete)
**Reference**: `specs/001-using-gradio-as/quickstart.md` "Next Steps"

Run complete test suite:
```bash
# All tests
pytest tests/ -v

# With coverage
pytest --cov=src --cov-report=html --cov-report=term tests/

# Coverage targets:
# - Contract tests: 100% (required by TDD)
# - Core modules: >80%
# - Integration: >70%
```

Review coverage report:
```bash
open htmlcov/index.html
```

Fix any gaps in coverage by adding unit tests.

**Validation**:
- All tests PASS
- Overall coverage >75%
- No critical uncovered branches

---

### T026: Execute quickstart validation manually
**Files**: N/A (manual testing with real camera)
**Dependencies**: T019 (main.py exists), T025 (tests pass)
**Reference**: `specs/001-using-gradio-as/quickstart.md` all scenarios

Perform manual testing with physical camera:

1. **Install and run**:
   ```bash
   pip install -e .[dev]
   python main.py
   ```

2. **Validate each scenario**:
   -  Camera feed displays automatically (Scenario 1)
   -  Second browser tab shows "in use" message (Scenario 2)
   -  Disconnect camera, restart � "No camera" error (Scenario 3)
   -  Close tab, run `spec/python_demo/cv_grab.py` � works (Scenario 4)
   -  Cannot access from http://192.168.x.x:7860 (Scenario 5)

3. **Performance checks**:
   - Frame rate: Check logs show target FPS
   - Latency: Wave hand, observe <100ms delay
   - Resolution: Verify native camera resolution displayed

Document any issues in `specs/001-using-gradio-as/validation-results.md`.

**Validation**: All quickstart scenarios PASS with real camera

---

### T027 [x]: Update documentation
**Files**: `README.md`, `specs/001-using-gradio-as/validation-results.md`
**Dependencies**: T026 (validation complete)

Update README.md with:
- Full installation instructions
- Hardware requirements (camera, platform)
- Usage examples
- Troubleshooting section from quickstart.md
- Link to specs/ documentation

Create validation-results.md:
```markdown
# Validation Results: 001-using-gradio-as

Date: [DATE]
Camera: [Camera model used]
Platform: macOS [version]

## Scenario Results
- [x] Scenario 1: Camera feed displays - PASS
- [x] Scenario 2: Single viewer restriction - PASS
- [x] Scenario 3: No camera error - PASS
- [x] Scenario 4: Resource cleanup - PASS
- [x] Scenario 5: Localhost-only - PASS

## Performance Metrics
- Frame rate: [measured FPS]
- Latency: [measured ms]
- Resolution: [WxH]

## Issues Found
[None or list issues]

## Sign-off
All functional requirements (FR-001 to FR-012) validated.
Ready for production use.
```

**Validation**: Documentation is complete and accurate

---

## Dependency Graph

```
Setup Phase (Sequential):
T001 � T002 � T003

Contract Tests (Parallel after setup):
[T004, T005, T006, T007] (all depend on T001-T003)

Core Implementation (Parallel after contract tests):
T008 (depends on T005)
T009 (depends on T004, T008)
T010 (depends on T006)
T011 (depends on T008)

Services (Sequential, depend on core):
T012 � depends on T009, T011
T013 � standalone
T014 � depends on T010
T015 � depends on T009, T013
T016 � depends on T012-T015

UI Layer (Sequential, depends on services):
T017 � depends on T012, T014
T018 � depends on T017
T019 � depends on T017, T015

Integration Tests (Parallel after UI):
[T020, T021, T022, T023, T024] (all depend on T008-T019)

Validation (Sequential, depends on integration):
T025 � depends on T020-T024
T026 � depends on T025
T027 � depends on T026
```

## Parallel Execution Examples

**After Setup (T001-T003)**:
```bash
# Run all contract tests in parallel
pytest tests/contract/ -n 4  # pytest-xdist for parallel execution
```

**After Contract Tests Pass**:
```bash
# Implement entities in parallel (different files)
# Terminal 1:
# Work on T008 (video_frame.py)

# Terminal 2:
# Work on T009 (device.py)

# Terminal 3:
# Work on T010 (session.py)

# Terminal 4:
# Work on T011 (fixtures)
```

**After UI Complete**:
```bash
# Run integration tests in parallel
pytest tests/integration/ -n 5
```

## Progress Tracking

- [x] **Phase 3.1 Setup**: T001-T003 (3 tasks) ✓ COMPLETE
- [x] **Phase 3.2 Tests**: T004-T007 (4 tasks, all [P]) ✓ COMPLETE
- [x] **Phase 3.3 Core**: T008-T016 (9 tasks, 4 [P])
- [x] **Phase 3.4 UI**: T017-T019 (3 tasks)
- [x] **Phase 3.5 Integration**: T020-T024 (5 tasks, all [P])
- [x] **Phase 3.6 Validation**: T025-T027 (3 tasks)

**Total**: 27 tasks, 13 parallel-safe [P]

---

## Execution Status

**Ready for implementation**: All tasks defined with:
- Clear file paths
- Specific dependencies
- Validation criteria
- Code examples where needed

**Next Step**: Begin with `T001` (create project structure)

---

*Generated from design artifacts in `/specs/001-using-gradio-as/`*
*Based on TDD principles from constitution*

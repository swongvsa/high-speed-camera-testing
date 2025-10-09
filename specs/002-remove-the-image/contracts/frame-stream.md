# Frame Stream Contract: Simplified Camera Streaming

**Feature**: Remove processing pipelines  
**Date**: 2025-10-09  
**Contract Type**: Frame Streaming Interface

## Overview

This contract defines the simplified frame streaming interface after removing image segmentation and face recognition processing. The frame stream now delivers raw camera frames directly to the UI without any processing stages.

---

## Function Signature

### Before Removal

```python
def frame_stream(
    request: gr.Request,
    enable_segmentation: bool = False,
    model_size: str = "n",
    confidence: float = 0.25,
    enable_tracking: bool = False,
    selected_classes: Optional[list] = None,
    enable_face_recognition: bool = False,
    face_model: str = "Facenet512",
    face_detector: str = "retinaface",
    face_threshold: float = 0.6,
) -> Iterator[tuple[np.ndarray, str]]:
```

### After Removal

```python
def frame_stream(
    request: gr.Request,
) -> Iterator[tuple[np.ndarray, str]]:
    """
    Generator function for streaming raw camera frames to Gradio.
    
    Args:
        request: Gradio request with session_hash for session management
    
    Yields:
        tuple: (frame, camera_info)
            - frame: np.ndarray - Raw camera frame (H×W×3, RGB, uint8)
            - camera_info: str - Camera status and performance metrics
    
    Contract:
        - FR-003: Auto-start on page load
        - FR-006: Continuous frame updates
        - FR-006a: Block if camera already in use
        - FR-012: Single viewer session enforcement
    """
```

**Changes**:
- ❌ Removed 9 processing-related parameters
- ✅ Kept only `request` for session management
- ✅ Output format unchanged (frame + info string)

---

## Input Contract

### Required Input

**Parameter**: `request: gr.Request`

**Purpose**: Gradio request object containing session hash

**Contract**:
- ✅ MUST contain `session_hash` for session management
- ✅ MUST be provided by Gradio framework (not user-controlled)
- ✅ Used to enforce single viewer constraint

**Usage**:
```python
session_hash = request.session_hash or "unknown"
error = lifecycle.on_session_start(session_hash)
if error:
    gr.Warning(error)
    return  # Block if camera in use
```

### Removed Inputs

The following parameters **MUST NOT** be accepted:

❌ `enable_segmentation: bool`  
❌ `model_size: str`  
❌ `confidence: float`  
❌ `enable_tracking: bool`  
❌ `selected_classes: Optional[list]`  
❌ `enable_face_recognition: bool`  
❌ `face_model: str`  
❌ `face_detector: str`  
❌ `face_threshold: float`

---

## Output Contract

### Frame Output

**Type**: `np.ndarray`

**Contract**:
```python
frame: np.ndarray
# Shape: (height, width, 3) - RGB color image
# Dtype: uint8 - 8-bit unsigned integer (0-255 per channel)
# Format: RGB (not BGR) - Gradio expects RGB ordering
# Source: Raw camera frame without modifications
```

**Requirements**:
- ✅ MUST be raw camera frame (no annotations)
- ✅ MUST NOT contain bounding boxes
- ✅ MUST NOT contain segmentation masks
- ✅ MUST NOT contain face recognition labels
- ✅ MUST NOT contain any overlays or text
- ✅ MUST maintain original camera resolution
- ✅ MUST be RGB format (Gradio requirement)

**Example Frame Properties**:
```python
assert frame.shape == (1024, 1280, 3)  # Camera resolution
assert frame.dtype == np.uint8
assert np.min(frame) >= 0
assert np.max(frame) <= 255
# No annotations mean frame is unmodified from camera
```

### Camera Info Output

**Type**: `str`

**Contract**:
```python
camera_info: str
# Format: Multi-line string with camera status and metrics
# Sections: Camera status, Performance metrics
# No processing metrics included
```

**Required Content**:
```
📹 Camera: [camera_model] ([resolution])

📊 Performance:
FPS: [X.X]
Frame time: [XX.X]ms
```

**Example**:
```
📹 Camera: MV-CA016-10UC (1280x1024)

📊 Performance:
FPS: 28.3
Frame time: 35.4ms
```

**Requirements**:
- ✅ MUST include camera model and resolution
- ✅ MUST include FPS (frames per second)
- ✅ MUST include frame time (milliseconds per frame)
- ✅ MUST NOT include segmentation metrics (detection count, processing time)
- ✅ MUST NOT include face recognition metrics (faces found, recognition time)
- ✅ MUST NOT include total processing time

### Removed Outputs

The following information **MUST NOT** be included in camera_info:

❌ Segmentation detection count  
❌ Segmentation processing time  
❌ Face recognition count  
❌ Face recognition processing time  
❌ Total processing time  
❌ Any processing-related warnings

---

## Streaming Behavior

### Session Management

**Contract**:
```python
# Check if camera already in use
if lifecycle.camera is None:
    error = lifecycle.on_session_start(session_hash)
    if error:
        gr.Warning(error)
        return  # Stop generator if blocked
```

**Requirements**:
- ✅ MUST enforce single viewer constraint (FR-006a)
- ✅ MUST reuse existing camera session if already initialized
- ✅ MUST block new sessions if camera in use
- ✅ MUST display warning message if blocked

### Frame Generation Loop

**Contract**:
```python
for frame in create_frame_generator(lifecycle.camera):
    # Calculate performance metrics
    current_time = time.time()
    frame_time_ms = (current_time - last_frame_time) * 1000
    fps = 1000.0 / frame_time_ms if frame_time_ms > 0 else 0.0
    
    # Build camera info (no processing metrics)
    camera_info = f"""
📹 Camera: {lifecycle.camera.info()}

📊 Performance:
FPS: {fps:.1f}
Frame time: {frame_time_ms:.1f}ms
"""
    
    yield frame, camera_info
```

**Requirements**:
- ✅ MUST yield frames continuously until page unload
- ✅ MUST calculate FPS from recent frames
- ✅ MUST NOT apply any processing to frames
- ✅ MUST handle timeouts gracefully (logged, not raised)
- ✅ MUST yield raw frames without modification

### Removed Behavior

The following behaviors **MUST NOT** be present:

❌ Processor initialization (`_ensure_processors_initialized()`)  
❌ Segmentation application (`seg_processor.process_frame()`)  
❌ Face recognition application (`face_processor.process_frame()`)  
❌ Processing time tracking (`seg_times`, `face_times` deques)  
❌ Processing warnings (high processing load messages)  
❌ Settings refresh for processing parameters  
❌ Model loading notifications

---

## Performance Contract

### Frame Rate

**Before Removal** (With Processing):
```
Frame rate: 10-15 FPS
Bottleneck: Processing time (50-130ms per frame)
```

**After Removal** (Raw Stream):
```
Frame rate: 25-30 FPS
Bottleneck: Camera hardware (~33ms per frame)
```

**Contract**:
- ✅ MUST achieve 25+ FPS (SC-004)
- ✅ MUST be limited only by camera hardware
- ✅ MUST NOT be limited by processing overhead

### Latency

**Before Removal**:
```
Camera → Processing (50-130ms) → Display
Total latency: ~100-150ms
```

**After Removal**:
```
Camera → Display
Total latency: ~35-40ms (camera capture time only)
```

**Contract**:
- ✅ MUST reduce latency by 60-70%
- ✅ MUST eliminate processing delay
- ✅ MUST deliver frames as fast as camera captures them

### Resource Usage

**Contract**:
- ✅ MUST reduce CPU usage by 60%+ (SC-003)
- ✅ MUST reduce memory usage by 60%+ (SC-003)
- ✅ MUST NOT load ML models (no processing overhead)

---

## Error Handling

### Camera Not Available

```python
if lifecycle.camera is None:
    error = lifecycle.on_session_start(session_hash)
    if error:
        logger.warning(f"Session blocked: {session_hash}")
        gr.Warning(error)
        return
```

**Contract**:
- ✅ MUST display user-friendly error message
- ✅ MUST log error for debugging
- ✅ MUST NOT crash or raise exception
- ✅ MUST allow retry (user can refresh page)

### Frame Timeout

```python
for frame in create_frame_generator(lifecycle.camera):
    # Timeouts handled in generator (yields None)
    if frame is None:
        # Skip frame, continue streaming
        continue
```

**Contract**:
- ✅ MUST handle frame timeouts gracefully
- ✅ MUST continue streaming after timeout
- ✅ MUST log timeout for debugging
- ✅ MUST NOT stop generator on timeout

### Fatal Camera Error

```python
try:
    for frame in create_frame_generator(lifecycle.camera):
        yield frame, camera_info
except CameraException as e:
    logger.error(f"Camera error: {e}")
    gr.Error(f"Camera error: {e}")
```

**Contract**:
- ✅ MUST catch fatal camera errors
- ✅ MUST display error to user
- ✅ MUST log error for debugging
- ✅ MUST stop generator on fatal error

---

## Integration Points

### Camera Capture

**Integration**: `create_frame_generator(lifecycle.camera)`

**Contract**:
- ✅ MUST use existing camera capture logic (unchanged)
- ✅ MUST receive frames from `src.camera.capture.create_frame_generator()`
- ✅ MUST NOT modify frame capture implementation

### Session Lifecycle

**Integration**: `SessionLifecycle(session_manager)`

**Contract**:
- ✅ MUST use existing session management (unchanged)
- ✅ MUST enforce single viewer via `lifecycle.on_session_start()`
- ✅ MUST clean up via `lifecycle.on_session_end()` on page unload

### Exposure Settings

**Integration**: `current_settings["auto_exposure"]`, `current_settings["exposure_time_ms"]`

**Contract**:
- ✅ MUST respect camera exposure settings (unchanged)
- ✅ MUST apply exposure changes via `_apply_exposure_settings()`
- ✅ MUST NOT interfere with frame streaming

---

## Testing Requirements

### Contract Tests

```python
def test_frame_stream_signature():
    """Frame stream accepts only request parameter"""
    sig = inspect.signature(frame_stream)
    assert list(sig.parameters.keys()) == ["request"]

def test_frame_stream_output_format():
    """Frame stream yields (frame, info) tuples"""
    generator = frame_stream(mock_request)
    frame, info = next(generator)
    
    assert isinstance(frame, np.ndarray)
    assert frame.dtype == np.uint8
    assert len(frame.shape) == 3  # H×W×C
    assert isinstance(info, str)

def test_raw_frame_no_annotations():
    """Frames are raw without annotations"""
    generator = frame_stream(mock_request)
    frame, _ = next(generator)
    
    # Verify frame is unmodified from camera
    # (Implementation-specific: check no opencv drawing calls)

def test_camera_info_no_processing():
    """Camera info excludes processing metrics"""
    generator = frame_stream(mock_request)
    _, info = next(generator)
    
    assert "segmentation" not in info.lower()
    assert "face" not in info.lower()
    assert "processing" not in info.lower()
    assert "Camera" in info
    assert "FPS" in info
```

### Performance Tests

```python
def test_frame_rate_meets_target():
    """Stream achieves 25+ FPS"""
    generator = frame_stream(mock_request)
    
    start = time.time()
    for _ in range(100):
        next(generator)
    elapsed = time.time() - start
    
    fps = 100 / elapsed
    assert fps >= 25.0  # SC-004

def test_no_processing_overhead():
    """No processing time added to frame pipeline"""
    generator = frame_stream(mock_request)
    
    # Measure frame times
    times = []
    for _ in range(30):
        start = time.time()
        next(generator)
        times.append(time.time() - start)
    
    avg_time = sum(times) / len(times)
    assert avg_time < 0.050  # <50ms (camera only, no processing)
```

---

## Success Criteria (from spec)

This frame stream contract fulfills:

- ✅ **FR-003**: Raw camera feed without overlays
- ✅ **FR-012**: Maintains camera performance (25+ FPS)
- ✅ **SC-001**: No segmentation masks or face labels in frames
- ✅ **SC-004**: Maintains 25+ FPS frame rate
- ✅ **SC-008**: Core camera operations unchanged

---

## Migration Notes

### Code Changes Required

**Remove from frame_stream():**
```python
# DELETE: Processing parameter extraction
enable_segmentation = settings["enable_segmentation"]
enable_face_recognition = settings["enable_face_recognition"]

# DELETE: Processor initialization
_ensure_processors_initialized()

# DELETE: Processing application
if enable_segmentation and seg_processor:
    frame, seg_debug = seg_processor.process_frame(frame)
if enable_face_recognition and face_processor:
    frame, face_debug = face_processor.process_frame(frame)

# DELETE: Processing time tracking
seg_times = deque(maxlen=30)
face_times = deque(maxlen=30)
```

**Keep in frame_stream():**
```python
# KEEP: Session management
session_hash = request.session_hash or "unknown"
error = lifecycle.on_session_start(session_hash)

# KEEP: Frame capture loop
for frame in create_frame_generator(lifecycle.camera):
    # Calculate FPS
    # Build camera_info (no processing)
    yield frame, camera_info
```

### Backward Compatibility

**Breaking Changes**:
- ❌ Function signature changed (removed 9 parameters)
- ❌ No processing applied to frames
- ❌ Camera info format simplified

**Preserved Behavior**:
- ✅ Output format unchanged (still tuple of frame + info)
- ✅ Session management unchanged
- ✅ Camera capture unchanged
- ✅ Error handling unchanged

---

## Summary

**Parameters**: 10 → 1 (90% reduction)  
**Processing Stages**: 2 → 0 (removed)  
**Frame Rate**: ~15 FPS → ~28 FPS (87% increase)  
**Latency**: ~120ms → ~35ms (71% reduction)  

This simplified frame stream focuses solely on efficient camera capture and display, eliminating all processing overhead while maintaining core streaming functionality.

# UI Contract: Simplified Camera Interface

**Feature**: Remove processing pipelines  
**Date**: 2025-10-09  
**Contract Type**: User Interface

## Overview

This contract defines the simplified Gradio UI after removing image segmentation and face recognition features. The UI focuses solely on camera feed display and camera control settings.

---

## UI Components

### 1. Camera Feed Display

**Component**: `gr.Image`

**Contract**:
```python
image = gr.Image(
    label="Live Camera Feed",
    show_label=True,
    show_download_button=False,
    # Streaming enabled via .load() event
)
```

**Behavior**:
- ✅ MUST display raw camera frames without any annotations
- ✅ MUST update continuously (streaming mode)
- ✅ MUST NOT show segmentation masks
- ✅ MUST NOT show bounding boxes
- ✅ MUST NOT show face recognition labels
- ✅ MUST maintain aspect ratio of camera frames
- ✅ MUST auto-resize to fit viewport

**Output Format**:
- Type: `np.ndarray` (RGB, uint8)
- Shape: `(height, width, 3)` from camera
- No overlays or annotations applied

---

### 2. Camera Info Display

**Component**: `gr.Textbox`

**Contract**:
```python
camera_info = gr.Textbox(
    label="📹 Camera Info",
    lines=4,
    max_lines=4,
    interactive=False,
    show_copy_button=False,
)
```

**Behavior**:
- ✅ MUST display camera status information
- ✅ MUST display performance metrics (FPS, frame time)
- ✅ MUST NOT display segmentation metrics
- ✅ MUST NOT display face recognition metrics
- ✅ MUST update in real-time with frame stream

**Content Format**:
```
📹 Camera: [Camera model and status]

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

---

### 3. Camera Controls

**Layout**: Single column (no tabs)

#### 3.1 Auto Exposure Toggle

**Component**: `gr.Checkbox`

**Contract**:
```python
auto_exposure = gr.Checkbox(
    label="Auto Exposure",
    value=False,
    info="Enable automatic exposure control",
)
```

**Behavior**:
- ✅ MUST control camera auto-exposure mode
- ✅ MUST disable exposure slider when enabled
- ✅ MUST enable exposure slider when disabled
- ✅ MUST apply setting immediately (no restart needed)

**State Management**:
- Default: `False` (manual exposure)
- Persisted in: `current_settings["auto_exposure"]`
- Applied via: `_apply_exposure_settings()`

#### 3.2 Exposure Time Slider

**Component**: `gr.Slider`

**Contract**:
```python
exposure_slider = gr.Slider(
    label="Shutter Speed (Exposure Time)",
    minimum=0.1,
    maximum=100.0,
    value=30.0,
    step=0.1,
    info="Exposure in milliseconds (lower=faster/darker, higher=slower/brighter)",
    interactive=True,  # Disabled when auto_exposure=True
)
```

**Behavior**:
- ✅ MUST control manual exposure time in milliseconds
- ✅ MUST be disabled when auto exposure is enabled
- ✅ MUST convert ms to microseconds for SDK (exposure_us = exposure_ms * 1000)
- ✅ MUST apply setting immediately (no restart needed)
- ✅ MUST update camera exposure via SDK

**Value Range**:
- Minimum: 0.1ms (fast shutter, dark image, freeze motion)
- Maximum: 100.0ms (slow shutter, bright image, motion blur)
- Default: 30.0ms (balanced for general use)
- Step: 0.1ms (fine-grained control)

**State Management**:
- Default: `30.0` (ms)
- Persisted in: `current_settings["exposure_time_ms"]`
- Applied via: `lifecycle.camera.set_exposure_time(exposure_us)`

#### 3.3 Exposure Guide

**Component**: `gr.Markdown`

**Contract**:
```python
gr.Markdown("""
**📸 Exposure Guide:**
- **Fast motion**: Use shorter exposure (1-10ms) to freeze motion
- **Low light**: Use longer exposure (30-100ms) for brighter image
- **Auto mode**: Camera adjusts exposure automatically
- Default: 30ms (good balance for most scenarios)

**SDK Reference:** Spec section 5.1-5.2
- Manual: CameraSetAeState(0) + CameraSetExposureTime()
- Auto: CameraSetAeState(1)
""")
```

**Behavior**:
- ✅ MUST provide user guidance on exposure settings
- ✅ MUST reference SDK documentation
- ✅ Static content (no dynamic updates)

---

## Removed Components

The following components **MUST NOT** be present in the simplified UI:

### ❌ Removed from UI

1. **Enable Object Segmentation** checkbox - DELETED
2. **Enable Face Recognition** checkbox - DELETED
3. **Segmentation Tab** - DELETED
   - Model Size dropdown
   - Confidence Threshold slider
   - Enable Tracking checkbox
   - Class Selection dropdown
   - Select All / Clear Selection buttons
   - Model info and troubleshooting markdown
4. **Face Recognition Tab** - DELETED
   - Recognition Model dropdown
   - Face Detector dropdown
   - Recognition Threshold slider
   - Enroll New Face section (image upload, name input, enroll button)
   - Face Database section (face list dropdown, delete button)
   - Face recognition tips markdown
5. **Processing Tabs Container** - DELETED

---

## Layout Structure

### Before Removal (With Tabs)

```
┌─────────────────────────────────────────────┐
│ Camera Feed Display                         │
├─────────────────────────────────────────────┤
│ Detection & Recognition Info (Debug)        │
├─────────────────────────────────────────────┤
│ ┌──────────────────────────────────────┐   │
│ │ Live Camera Feed (Image)             │   │
│ └──────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│ Processing Controls                         │
│ ├─ Enable Object Segmentation    [ ]       │
│ ├─ Enable Face Recognition       [ ]       │
│ └─ Tabs                                     │
│    ├─ Segmentation                          │
│    ├─ Face Recognition                      │
│    └─ Camera Settings                       │
└─────────────────────────────────────────────┘
```

### After Removal (Simplified)

```
┌─────────────────────────────────────────────┐
│ Camera Feed Display                         │
├─────────────────────────────────────────────┤
│ 📹 Camera Info (Textbox)                    │
├─────────────────────────────────────────────┤
│ ┌──────────────────────────────────────┐   │
│ │ Live Camera Feed (Image)             │   │
│ └──────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│ Camera Controls                             │
│ ├─ Auto Exposure              [ ]           │
│ ├─ Shutter Speed              [====o===]    │
│ └─ 📸 Exposure Guide (help text)            │
└─────────────────────────────────────────────┘
```

**Changes**:
- ✅ Removed processing enable checkboxes
- ✅ Removed tab container (no longer needed)
- ✅ Direct camera controls (no tab nesting)
- ✅ Simpler, cleaner layout
- ✅ ~60% reduction in UI complexity

---

## Event Handlers

### Preserved Events

**1. Page Load (Auto-start streaming)**
```python
app.load(
    fn=frame_stream,
    outputs=[image, camera_info],
)
```
- ✅ MUST auto-start camera stream on page load (FR-003)
- ✅ MUST display camera feed immediately
- ✅ MUST NOT require user action to start

**2. Auto Exposure Change**
```python
auto_exposure.change(
    fn=update_settings,
    inputs=[auto_exposure, exposure_slider],
    outputs=settings_state,
)
```
- ✅ MUST update camera exposure mode
- ✅ MUST toggle exposure slider interactive state
- ✅ MUST apply setting to camera immediately

**3. Exposure Slider Change**
```python
exposure_slider.change(
    fn=update_settings,
    inputs=[auto_exposure, exposure_slider],
    outputs=settings_state,
)
```
- ✅ MUST update camera exposure time
- ✅ MUST convert ms to microseconds for SDK
- ✅ MUST apply setting to camera immediately

**4. Page Unload (Cleanup)**
```python
app.unload(
    fn=on_unload,
)
```
- ✅ MUST release camera resources (FR-005)
- ✅ MUST allow next viewer to connect
- ✅ MUST clean up session state

### Removed Events

The following event handlers **MUST NOT** be present:

❌ Processing enable checkbox changes  
❌ Model size dropdown changes  
❌ Confidence slider changes  
❌ Tracking checkbox changes  
❌ Class selection dropdown changes  
❌ Select All / Clear Selection button clicks  
❌ Face model dropdown changes  
❌ Face detector dropdown changes  
❌ Face threshold slider changes  
❌ Face enrollment button clicks  
❌ Face deletion button clicks

---

## State Management

### Simplified State

**Current Settings (Global)**:
```python
current_settings = {
    "auto_exposure": False,
    "exposure_time_ms": 30.0,
}
```

**Gradio State**:
```python
settings_state = gr.State({
    "auto_exposure": False,
    "exposure_time_ms": 30.0,
})
```

### Removed State

The following state variables **MUST NOT** be present:

❌ `enable_segmentation`  
❌ `model_size`  
❌ `confidence`  
❌ `enable_tracking`  
❌ `selected_classes`  
❌ `enable_face_recognition`  
❌ `face_model`  
❌ `face_detector`  
❌ `face_threshold`

---

## Contract Verification

### Required Tests

**UI Contract Tests (`test_gradio_ui_contract.py`):**

```python
def test_camera_feed_display_exists():
    """Camera feed image component exists"""
    assert image component is gr.Image
    assert label == "Live Camera Feed"

def test_camera_info_display_exists():
    """Camera info textbox exists"""
    assert camera_info component is gr.Textbox
    assert label == "📹 Camera Info"

def test_exposure_controls_exist():
    """Exposure controls exist and are functional"""
    assert auto_exposure checkbox exists
    assert exposure_slider exists
    assert exposure_guide markdown exists

def test_no_processing_controls():
    """No processing controls present in UI"""
    assert no "Segmentation" components
    assert no "Face Recognition" components
    assert no enable_segmentation checkbox
    assert no enable_face_recognition checkbox

def test_auto_start_streaming():
    """Camera stream auto-starts on page load"""
    assert app.load event is configured
    assert fn == frame_stream

def test_localhost_only():
    """Server enforces localhost-only access (FR-012)"""
    assert server_name == "127.0.0.1"
    assert share == False
```

### Integration Tests

```python
def test_raw_feed_no_annotations():
    """Camera feed displays without processing annotations"""
    frame = get_frame_from_ui()
    assert no bounding boxes in frame
    assert no segmentation masks in frame
    assert no face labels in frame

def test_exposure_control_works():
    """Exposure controls update camera settings"""
    set_auto_exposure(True)
    assert camera uses auto exposure
    
    set_auto_exposure(False)
    set_exposure_time(50.0)
    assert camera exposure == 50000  # microseconds
```

---

## Success Criteria (from spec)

This UI contract fulfills:

- ✅ **SC-001**: Camera feed without annotations (raw display)
- ✅ **SC-002**: No segmentation/face recognition controls visible
- ✅ **FR-011**: Simplified UI with camera controls only
- ✅ **FR-004**: No segmentation UI controls present
- ✅ **FR-005**: No face recognition UI controls present

---

## Notes

- UI simplification reduces code by ~400 lines in `app.py`
- Simpler UX with direct controls (no tab navigation)
- Faster page load (no model loading UI elements)
- Clearer focus on camera operations
- Easier to maintain (fewer components, fewer event handlers)

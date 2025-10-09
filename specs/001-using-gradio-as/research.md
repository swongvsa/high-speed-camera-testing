# Research: Camera Feed Display Implementation

## 1. Gradio Real-Time Streaming Patterns

### Decision: Use `gr.Image()` with generator-based streaming

**Rationale**:
- Gradio's `gr.Image()` component supports continuous updates via generator functions
- Generator pattern allows infinite streaming without blocking the UI thread
- Can yield NumPy arrays directly, which aligns with camera SDK output format

**Implementation Pattern**:
```python
def video_stream():
    while camera_active:
        frame = capture_frame()  # Returns NumPy array
        yield frame

gr.Image(value=video_stream, streaming=True, every=0.033)  # ~30fps update
```

**Alternatives Considered**:
- ❌ `gr.Video()`: Requires file input, not suitable for live streaming
- ❌ Manual `gr.Image().update()`: Requires complex event handling, less efficient
- ❌ WebRTC components: Overkill for localhost-only, adds complexity

**Gradio Server Configuration for Localhost**:
```python
interface.launch(
    server_name="127.0.0.1",  # Localhost only
    server_port=7860,
    share=False,              # Disable public URL
    inbrowser=True            # Auto-open browser
)
```

## 2. Camera SDK Integration

### Decision: Wrap SDK in async-friendly abstraction with context manager

**Rationale**:
- Existing `cv_grab.py` shows synchronous blocking pattern
- Need clean resource management for camera init/cleanup
- Context manager ensures proper resource release on disconnect

**SDK Initialization Flow** (from cv_grab.py):
1. `mvsdk.CameraEnumerateDevice()` - List cameras
2. `mvsdk.CameraInit(DevInfo, -1, -1)` - Initialize selected camera
3. `mvsdk.CameraGetCapability(hCamera)` - Get camera specs
4. `mvsdk.CameraSetIspOutFormat()` - Set output format (MONO8/BGR8)
5. `mvsdk.CameraSetTriggerMode(hCamera, 0)` - Continuous capture mode
6. `mvsdk.CameraPlay(hCamera)` - Start capture thread

**Frame Capture Pattern**:
```python
pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, timeout=200)
mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)
mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)

# Convert to NumPy array
frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
frame = np.frombuffer(frame_data, dtype=np.uint8)
frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, channels))
```

**Error Handling**:
- `mvsdk.CameraException`: Catch specific error codes
- `CAMERA_STATUS_TIME_OUT`: Normal, retry frame capture
- Other errors: Log and propagate to UI for user notification

**Alternatives Considered**:
- ❌ Direct SDK calls in UI layer: Violates separation of concerns
- ❌ Threaded capture with queue: Adds complexity, not needed for single viewer
- ✅ Context manager pattern: Clean, Pythonic, ensures cleanup

## 3. Single-Session Concurrency Control

### Decision: Use application-level flag with Gradio session events

**Rationale**:
- Gradio doesn't provide built-in single-session enforcement
- Simple flag-based locking sufficient for localhost demo use case
- Session load/unload events provide hooks for lock management

**Implementation Strategy**:
```python
_active_session = None
_session_lock = threading.Lock()

def on_session_start(request: gr.Request):
    with _session_lock:
        if _active_session is not None:
            raise gr.Error("Camera already in use. Only one viewer allowed.")
        _active_session = request.session_hash

def on_session_end(request: gr.Request):
    with _session_lock:
        if _active_session == request.session_hash:
            _active_session = None
            cleanup_camera()
```

**Gradio Integration**:
- Use `demo.load()` event for session start detection
- Use `demo.unload()` for cleanup (browser close/navigate away)
- Display informative error message for blocked second viewer

**Alternatives Considered**:
- ❌ OS-level mutex/semaphore: Overkill for Python app
- ❌ Network socket locking: Too complex for localhost
- ❌ No restriction: Violates FR-006a requirement

## 4. Performance Optimization

### Decision: Zero-copy frame passing with minimal buffering

**Rationale**:
- Camera SDK already provides frame in memory-aligned buffer
- NumPy arrays share memory with C buffers (no copy needed)
- Gradio accepts NumPy arrays directly

**Optimization Techniques**:

1. **Zero-Copy Path**:
   - SDK buffer → NumPy view (no copy)
   - NumPy array → Gradio (reference passed)
   - Only platform flip (Windows) requires actual copy

2. **Frame Rate Matching**:
   - Set Gradio `every` parameter to match camera frame interval
   - Camera max FPS from `cap.sResolutionRange` capability
   - Generator yields only when new frame available

3. **Memory Management**:
   - Pre-allocate frame buffer once: `mvsdk.CameraAlignMalloc()`
   - Reuse same buffer for all frames
   - Release on cleanup: `mvsdk.CameraAlignFree()`

4. **Latency Minimization**:
   - Skip frame processing if display can't keep up
   - Set camera timeout to 200ms (balance responsiveness/CPU)
   - No queuing/buffering beyond SDK's internal buffer

**Platform-Specific Handling** (from cv_grab.py):
```python
if platform.system() == "Windows":
    mvsdk.CameraFlipFrameBuffer(pFrameBuffer, FrameHead, 1)  # Vertical flip
# Linux/macOS: no flip needed
```

**Measured Performance Targets**:
- Frame capture: <10ms (SDK operation)
- NumPy conversion: <5ms (memory view, no copy)
- Gradio render: <20ms (browser-dependent)
- Total latency budget: <50ms (well under 100ms requirement)

**Alternatives Considered**:
- ❌ Frame buffering queue: Adds latency, not needed
- ❌ Downsampling: Violates native resolution requirement (FR-010)
- ❌ Frame skipping: Only if browser can't keep up (monitor, don't force)

## 5. Browser Compatibility (Deferred Item from Spec)

### Decision: Target modern browsers with fallback messaging

**Rationale**:
- Gradio generates standard HTML5/JavaScript
- Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+) all supported
- Localhost use means presenter controls environment

**Implementation**:
- No special browser detection needed
- Gradio handles compatibility internally
- If issues arise, display system requirements in README

## 6. Camera Type Support (Deferred Item from Spec)

### Decision: Support both monochrome and color cameras automatically

**Rationale**:
- SDK example already shows detection pattern
- `cap.sIspCapacity.bMonoSensor` flag indicates camera type
- Format selection: MONO8 for mono, BGR8 for color

**Implementation** (from cv_grab.py):
```python
monoCamera = (cap.sIspCapacity.bMonoSensor != 0)

if monoCamera:
    mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
    channels = 1
else:
    mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)
    channels = 3

# Reshape with appropriate channel count
frame = frame.reshape((height, width, channels))
```

## Summary of Research Decisions

| Area | Decision | Key Benefit |
|------|----------|-------------|
| Streaming | gr.Image() with generator | Native Gradio support, efficient |
| SDK Wrapper | Context manager abstraction | Clean resource management |
| Concurrency | Application-level flag | Simple, effective for localhost |
| Performance | Zero-copy frame path | Minimal latency, max FPS |
| Browser Support | Modern browsers (auto) | No special handling needed |
| Camera Types | Automatic detection | Works with any camera |

**All NEEDS CLARIFICATION items from Technical Context have been resolved.**

Ready for Phase 1: Design & Contracts

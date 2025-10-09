# MindVision SDK Implementation Reference

This document describes how the high-speed camera testing application implements the MindVision Industrial Camera SDK based on the official specification.

## Specification Source

All implementations follow **spec/llm.txt** - MindVision Industrial Camera SDK Specification (v2.4)

## Key Implementation Decisions

### 1. SDK Initialization (Section 2.1, 23.1, 23.14)

**Requirement**: `CameraSdkInit(1)` must be called before any camera operations.

**Implementation**: `src/lib/mvsdk.py:52-58`
```python
# Initialize SDK (CRITICAL: must be called before any camera operations)
# Per spec/llm.txt section 23.1 and 23.14
try:
    if _sdk is not None:
        _sdk.CameraSdkInit(1)  # 1 = Chinese language, 0 = English
except Exception as e:
    print(f"Warning: CameraSdkInit failed: {e}")
```

This is automatically called when the `mvsdk` module is imported.

### 2. High-Speed Capture Configuration (Section 5.1, 16.1, 19.2)

**Requirements**:
- Manual exposure for consistent frame timing
- High-speed frame mode
- Continuous capture (non-triggered)

**Implementation**: `src/camera/device.py:222-232`
```python
# Set continuous capture mode
mvsdk.CameraSetTriggerMode(hCamera, 0)

# Optimize for max FPS (spec section 19.2)
mvsdk.CameraSetFrameSpeed(hCamera, 2)  # High speed mode

# Set manual exposure for consistent capture (spec section 5.1)
mvsdk.CameraSetAeState(hCamera, 0)  # Manual exposure
mvsdk.CameraSetExposureTime(hCamera, 30 * 1000)  # 30ms default
```

### 3. Memory Management (Section 19.3, 23.9)

**Requirements**:
- 16-byte aligned buffers for SIMD optimization
- Zero-copy NumPy conversion
- Proper buffer cleanup

**Implementation**: `src/camera/device.py:234-240, 287-290`
```python
# Allocate aligned buffer
buffer_size = max_width * max_height * channels
self._frame_buffer = mvsdk.CameraAlignMalloc(buffer_size, 16)

# Zero-copy conversion
frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self._frame_buffer)
frame = np.frombuffer(frame_data, dtype=np.uint8)

# Cleanup
mvsdk.CameraAlignFree(self._frame_buffer)
```

### 4. Error Handling (Section 15, 23.3, 23.9.5)

**Requirements**:
- Use `CameraGetErrorString` for descriptive errors
- Handle timeouts gracefully (expected behavior)
- Cleanup on errors

**Implementation**: `src/camera/device.py:346-347`
```python
except mvsdk.CameraException as e:
    if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
        continue  # Timeout is normal, continue capturing

    error_str = mvsdk.CameraGetErrorString(e.error_code)
    raise CameraException(f"Frame capture failed: {error_str}", e.error_code)
```

### 5. Platform-Specific Handling (Section 23.9.1)

**Requirement**: Windows requires vertical frame buffer flip.

**Implementation**: `src/camera/device.py:321-323`
```python
# Windows requires vertical flip (BMP format quirk)
if platform.system() == "Windows":
    mvsdk.CameraFlipFrameBuffer(self._frame_buffer, FrameHead, 1)
```

### 6. Image Format Configuration (Section 4.3, 23.11)

**Requirements**:
- Set output format based on camera type (mono vs color)
- Use BGR8 for OpenCV compatibility

**Implementation**: `src/camera/device.py:248-253`
```python
# Determine mono vs color
self._is_mono = self._capability.sIspCapacity.bMonoSensor != 0

# Set output format
if self._is_mono:
    mvsdk.CameraSetIspOutFormat(self._handle, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
else:
    mvsdk.CameraSetIspOutFormat(self._handle, mvsdk.CAMERA_MEDIA_TYPE_BGR8)
```

## Compliance Checklist (Section 23.14)

From the spec's "Python Implementation Checklist":

- ✅ Load SDK based on platform (Windows/Mac/Linux)
- ✅ Call `CameraSdkInit(1)` before any other function
- ✅ Use `CameraAlignMalloc(size, 16)` for frame buffers
- ✅ Set output format with `CameraSetIspOutFormat()` after init
- ✅ Call `CameraPlay()` before capture
- ✅ Always pair `CameraGetImageBuffer()` with `CameraReleaseImageBuffer()`
- ✅ Always call `CameraUnInit()` before exit
- ✅ Always call `CameraAlignFree()` for allocated buffers
- ✅ Windows: Call `CameraFlipFrameBuffer()` after process
- ✅ Use `np.frombuffer()` for zero-copy conversion
- ✅ Handle timeout exceptions gracefully

## Performance Optimizations (Section 19)

Applied optimizations from spec section 19:

1. **Reduce CPU Load** (19.1):
   - ✅ Use grayscale (MONO8) when color not needed
   - ✅ Native resolution (no unnecessary resizing)
   - ✅ Minimal ISP processing in high-speed mode
   - ✅ Zero-copy NumPy conversion

2. **Increase Frame Rate** (19.2):
   - ✅ Manual exposure (consistent timing)
   - ✅ `CameraSetFrameSpeed(hCamera, 2)` (high speed)
   - ✅ Native resolution (no ROI overhead for full frame)

3. **Memory Efficiency** (19.3):
   - ✅ `CameraAlignMalloc(size, 16)` for SIMD alignment
   - ✅ Allocate buffers once, reuse in loop
   - ✅ Proper cleanup with `CameraAlignFree(ptr)`

## Common Patterns Implemented

### Pattern 1: Continuous Capture (Section 23.4)
Used in `src/camera/device.py::capture_frames()`

### Pattern 4: Multi-Camera Support (Section 23.7)
Supported via `CameraDevice.enumerate_cameras()` and device index selection

## Reference Documentation

For detailed API documentation, see:
- **spec/llm.txt** - Complete SDK specification
- **spec/python_demo/** - Reference implementations
- **spec/manual.txt** - Official Chinese manual

## Testing SDK Compliance

To verify SDK is working correctly:

```bash
# Check camera connectivity
python main.py --check

# Test with specific camera IP (for GigE cameras)
python main.py --camera-ip 169.254.22.149 --check
```

## Troubleshooting

### "MVSDK native library not loaded"
- Ensure the SDK is installed in `spec/Mac_sdk_m1(250120)/lib/libmvsdk.dylib` (macOS M1)
- Or install system-wide SDK

### "CameraSdkInit failed"
- Check that the native SDK library is compatible with your OS
- Verify file permissions on the SDK library

### Frame rate lower than expected
- Check exposure time: `camera.set_exposure_time(10000)` (10ms)
- Verify high-speed mode is active (automatically set in `device.py`)
- Check CPU usage (reduce if necessary per section 19.1)

## Additional Features Available

The SDK supports many features not currently exposed:

- Hardware trigger modes (Section 7)
- ROI (Region of Interest) for higher FPS (Section 6)
- White balance control (Section 9)
- GPIO/Strobe control (Section 12)
- Video recording (Section 11)

These can be added by following patterns in spec/llm.txt sections 6-12.

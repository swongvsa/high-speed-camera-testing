# Exposure Control Implementation

## Overview
Added comprehensive shutter speed (exposure time) controls to the Gradio UI, enabling both automatic and manual exposure control based on the MindVision SDK spec (sections 5.1-5.2).

## Features Added

### 1. Camera Settings Tab
New tab in the Gradio interface with exposure controls:
- **Auto Exposure Toggle**: Enable/disable automatic exposure (SDK: `CameraSetAeState`)
- **Shutter Speed Slider**: Manual exposure time control (0.1-100ms)
  - Range: 0.1ms to 100ms
  - Step: 0.1ms
  - Default: 30ms
  - Converted to microseconds for SDK (1ms = 1000µs)

### 2. Backend Implementation

#### Settings State
Added to `current_settings`:
```python
"auto_exposure": False,           # Auto vs manual mode
"exposure_time_ms": 30.0,        # Exposure in milliseconds
```

#### Exposure Application Function
New function `_apply_exposure_settings()` (src/ui/app.py:159-180):
- Checks if camera is initialized
- Applies auto-exposure mode: `CameraSetAeState(handle, 1)`
- Or applies manual exposure: `CameraSetExposureTime(handle, exposure_us)`
- Converts milliseconds to microseconds for SDK
- Called every 10 frames during streaming for dynamic updates

### 3. User Interface

**Location**: Camera Settings tab (after Face Recognition tab)

**Controls**:
1. **Auto Exposure** checkbox
   - When enabled: Camera automatically adjusts exposure
   - When disabled: User controls exposure via slider

2. **Shutter Speed slider**
   - Label: "Shutter Speed (Exposure Time)"
   - Units: Milliseconds
   - Info text explains relationship (lower=faster/darker, higher=slower/brighter)

**Guidance provided**:
- Fast motion: Use 1-10ms to freeze motion
- Low light: Use 30-100ms for brighter image
- Auto mode: Camera adjusts automatically
- Default: 30ms (balanced for most scenarios)

### 4. SDK Integration

Based on spec/llm.txt sections 5.1-5.2:

**Manual Exposure** (SDK spec 5.1):
```python
mvsdk.CameraSetAeState(handle, 0)  # 0 = manual mode
mvsdk.CameraSetExposureTime(handle, time_us)  # microseconds
```

**Auto Exposure** (SDK spec 5.2):
```python
mvsdk.CameraSetAeState(handle, 1)  # 1 = auto mode
```

### 5. Integration Points

**Settings Update Flow**:
1. User adjusts UI controls →
2. Gradio change handler triggers `update_settings()` →
3. Updates `current_settings` dict →
4. Every 10 frames in stream loop →
5. Calls `_apply_exposure_settings()` →
6. Applies to camera via SDK

**Files Modified**:
- `src/ui/app.py`: Added exposure controls and settings management

## Usage

### Manual Exposure
1. Navigate to "Camera Settings" tab
2. Ensure "Auto Exposure" is unchecked
3. Adjust "Shutter Speed" slider
4. Changes apply within 10 frames (~0.3 seconds)

### Auto Exposure
1. Navigate to "Camera Settings" tab
2. Check "Auto Exposure"
3. Camera automatically adjusts based on scene brightness

## Technical Details

### Exposure Time Conversion
- UI displays: **milliseconds** (user-friendly)
- SDK requires: **microseconds**
- Conversion: `exposure_us = exposure_ms * 1000`

### Update Frequency
- Settings checked every 10 frames
- Prevents excessive SDK calls
- Provides near real-time responsiveness

### Default Values
- Auto exposure: **OFF** (manual mode)
- Exposure time: **30ms** (30,000µs)
- Matches camera initialization defaults in `CameraDevice._initialize()`

## Testing

Once camera is available:
1. Launch app: `uv run main.py --camera-ip <IP>`
2. Open browser to http://127.0.0.1:7860
3. Navigate to "Camera Settings" tab
4. Test exposure controls:
   - Toggle auto exposure on/off
   - Adjust slider and observe brightness changes
   - Check terminal logs for exposure updates

Expected log output:
```
📸 Manual exposure: 30.0ms (30000µs)
📸 Auto-exposure enabled
```

## References

- **SDK Spec**: spec/llm.txt sections 5.1-5.2
- **Camera Device**: src/camera/device.py:205-230 (`set_exposure_time` method)
- **Implementation**: src/ui/app.py:159-180 (`_apply_exposure_settings` function)
- **UI Code**: src/ui/app.py:778-809 (Camera Settings tab)

## Future Enhancements

Potential additions (from SDK spec):
- Analog gain control (SDK spec 5.1: `CameraSetAnalogGain`)
- Auto-exposure target brightness (SDK spec 5.2: `CameraSetAeTarget`)
- Auto-exposure window selection (SDK spec 5.2: `CameraSetAEWindow`)
- Frame speed control (SDK spec 16.1: `CameraSetFrameSpeed`)

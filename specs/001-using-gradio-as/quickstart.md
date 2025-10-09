# Quickstart: Camera Feed Display

## Prerequisites
- Python 3.11 or higher
- High-speed camera connected via USB
- macOS or Linux operating system

## Installation

```bash
# 1. Install dependencies
pip install gradio opencv-python numpy

# 2. Ensure camera SDK is available
# SDK should be in spec/python_demo/mvsdk.py
# SDK binaries in spec/macsdk(240831)/ (macOS) or spec/linuxSDK/ (Linux)

# 3. Verify camera connection
python spec/python_demo/cv_grab.py  # Should show camera feed in OpenCV window
```

## Running the Application

```bash
# Start the camera viewer
python src/main.py
```

Expected output:
```
Running on local URL: http://127.0.0.1:7860
* Opening browser...
Camera initialized: [Camera Name]
Streaming at [FPS] fps, [Width]x[Height] resolution
```

## User Workflow Validation

### Scenario 1: Successful Camera Feed Display (FR-001, FR-002, FR-003)

**Test Steps**:
1. Connect camera to computer
2. Run: `python src/main.py`
3. Browser opens automatically to http://127.0.0.1:7860
4. Observe camera feed

**Expected Results**:
- ✅ Camera feed appears within 1 second (FR-003 auto-start)
- ✅ Live video updates continuously (FR-006)
- ✅ Display shows native camera resolution (FR-010)
- ✅ Frame rate matches camera max FPS (FR-009)
- ✅ Both color and mono cameras work (FR-007)

**Validation**:
```bash
# Check logs for confirmation
# Should see:
# "Camera detected: [Name]"
# "Resolution: [W]x[H]"
# "Streaming started"
```

### Scenario 2: Single Viewer Restriction (FR-006a)

**Test Steps**:
1. Run `python src/main.py` (first viewer)
2. Camera feed displays successfully
3. Open second browser tab to http://127.0.0.1:7860 (second viewer)

**Expected Results**:
- ✅ First viewer: Camera feed continues normally
- ✅ Second viewer: Error message "Camera already in use. Only one viewer allowed."
- ✅ Second tab shows informative message, not blank screen

**Validation**:
```bash
# Check logs:
# "Session blocked: camera in use"
```

### Scenario 3: No Camera Error Handling (FR-004)

**Test Steps**:
1. Disconnect camera (or run without camera)
2. Run: `python src/main.py`
3. Browser opens to interface

**Expected Results**:
- ✅ Clear error message: "No camera detected. Please connect a camera."
- ✅ No crash or stack trace visible to user
- ✅ Application remains responsive

**Validation**:
```bash
# Check logs:
# "No cameras found"
# "Error displayed to user: No camera detected"
```

### Scenario 4: Resource Cleanup (FR-005)

**Test Steps**:
1. Run application with camera connected
2. Camera feed displays successfully
3. Close browser tab
4. Wait 2 seconds
5. Check camera status

**Expected Results**:
- ✅ Camera resources released (LED off if camera has indicator)
- ✅ Can run `cv_grab.py` immediately (camera available)
- ✅ No "device busy" errors

**Validation**:
```bash
# After closing browser:
python spec/python_demo/cv_grab.py
# Should open successfully (camera not locked)
```

### Scenario 5: Localhost-Only Access (FR-012)

**Test Steps**:
1. Run application
2. Try accessing from:
   - http://127.0.0.1:7860 ✅ (should work)
   - http://localhost:7860 ✅ (should work)
   - http://[local-ip]:7860 ❌ (should fail)
   - http://[public-ip]:7860 ❌ (should fail)

**Expected Results**:
- ✅ Works: 127.0.0.1 and localhost
- ✅ Fails: External IP access

**Validation**:
```bash
# Check Gradio launch config:
# server_name="127.0.0.1"
# share=False
```

## Performance Validation

### Frame Rate Check
```bash
# Enable debug logging (add to main.py):
# logging.basicConfig(level=logging.DEBUG)

# Run and observe logs:
# Should see frame timestamps showing target FPS
# "Frame captured: seq=123, fps=60.1"
```

### Latency Measurement
```bash
# Wave hand in front of camera
# Observe delay between motion and screen update
# Should be < 100ms (subjectively imperceptible)
```

## Troubleshooting

### Camera Not Found
```bash
# List connected cameras
python -c "import spec.python_demo.mvsdk as mvsdk; print(mvsdk.CameraEnumerateDevice())"

# Check permissions (Linux)
sudo usermod -a -G video $USER
```

### Low Frame Rate
```bash
# Check CPU usage
top -o cpu

# Reduce camera resolution in camera settings
# Or: check camera capabilities for max FPS
```

### "Port Already in Use"
```bash
# Kill existing Gradio process
lsof -ti:7860 | xargs kill -9

# Or: use different port
python src/main.py --port 7861
```

## Success Criteria

Application is working correctly when:
1. ✅ Camera feed displays immediately on interface load
2. ✅ Video updates smoothly at camera's max FPS
3. ✅ Second viewer is blocked with clear message
4. ✅ Resources released properly on disconnect
5. ✅ Error messages are user-friendly (no stack traces)
6. ✅ Works with both color and mono cameras
7. ✅ Only accessible from localhost

## Next Steps

After quickstart validation:
1. Run full test suite: `pytest tests/`
2. Check code coverage: `pytest --cov=src tests/`
3. Review performance: `python tests/benchmark.py`

## Development Workflow

**TDD Cycle** (from constitution):
1. Write test (see `tests/integration/test_camera_ui_flow.py`)
2. Get user approval on test
3. Run test (should fail - red)
4. Implement feature
5. Run test (should pass - green)
6. Refactor if needed
7. Repeat

Example:
```bash
# 1. Write test for camera initialization
# 2. Run: pytest tests/unit/test_camera_device.py
# 3. Implement in src/camera/device.py
# 4. Run: pytest tests/unit/test_camera_device.py
# 5. Verify: all green
```

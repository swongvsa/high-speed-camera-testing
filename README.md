# High-Speed Camera Testing

Live camera feed display using Gradio web interface and MindVision MVSDK.  
Showcases camera's maximum FPS and native resolution for demos and presentations.

## Features

- ✅ Live camera feed at native resolution and maximum FPS
- ✅ Auto-start streaming on page load
- ✅ Single-viewer enforcement (exclusive camera access)
- ✅ Localhost-only access for security
- ✅ Friendly error messages for camera issues
- ✅ Automatic resource cleanup on disconnect
- ✅ Support for both color and monochrome cameras
- ✅ Works with USB and GigE Vision cameras
- ✅ Exposure control (manual and auto modes)
- ✅ Raw, unprocessed camera feed for maximum performance

## Installation

```bash
# 1. Install dependencies with uv (recommended)
uv sync

# OR with pip
pip install -e .[dev]

# 2. Verify SDK is present
ls spec/macsdk*/lib/*.dylib    # macOS
ls spec/linuxSDK/lib/*.so      # Linux
```

## Quick Start

### Step 1: Configure Camera IP (GigE Cameras Only)

**For GigE Vision cameras**, ensure your network adapter is on the same subnet as the camera:

```bash
# 1. Check camera's default IP (usually 169.254.x.x)
# Default MindVision camera IP: 169.254.22.149

# 2. Configure your Ethernet adapter:
#    - IP Address: 169.254.22.100 (any IP in 169.254.x.x range, but not .149)
#    - Subnet Mask: 255.255.0.0
#    - Gateway: Leave empty

# 3. Verify connectivity
ping 169.254.22.149

# 4. Test camera detection
uv run python main.py --camera-ip 169.254.22.149 --check
```

**macOS Network Setup:**
1. System Settings → Network → Ethernet (or Thunderbolt Ethernet)
2. Click "Details" → TCP/IP tab
3. Configure IPv4: Manually
4. Set IP Address: `169.254.22.100`
5. Subnet Mask: `255.255.0.0`
6. Click "OK" and "Apply"

**For USB cameras**, skip this step—they're auto-detected.

### Step 2: Run the Gradio UI

```bash
# Start the application (use uv run to ensure all dependencies are loaded)
uv run python main.py

# For GigE cameras, specify the camera IP
uv run python main.py --camera-ip 169.254.22.149

# Custom port (optional)
uv run python main.py --port 8080
```

### Step 3: Access the Web Interface

Open your browser to: **http://127.0.0.1:7860**

- ✅ Camera feed displays automatically
- ✅ Only one viewer allowed at a time
- ✅ Close browser tab to release camera

That's it! You're now streaming live video from your high-speed camera. 🎥

---

## Hardware Requirements

**Camera**: MindVision high-speed camera (USB or GigE)  
**Platform**: macOS (tested) or Linux  
**Network** (GigE only): Ethernet adapter on same subnet as camera

## Usage

### Start the Application

**Important:** Use `uv run` to ensure all dependencies are available:

```bash
# Default: Auto-detect camera, start on port 7860
uv run python main.py

# Specify camera IP (GigE cameras)
uv run python main.py --camera-ip 169.254.22.149

# Custom port
uv run python main.py --port 8080

# Test camera connectivity only
uv run python main.py --camera-ip 169.254.22.149 --check
```

**Alternative:** If using pip instead of uv, activate your virtual environment first:
```bash
source .venv/bin/activate  # or your venv path
python main.py
```

### Access the Interface

Open browser to: **http://127.0.0.1:7860**

- Camera feed displays automatically
- Only one viewer allowed at a time
- Close browser to release camera

### Exposure Control

The UI includes manual and automatic exposure control:

1. **Auto Exposure** - Check the "Auto Exposure" box for automatic brightness adjustment
2. **Manual Exposure** - Uncheck Auto Exposure and use the Shutter Speed slider:
   - Fast motion: Use shorter exposure (1-10ms) to freeze motion
   - Low light: Use longer exposure (30-100ms) for brighter image
   - Default: 30ms (good balance for most scenarios)

### Command Reference

```bash
uv run python main.py --help           # Show all options
uv run python main.py                  # Start with auto-detected camera
uv run python main.py --check          # Test camera without starting UI
uv run python main.py --port 7861      # Use custom port
```

## Troubleshooting

### Camera Not Found

```bash
# List connected cameras
python -c "from src.lib import mvsdk; print(mvsdk.CameraEnumerateDevice())"

# Check SDK installation
python -c "from src.lib import mvsdk; print(mvsdk.__file__)"
```

### Error -37: Network Send Error (GigE Cameras)

Camera detected but initialization fails. **See TROUBLESHOOTING.md** for detailed diagnosis.

**Quick fixes**:
1. Set network adapter IP to same subnet as camera (169.254.x.x)
2. Ping camera to verify reachability: `ping 169.254.22.149`
3. Disable firewall temporarily: `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off`
4. Test with camera vendor's demo software first

### "Camera Already in Use"

Another application is using the camera. Close other programs and try again.

```bash
# On macOS, check for processes using camera
lsof | grep -i camera

# Kill other camera processes if needed
```

### Low Frame Rate

- Check CPU usage (Task Manager / Activity Monitor)
- Reduce camera resolution in camera settings
- Close other applications
- For GigE: Verify network adapter MTU settings (may need jumbo frames)

### Improved Frame Rate

After removing processing pipelines, you should see:
- **25-30 FPS** (vs. 10-15 FPS with processing)
- **Lower CPU usage** (60-70% reduction)
- **Faster startup** (2-3 seconds vs. 5-10 seconds)

If frame rate is still low:
- Check CPU usage (Activity Monitor)
- Close other applications
- For GigE cameras: Verify network adapter MTU settings

### Port Already in Use

```bash
# Find process using port 7860
lsof -ti:7860

# Kill the process
kill -9 $(lsof -ti:7860)

# Or use different port
python main.py --port 7861
```

## Development

### Project Structure

```
src/
├── camera/      # Camera hardware interaction
├── ui/          # Gradio web interface
└── lib/         # MVSDK integration

tests/
├── contract/    # Contract tests (TDD)
├── unit/        # Unit tests
└── integration/ # Integration tests
```

### Running Tests

```bash
# All tests (85 tests)
pytest tests/ -v

# Contract tests only
pytest tests/contract/ -v

# With coverage
pytest --cov=src --cov-report=html tests/

# Single test
pytest tests/unit/test_errors.py::test_no_device_found_message -v
```

### Code Quality

```bash
# Lint and format checks
ruff check src tests

# Auto-fix formatting
ruff format src tests
```

### Documentation

**Application Documentation**:
- **Implementation Plan**: `specs/001-using-gradio-as/plan.md`
- **Data Model**: `specs/001-using-gradio-as/data-model.md`
- **API Contracts**: `specs/001-using-gradio-as/contracts/`
- **Quickstart Guide**: `specs/001-using-gradio-as/quickstart.md`
- **Task Breakdown**: `specs/001-using-gradio-as/tasks.md`
- **Troubleshooting**: `TROUBLESHOOTING.md`

**SDK Documentation**:
- **📖 SDK Implementation Reference**: `SDK_REFERENCE.md` - How we implement the MindVision SDK
- **Official Spec**: `spec/llm.txt` - MindVision SDK Specification v2.4 (English, AI-optimized)
- **Official Manual**: `spec/manual.txt` - Full SDK manual (Chinese)
- **Python Examples**: `spec/python_demo/` - Reference implementations
- **SDK Binaries**: `spec/Mac_sdk_m1(250120)/` (macOS M1+), `spec/macsdk(240831)/` (macOS Intel)

## Security

- **Localhost only**: Server binds to 127.0.0.1 (no external access)
- **No public sharing**: Gradio sharing is disabled
- **Single viewer**: Camera access restricted to one user

## Performance

Implementation follows MindVision SDK best practices (see `SDK_REFERENCE.md`):

- **Frame rate**: Maximum FPS via `CameraSetFrameSpeed(2)` high-speed mode
- **Latency**: <100ms target frame delay
- **Resolution**: Native camera resolution (no downsampling)
- **Zero-copy**: 16-byte aligned buffers with `np.frombuffer()` for SIMD optimization
- **CPU efficiency**: Manual exposure, minimal ISP processing
- **Memory**: Aligned allocation with proper cleanup

## License

See project license file.

## Support

For camera hardware issues, consult:
1. `TROUBLESHOOTING.md` - Common problems and solutions
2. `spec/manual.txt` - Complete SDK documentation
3. Camera manufacturer support
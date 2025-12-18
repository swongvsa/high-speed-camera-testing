# High-Speed Camera Testing

Live camera feed display using Gradio web interface and MindVision MVSDK.  
Showcases camera's maximum FPS and native resolution for demos and presentations.

## For Python Beginners

If you're new to Python, this guide will help you set up the environment step by step. Python is a programming language, and this project runs as a Python application. We'll use a "virtual environment" to keep dependencies isolated.

### Prerequisites

- Python 3.12+ (The project targets Python 3.13, but 3.12+ is supported).
- **Recommended**: [uv](https://docs.astral.sh/uv/) - a fast Python package and version manager.

### Setting Up the Environment (Recommended: uv)

We recommend using `uv` for the fastest and most reliable setup. It can automatically manage Python versions and virtual environments for you.

1. **Install uv**:

   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Install Python via uv**:

   ```bash
   uv python install 3.13
   ```

3. **Sync Project**:

   ```bash
   uv sync
   ```

   This automatically creates a virtual environment and installs all dependencies exactly as specified in `uv.lock`.

4. **Run the App**:

   ```bash
   uv run python main.py
   ```

---

### Alternative: Manual Setup (pip)

If you prefer using standard Python tools:

1. **Install Python**: Download and install Python 3.12+ from [python.org](https://www.python.org/downloads/).

2. **Create the virtual environment**:

   ```bash
   python -m venv .venv
   ```

3. **Activate it**:
   - **macOS/Linux**: `source .venv/bin/activate`
   - **Windows**: `.venv\Scripts\activate`

4. **Install Dependencies**:

   ```bash
   pip install -e .[dev]
   ```

### Deactivating the Environment

When done, run `deactivate` in the terminal (if using the manual setup).

Now proceed to the main installation steps below.

## 🚀 Getting Started Checklist

1. [ ] **Connect Hardware**: Plug in your USB or GigE camera.
2. [ ] **Setup Environment**: Run `uv sync` (recommended) or follow the [Manual Setup](#alternative-manual-setup-pip).
3. [ ] **Configure IP** (GigE only): Ensure your network adapter is on the same subnet (e.g., `169.254.22.100`).
4. [ ] **Test Connection**: Run `python main.py --check` to verify the SDK detects your camera.
5. [ ] **Launch UI**: Run `python main.py` and open `http://127.0.0.1:7860`.

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
# Verify SDK is present (after cloning/downloading the repo)
ls spec/Mac_sdk_m1*/lib/*.dylib    # macOS (M1/M2/M3)
```

**Note:** The MindVision SDK binaries for macOS are included in the `spec/` directory. For Linux or Intel-based Macs, please consult the `spec/manual.txt` or contact support for the appropriate binaries if they are not pre-installed.

## Quick Start

### Step 1: Configure Camera IP (GigE Cameras Only)

**Important for GigE Vision Cameras:** These cameras use link-local IP addressing (APIPA) by default, which means they auto-assign an IP in the 169.254.x.x range if no DHCP server is available. Your computer's Ethernet adapter must be on the same subnet (169.254.0.0/16) to communicate with the camera. USB cameras do not require this setup—they are plug-and-play.

#### Why This Setup?

- GigE cameras don't use your regular home/office network (which is usually 192.168.x.x or similar).
- They rely on direct Ethernet connection with link-local IPs to avoid configuration conflicts.
- Default camera IP: 169.254.22.149 (confirm yours using the camera's utility software if different).

#### Step-by-Step IP Configuration

1. **Connect the Hardware:**
   - Plug the Ethernet cable from the camera directly to your computer's Ethernet port (or via a switch if multiple devices).
   - Do NOT connect to a router with DHCP—use a direct connection.

2. **Find the Camera's IP (if not default):**

   - Use the MindVision camera configuration tool (included with SDK) or run:

     ```bash
     python -c "from src.lib import mvsdk; print(mvsdk.CameraEnumerateDevice())"
     ```

   - Look for the IP in the output (e.g., 169.254.22.149).

3. **Configure Your Computer's Ethernet Adapter:**
   - **macOS:**
     1. Go to System Settings → Network.
     2. Select Ethernet (or Thunderbolt Ethernet) → Details... → TCP/IP tab.
     3. Configure IPv4: Manually.
     4. IP Address: 169.254.22.100 (choose any unused IP in 169.254.x.x, but avoid the camera's IP like .149).
     5. Subnet Mask: 255.255.0.0.
     6. Router/Gateway: Leave blank.
     7. Click OK → Apply.
   
    - **Windows**:
      1. Open Settings → Network & Internet → Ethernet → Change adapter options.
      2. Right-click Ethernet → Properties → Internet Protocol Version 4 (TCP/IPv4) → Properties.
      3. Select "Use the following IP address".
      4. IP Address: 169.254.22.100.
      5. Subnet Mask: 255.255.0.0.
      6. Default Gateway: Leave blank.
      7. Click OK.

    - **Linux (Ubuntu example)**:
      1. Edit `/etc/netplan/01-netcfg.yaml` (or similar).
      2. Set: addresses: [169.254.22.100/16].
      3. Apply: `sudo netplan apply`.


4. **Verify Connectivity**:

   ```bash
   ping 169.254.22.149  # Replace with your camera's IP
   ```

   - You should see replies. If not, check cables, firewall, or IP conflicts.

5. **Test Camera Detection**:

   ```bash
   python main.py --camera-ip 169.254.22.149 --check
   ```
   - Success: "Camera initialized successfully".
   - Failure: Check IP setup or SDK installation.

**For USB Cameras:** No IP configuration needed—plug in and proceed to Step 2.

**Revert Network Settings:** After use, reset your Ethernet adapter to "Obtain IP automatically" to restore normal internet access.

### Step 2: Run the Gradio UI

Ensure your virtual environment is activated (see "For Python Beginners" above).

```bash
# Start the application
python main.py

# For GigE cameras, specify the camera IP
python main.py --camera-ip 169.254.22.149

# Custom port (optional)
python main.py --port 8080

# Test camera connectivity only
python main.py --camera-ip 169.254.22.149 --check
```

**Using uv (if installed):**
Replace `python` with `uv run` for faster execution, e.g., `uv run python main.py`.

### Step 3: Access the Web Interface

Open your browser to: [http://127.0.0.1:7860](http://127.0.0.1:7860)

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

**Important:** Activate your virtual environment first (see "For Python Beginners").

```bash
# Default: Auto-detect camera, start on port 7860
python main.py

# Specify camera IP (GigE cameras)
python main.py --camera-ip 169.254.22.149

# Custom port
python main.py --port 8080

# Test camera connectivity only
python main.py --camera-ip 169.254.22.149 --check
```

### Access the Interface

Open browser to: [http://127.0.0.1:7860](http://127.0.0.1:7860)

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
python main.py --help           # Show all options
python main.py                  # Start with auto-detected camera
python main.py --check          # Test camera without starting UI
python main.py --port 7861      # Use custom port
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

- On macOS, check for processes using camera:
  ```bash
  lsof | grep -i camera
  ```
- Kill other camera processes if needed.

### Low Frame Rate

- **Check CPU usage**: Ensure no other heavy processes are running.
- **MTU Settings**: For GigE cameras, verify if your network adapter supports Jumbo Frames (MTU 9000).
- **Network Congestion**: Use a direct Ethernet connection; avoid busy office networks.
- **Lighting**: In manual exposure mode, very long exposure times (e.g., >40ms) will naturally limit the maximum possible FPS.

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

```text
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

## Documentation

### Application Docs

- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and network setup
- [SDK Implementation Reference](SDK_REFERENCE.md) - Deep dive into how we use the MindVision SDK
- [Exposure Controls](EXPOSURE_CONTROLS.md) - Details on manual vs auto exposure
- [Implementation Plan](specs/001-using-gradio-as/plan.md) - Original design specifications

### SDK Resources (under `spec/`)

- `llm.txt` - AI-optimized SDK Specification v2.4 (English)
- `manual.txt` - Full SDK technical manual (Chinese)
- `python_demo/` - Reference Python implementations from the vendor

## Security

- **Localhost only**: Server binds to 127.0.0.1 (no external access)
- **No public sharing**: Gradio sharing is disabled
- **Single viewer**: Camera access restricted to one user

## Performance & Optimization

This implementation follows MindVision SDK best practices (see `SDK_REFERENCE.md`) to deliver maximum performance:

- **Zero-copy Capture**: Uses aligned memory buffers with `ctypes` and `np.frombuffer()` to create NumPy views directly on SDK memory, avoiding expensive data copying.
- **High-speed Mode**: Automatically enables `CameraSetFrameSpeed(2)` to prioritize frame rate over ISP processing.
- **Minimal Latency**: <100ms end-to-end latency by bypassing unnecessary image processing pipelines.
- **Native Resolution**: Streams at the camera's full native resolution for maximum detail.
- **Efficient UI**: Gradio interface optimized for streaming high-FPS video feeds with minimal overhead.

### Recent Improvements

We recently refactored the capture pipeline to achieve:

- **Higher Frame Rates**: Up to **25-30 FPS** (previously 10-15 FPS).
- **Lower CPU Usage**: ~60% reduction in processing overhead.
- **Faster Startup**: App initializes in 2-3 seconds.
- **Robust Reconnection**: Automatically detects and recovers from transient network timeouts.

## License

See project license file.

## Support

For camera hardware issues, consult:

1. `TROUBLESHOOTING.md` - Common problems and solutions
2. `spec/manual.txt` - Complete SDK documentation
3. Camera manufacturer support


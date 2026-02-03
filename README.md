# High-Speed Camera Testing

Live camera feed display using Gradio web interface and MindVision MVSDK.  
Showcases camera's maximum FPS and native resolution for demos and presentations.

## Quick Start (Recommended)

The easiest way to get started is using the provided deployment script:

```bash
# Clone or download the repository
cd high-speed-camera-testing

# Run the deployment script
./deploy.sh
```

The script will:
1. Check for Python 3.13+ (install via uv if missing)
2. Install uv (if not present)
3. Create a project-specific virtual environment
4. Install all dependencies
5. Start the application

**That's it!** Open http://localhost:7860 in your browser.

### Deployment Commands

```bash
./deploy.sh start      # Start the app
./deploy.sh stop       # Stop the app
./deploy.sh logs       # View application logs
./deploy.sh install    # Install dependencies only
./deploy.sh clean      # Remove venv and start fresh
./deploy.sh check      # Check dependencies only
```

## For Python Beginners

If you're new to Python or want to understand what's happening behind the scenes, here's a step-by-step guide.

### Prerequisites

- Python 3.13+ (The deployment script can install this for you)
- [uv](https://docs.astral.sh/uv/) - A fast Python package and version manager

### What the Script Does

The `deploy.sh` script automates the setup process:

1. **Python Management**: Uses `uv` to download and install Python 3.13 if not present
2. **Version Pinning**: Creates a `.python-version` file to lock the project to Python 3.13
3. **Virtual Environment**: Creates an isolated Python environment in `./.venv`
4. **Dependencies**: Installs all required packages from `pyproject.toml`
5. **Process Management**: Runs the app in the background and tracks it with a PID file

### Manual Setup (Alternative)

If you prefer to set up manually:

1. **Install uv**:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install and Pin Python**:

   ```bash
   uv python install 3.13
   uv python pin 3.13
   ```

3. **Create Virtual Environment**:

   ```bash
   uv venv .venv
   ```

4. **Install Dependencies**:

   ```bash
   uv pip install -e "."
   ```

5. **Run the App**:

   ```bash
   source .venv/bin/activate
   python main.py
   ```

### Understanding the Virtual Environment

The virtual environment (`.venv/`) is an isolated Python installation just for this project. It:
- Keeps project dependencies separate from your system Python
- Allows different projects to use different package versions
- Makes the project portable and reproducible

**To activate manually**:
- macOS/Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

**To deactivate**: Type `deactivate` in your terminal.

## 🚀 Getting Started Checklist

1. [ ] **Connect Hardware**: Plug in your USB or GigE camera.
2. [ ] **Run Deployment Script**: Execute `./deploy.sh` to set up everything automatically.
3. [ ] **Configure IP** (GigE only): Ensure your network adapter is on the same subnet (e.g., `169.254.22.100`).
4. [ ] **Test Connection**: Run `./deploy.sh` and the script will verify camera connectivity.
5. [ ] **Access UI**: Open `http://localhost:7860` in your browser.

## Features

- ✅ Live camera feed at native resolution and maximum FPS
- ✅ High-speed recording up to **1594+ FPS** with slow-motion playback
- ✅ ROI (Region of Interest) presets for bandwidth optimization
- ✅ Decoupled capture architecture (background thread for max performance)
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

### One-Line Setup

```bash
./deploy.sh
```

This interactive script handles everything:
- Installs Python 3.13 (if needed)
- Installs uv package manager (if needed)
- Creates virtual environment
- Installs dependencies
- Starts the application

### Manual Verification

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

### Step 2: Start the Application

Use the deployment script (it handles the virtual environment automatically):

```bash
# Start with interactive menu
./deploy.sh

# Or start directly
./deploy.sh start

# Specify camera IP (GigE cameras)
./deploy.sh start
# Then edit .env to set CAMERA_IP=169.254.22.149

# Test camera connectivity only
source .venv/bin/activate
python main.py --camera-ip 169.254.22.149 --check
```

### Step 3: Access the Web Interface

Open your browser to: [http://localhost:7860](http://localhost:7860)

- ✅ Camera feed displays automatically
- ✅ Only one viewer allowed at a time
- ✅ Close browser tab to release camera

**To stop the app:**
```bash
./deploy.sh stop
```

That's it! You're now streaming live video from your high-speed camera. 🎥

---

## Hardware Requirements

**Camera**: MindVision high-speed camera (USB or GigE)  
**Platform**: macOS (tested) or Linux  
**Network** (GigE only): Ethernet adapter on same subnet as camera

## Usage

### Start the Application

**Recommended:** Use the deployment script:

```bash
# Start with interactive menu
./deploy.sh

# Start directly
./deploy.sh start

# Stop the app
./deploy.sh stop

# View logs
./deploy.sh logs
```

**Manual (if preferred):**
Ensure your virtual environment is activated first:

```bash
source .venv/bin/activate

# Default: Auto-detect camera, start on port 7860
python main.py

# Specify camera IP (GigE cameras)
python main.py --camera-ip 169.254.22.149

# Custom port
python main.py --port 8080

# Test camera connectivity only
python main.py --camera-ip 169.254.22.149 --check
```

### Configuration

The app reads configuration from `.env` file:

```bash
CAMERA_IP=169.254.22.149      # Your camera's IP address
GRADIO_PORT=7860              # Web interface port
```

The deployment script creates this file automatically on first run.

### Access the Interface

Open browser to: [http://127.0.0.1:7860](http://127.0.0.1:7860)

- Camera feed displays automatically
- Only one viewer allowed at a time
- Close browser to release camera

### High-Speed Controls

The UI includes advanced controls for high-speed recording:

1. **ROI Presets** - Select resolution for bandwidth optimization:
   - Full Res (816×624) - Standard recording
   - 720p (816×480) - HD video capture  
   - Half (816×312) - Medium speed events
   - Quarter (816×156) - Fast motion analysis
   - Extreme (816×64) - Ultra high-speed capture (1594+ FPS)

2. **Frame Rate Control**:
   - **Target FPS** - Set desired capture frame rate (30-1600)
   - **Playback FPS** - Output frame rate for slow-motion (15-60)
   - **Shutter Speed** - Exposure time (0.1-100ms)
   - **Analog Gain** - Amplification for short exposures

3. **Slow-Motion Recording**:
   - Enable recording with "Start Recording" button
   - Set capture duration and playback speed
   - System saves slow-motion video automatically

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

## Deployment Script Reference

The `deploy.sh` script provides a complete deployment solution:

### Commands

| Command | Description |
|---------|-------------|
| `./deploy.sh` | Interactive menu - choose start/stop/logs/install/clean |
| `./deploy.sh start` | Start the application |
| `./deploy.sh stop` | Stop the running application |
| `./deploy.sh logs` | View application logs in real-time |
| `./deploy.sh install` | Install/update dependencies only |
| `./deploy.sh clean` | Remove virtual environment and start fresh |
| `./deploy.sh check` | Verify all dependencies are installed |

### What It Does

1. **Python Management**: Uses `uv` to install Python 3.13 if not present
2. **Version Pinning**: Creates `.python-version` file to lock Python version
3. **Virtual Environment**: Creates isolated environment at `./.venv`
4. **Dependencies**: Installs from `pyproject.toml` into the venv
5. **Process Management**: Tracks running app with PID file (`.app.pid`)
6. **Configuration**: Creates `.env` file on first run

### Environment Variables

Set these in your `.env` file:

- `CAMERA_IP` - Camera IP address (for GigE cameras)
- `GRADIO_PORT` - Web interface port (default: 7860)

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

First, ensure your virtual environment is activated:

```bash
source .venv/bin/activate
```

Then run tests:

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

Ensure virtual environment is activated:

```bash
source .venv/bin/activate

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

- **High-Speed Recording**: Up to **1600 FPS** with dedicated recorder for slow-motion playback
- **ROI Support**: Region of Interest presets (Full, 720p, Half, Quarter, Extreme) for bandwidth optimization
- **Decoupled Architecture**: Background capture thread enables camera to run at max FPS while UI displays at 25 FPS
- **Automatic Exposure/FPS Coordination**: System automatically adjusts exposure when FPS increases
- **Lower CPU Usage**: ~60% reduction in processing overhead.
- **Faster Startup**: App initializes in 2-3 seconds.
- **Robust Reconnection**: Automatically detects and recovers from transient network timeouts.

## High-Speed Recording Guide

### Maximum FPS Achievement

To achieve the highest frame rates (up to 1594+ FPS):

1. **Select Extreme ROI**: Use "Extreme High-Speed" preset (816x64 pixels)
2. **Set Shutter Speed**: 0.5ms or lower for minimal motion blur
3. **Adjust Analog Gain**: Compensate for short exposure brightness
4. **Target FPS**: Set to 1600 (camera will auto-limit to maximum achievable)
5. **Playback FPS**: 30 for 53x slow-motion effect

### ROI Presets and Maximum FPS

| Preset | Resolution | Max FPS | Use Case |
|--------|------------|---------|----------|
| Full Res | 816×624 | ~120 | Standard recording |
| 720p | 816×480 | ~200 | HD video capture |
| Half | 816×312 | ~400 | Medium speed events |
| Quarter | 816×156 | ~800 | Fast motion analysis |
| Extreme | 816×64 | 1594+ | Ultra high-speed capture |

### Slow-Motion Recording

1. **Enable Recording**: Click "Start Recording" in the UI
2. **Set Duration**: Choose capture duration (1-60 seconds)
3. **Configure Slow-Motion**: Set Target FPS (capture) and Playback FPS (output)
4. **Save Video**: System automatically saves slow-motion .mp4 file

### Performance Tips

- **GigE Bandwidth**: Lower resolution reduces network load, enabling higher FPS
- **CPU Usage**: Background capture minimizes UI impact
- **Storage**: High-speed recordings create large files - ensure adequate disk space
- **Lighting**: Use bright lighting for short exposures at high FPS

## License

See project license file.

## Support

For camera hardware issues, consult:

1. `TROUBLESHOOTING.md` - Common problems and solutions
2. `spec/manual.txt` - Complete SDK documentation
3. Camera manufacturer support


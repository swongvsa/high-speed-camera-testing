# Project Overview: High-Speed Camera Testing

## Purpose
Display live camera feed from high-speed camera through Gradio web interface for demos and presentations. The system uses MVSDK Python bindings to capture frames from camera and stream them to a localhost web UI, showcasing camera's maximum FPS and native resolution capabilities.

## Tech Stack
- **Language**: Python 3.13 (requires >=3.12)
- **Web Framework**: Gradio (for web UI)
- **Camera SDK**: MVSDK (bindings in spec/python_demo/mvsdk.py, binaries in spec/macsdk(240831)/)
- **Image Processing**: OpenCV, NumPy
- **C Bindings**: ctypes
- **Testing**: pytest with pytest-mock, pytest-cov
- **Linting/Formatting**: ruff
- **Platform**: macOS (Darwin), with Linux support

## Project Structure
```
src/
├── camera/              # Camera hardware interaction
│   ├── __init__.py
│   ├── device.py        # Camera enumeration, initialization, cleanup
│   └── video_frame.py   # Frame capture and processing
├── ui/                  # Gradio web interface
│   ├── __init__.py
│   └── app.py           # Gradio app setup and streaming logic
├── lib/                 # SDK integration
│   ├── __init__.py
│   └── mvsdk.py         # MVSDK Python bindings
└── session/             # Session management
    └── __init__.py

tests/
├── integration/         # End-to-end tests
├── unit/                # Unit tests
├── contract/            # Contract tests
└── fixtures/            # Test fixtures

specs/                   # Feature specifications and plans
main.py                  # Application entry point
pyproject.toml           # Dependencies and project config
```

## Key Features
- Live camera feed streaming at maximum FPS
- Native camera resolution display
- Single viewer restriction (one user at a time)
- Localhost-only access for security
- Proper camera resource cleanup
- Support for both color and monochrome cameras
- Error handling for camera disconnection/unavailability

## Constraints
- Single camera support
- Single concurrent viewer
- Localhost access only
- Demo/presentation use case
- Minimal latency (<100ms frame delay target)
# Suggested Commands for Development

## Installation and Setup
```bash
# Install dependencies
pip install gradio opencv-python numpy

# Install dev dependencies (for testing/linting)
pip install pytest pytest-mock pytest-cov ruff

# Verify camera connection (macOS)
python spec/python_demo/cv_grab.py
```

## Running the Application
```bash
# Start the camera viewer
python src/main.py

# Run with custom port (if 7860 is busy)
python src/main.py --port 7861
```

## Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/

# Run single test file
pytest tests/unit/test_camera_device.py
```

## Code Quality
```bash
# Lint code
ruff check .

# Format code
ruff format .

# Fix auto-fixable issues
ruff check --fix .
```

## Development Workflow
```bash
# TDD Cycle Example:
# 1. Write test
# 2. Run test (should fail)
pytest tests/unit/test_camera_device.py::test_camera_initialization

# 3. Implement feature in src/camera/device.py
# 4. Run test (should pass)
pytest tests/unit/test_camera_device.py::test_camera_initialization

# 5. Check code quality
ruff check src/camera/device.py
ruff format src/camera/device.py
```

## Troubleshooting
```bash
# List connected cameras
python -c "import spec.python_demo.mvsdk as mvsdk; print(mvsdk.CameraEnumerateDevice())"

# Check permissions (Linux)
sudo usermod -a -G video $USER

# Kill existing Gradio process
lsof -ti:7860 | xargs kill -9

# Check CPU usage
top -o cpu
```

## System Commands (macOS/Darwin)
```bash
# List files
ls -la

# Change directory
cd src/

# Find files
find . -name "*.py" -type f

# Search in files
grep -r "camera" src/

# Check processes
ps aux | grep python

# Kill process
kill -9 <PID>
```
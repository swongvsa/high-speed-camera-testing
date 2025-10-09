# Code Style and Conventions

## Python Version
- Python 3.13 (minimum 3.12)
- Follow PEP 8 standards
- Use type hints where appropriate

## Linting and Formatting
- **Linter**: ruff
- **Configuration**: ruff.toml in project root
- **Line length**: 100 characters
- **Selected rules**: E (pycodestyle), F (Pyflakes), I (isort), N (pep8-naming), W (pycodestyle warnings)
- **Ignored rules**: E501 (line too long, handled by formatter)

## Naming Conventions
- **Modules**: lowercase_with_underscores (e.g., `camera_device.py`)
- **Classes**: PascalCase (e.g., `CameraDevice`)
- **Functions/Methods**: lowercase_with_underscores (e.g., `initialize_camera()`)
- **Variables**: lowercase_with_underscores (e.g., `frame_rate`)
- **Constants**: UPPERCASE_WITH_UNDERSCORES (e.g., `MAX_FRAME_RATE`)

## Code Structure
- **Imports**: Group by standard library, third-party, local modules
- **Docstrings**: Use triple quotes, describe purpose, parameters, return values
- **Error Handling**: Use specific exceptions, provide meaningful error messages
- **Logging**: Use Python's logging module for debug/info/error messages

## Project-Specific Patterns
- **Camera Integration**: Use MVSDK bindings through ctypes
- **Web Interface**: Gradio for UI, localhost-only access
- **Resource Management**: Proper cleanup of camera resources
- **Threading**: Careful with camera capture loops and UI updates
- **Testing**: Contract tests for interfaces, unit tests for components, integration tests for workflows

## File Organization
- **src/**: Main application code
  - `camera/`: Camera hardware interaction
  - `ui/`: Web interface components
  - `lib/`: Third-party integrations (SDK bindings)
  - `session/`: Session management
- **tests/**: Test code mirroring src/ structure
  - `unit/`: Unit tests
  - `integration/`: End-to-end tests
  - `contract/`: Interface contract tests
  - `fixtures/`: Test data and mocks

## Dependencies
- **Core**: gradio, numpy, opencv-python
- **Dev**: pytest, pytest-mock, pytest-cov, ruff
- **SDK**: MVSDK (provided in spec/, copied to src/lib/)

## Performance Considerations
- Minimize latency in camera feed (<100ms target)
- Efficient frame processing with NumPy/OpenCV
- Proper resource cleanup to avoid camera locks
- Single viewer restriction to manage resources
# Task Completion Checklist

After completing any development task (adding features, fixing bugs, refactoring), run these commands to ensure code quality and functionality:

## 1. Code Quality Checks
```bash
# Lint the code
ruff check .

# Format the code
ruff format .

# Fix auto-fixable issues
ruff check --fix .
```

## 2. Run Tests
```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=src tests/

# Ensure no regressions in key functionality
pytest tests/integration/
```

## 3. Manual Testing (if applicable)
```bash
# Test camera functionality (if hardware available)
python spec/python_demo/cv_grab.py

# Test application startup
python src/main.py
# Check that it starts without errors and shows expected output
```

## 4. Performance Validation (for camera-related changes)
```bash
# Check frame rate and latency
# Wave hand in front of camera and observe delay
# Should be < 100ms subjectively imperceptible

# Monitor CPU usage during streaming
top -o cpu
```

## 5. Documentation Update
- Update README.md if user-facing changes
- Update specs/ if requirements change
- Update this checklist if new validation steps needed

## Success Criteria
- ✅ All linting passes (ruff check . returns no errors)
- ✅ All tests pass (pytest tests/ exits with code 0)
- ✅ Code coverage maintained (>80% target)
- ✅ Application starts without errors
- ✅ Camera feed displays correctly (if hardware available)
- ✅ No resource leaks (camera releases properly on exit)

## Common Issues to Check
- Camera resource not released on application close
- Second viewer not properly blocked
- Error messages not user-friendly
- Performance degradation in frame rate
- Memory leaks in continuous streaming
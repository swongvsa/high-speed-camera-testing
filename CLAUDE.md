<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# high-speed-camera-testing Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-06

## Active Technologies
- Python 3.13 (from pyproject.toml) + Gradio (web UI framework), MVSDK (camera SDK at spec/python_demo/mvsdk.py), OpenCV/numpy (image processing), ctypes (C library bindings) (001-using-gradio-as)

## Project Structure
```
backend/
frontend/
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.13 (from pyproject.toml): Follow standard conventions

## Recent Changes
- 001-using-gradio-as: Added Python 3.13 (from pyproject.toml) + Gradio (web UI framework), MVSDK (camera SDK at spec/python_demo/mvsdk.py), OpenCV/numpy (image processing), ctypes (C library bindings)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
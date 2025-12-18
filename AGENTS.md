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

**Build & Test**:
- **Install deps**: `pip install -e .[dev]` (from repo root)
- **Run full tests**: `pytest tests/ -v`
- **Run a single test file**: `pytest tests/contract/test_camera_device_contract.py -q`
- **Run a single test case**: `pytest tests/contract/test_camera_device_contract.py::TestCameraDeviceContract::test_enumerate_returns_list -q`
- **Run tests matching expression**: `pytest -k "enumerate and camera" -q`
- **Run coverage**: `pytest --cov=src --cov-report=term --cov-report=html tests/`
- **Lint/format checks**: `ruff check src tests` (config in `ruff.toml`, line-length=100, double quotes)

**Quick commands**:
- `python main.py --help` - app entrypoint usage
- `python -c "import src.lib.mvsdk as m; print(m.CameraEnumerateDevice())"` - SDK smoke test

**Style & Conventions**:
- **Python version**: Target Python 3.13 (use `pyproject.toml`).
- **Formatting**: Follow `ruff.toml` (line-length 100, double quotes). Keep imports grouped: stdlib, third-party, local (absolute imports preferred).
- **Typing**: Use type hints everywhere for public functions and dataclasses. Prefer `list[T]`, `tuple[T, U]`, and `-> None` when appropriate.
- **Dataclasses/entities**: Use `@dataclass(frozen=True)` for immutable value objects (e.g., `VideoFrame`). Validate inputs in `__post_init__` and raise `ValueError` on invalid data.
- **Naming**: `PascalCase` for classes, `snake_case` for functions/variables, `UPPER_SNAKE` for constants.
- **Error handling**: Define domain-specific exceptions (inherit from `Exception`), include an `error_code` when wrapping SDK errors; log errors and avoid raising from `__exit__()` (cleanup should not raise).
- **I/O & side-effects**: Keep side-effects (camera init/IO) behind clear APIs and use context managers for resource lifecycles.
- **Testing**: Use `pytest` + `pytest-mock`; write contract tests first (TDD). Use fixtures in `tests/fixtures/` and mock `src.lib.mvsdk` for hardware isolation.

**Repo context (discovered)**:
- **FEATURE_DIR**: `/Users/swong/dev/high-speed-camera-testing/specs/001-using-gradio-as`
- **AVAILABLE_DOCS**: `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md` (all under the FEATURE_DIR)

**Editor/Agent notes**:
- No `.cursor` or Copilot instruction files found; include Copilot/Cursor rules here if added.
- Keep changes minimal and follow existing repo patterns; run the single-test command above when validating a focused change.

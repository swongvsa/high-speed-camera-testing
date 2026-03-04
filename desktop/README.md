# High Speed Camera — macOS Desktop App

Packages the Gradio-based camera tool as a self-contained macOS `.app` / `.dmg` using Electron as a shell around the Python/Gradio server.

## How It Works

1. Electron starts and shows a splash screen.
2. It spawns the bundled Python 3.13 runtime with `main.py`.
3. It polls `http://localhost:7860` every 500 ms until Gradio responds.
4. The Gradio UI loads inside the Electron window (no separate browser tab).
5. Closing the window kills the Python subprocess cleanly.

---

## Prerequisites (build machine)

| Tool | Version | Install |
|------|---------|---------|
| Node.js | 20+ | https://nodejs.org |
| npm | bundled with Node | — |
| uv | any | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| libmvsdk.dylib (ARM64) | — | see below |

### libmvsdk.dylib placement

The ARM64 macOS MindVision SDK library must be placed at:

```
spec/macos_sdk_arm64/libmvsdk.dylib
```

The build script will fail with a clear error if it is missing.

---

## Build

Run from the **repo root**:

```bash
./desktop/scripts/build.sh
```

First run downloads `python-build-standalone` (~65 MB) and caches it at `desktop/.cache/`. Subsequent runs are faster.

Output files appear in `desktop/dist/`:

```
desktop/dist/
  High Speed Camera-1.0.0-arm64.dmg   ← distribute this
  mac-arm64/
    High Speed Camera.app              ← or drag directly to /Applications
```

---

## Install

1. Mount `High Speed Camera-1.0.0-arm64.dmg`
2. Drag **High Speed Camera.app** to `/Applications`
3. Double-click to launch — no terminal or Python installation needed

### Camera IP

Set `CAMERA_IP` in your shell environment before launching, or the app falls back to webcam mode:

```bash
CAMERA_IP=192.168.1.100 open /Applications/High\ Speed\ Camera.app
```

---

## Development Mode

```bash
cd desktop
npm install
# From repo root:
CAMERA_IP=192.168.1.100 npm --prefix desktop start
```

This runs Electron against your local Python environment (expects `python3` on PATH with project deps installed).

---

## Verification Checklist

- [ ] `./desktop/scripts/build.sh` completes without errors
- [ ] `.dmg` appears in `desktop/dist/`
- [ ] Mount DMG, drag to `/Applications`, double-click — app launches
- [ ] Gradio UI appears (no terminal window, no browser tab)
- [ ] Close window → `pgrep -f main.py` returns nothing
- [ ] Webcam fallback: launch with `CAMERA_IP=` unset — webcam mode works

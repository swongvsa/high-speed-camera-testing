# High Speed Camera — macOS Desktop App

Packages the FastAPI-based camera tool as a self-contained macOS `.app` using Electrobun (Bun/TypeScript main process + WKWebView UI).

## How It Works

1. The Electrobun main process (`desktop/src/bun/index.ts`) shows a splash screen.
2. It spawns the bundled Python 3.13 ARM64 runtime with `main.py`.
3. It polls `http://localhost:7860/api/status` every 500 ms until FastAPI responds.
4. The custom web UI loads via the `views://main` scheme — no browser URL bar, no separate tab.
5. Closing the window sends SIGTERM to Python, waits up to 10 s for any in-progress clip save to flush, then exits.

Clips are saved to `~/Movies/High Speed Camera/` so they persist across app updates.

---

## Prerequisites (build machine)

| Tool | Version | Install |
|------|---------|---------|
| bun | 1.x+ | `curl -fsSL https://bun.sh/install \| bash` |
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

Output files appear in `desktop/build/dev-macos-arm64/`:

```
desktop/build/dev-macos-arm64/
  High Speed Camera-dev.app    ← drag directly to /Applications
```

---

## Install

1. Drag **High Speed Camera-dev.app** to `/Applications`
2. Double-click to launch — no terminal or Python installation needed

> **First launch:** macOS may show "app from unidentified developer." Right-click → Open to bypass. The build script removes the `com.apple.quarantine` attribute from the bundled SDK library so the camera loads without an additional Gatekeeper prompt.

### Camera IP

Set `CAMERA_IP` in your shell environment before launching, or the app falls back to webcam mode:

```bash
CAMERA_IP=192.168.1.100 open /Applications/High\ Speed\ Camera-dev.app
```

---

## Development Mode

Run Python directly (no desktop build needed):

```bash
# From repo root
python main.py --port 7860
# Then open http://localhost:7860 in your browser
```

To run the full Electrobun dev build:

```bash
cd desktop
bun install
# Set devRepoRoot in electrobun.config.ts, then:
bun run dev
```

---

## Verification Checklist

- [ ] `./desktop/scripts/build.sh` completes without errors
- [ ] `.app` appears in `desktop/build/dev-macos-arm64/`
- [ ] Drag to `/Applications`, double-click — splash appears, then camera UI
- [ ] Camera UI loads (ROI presets, slowdown controls populated from `/api/config`)
- [ ] Live MJPEG preview visible (or placeholder if no camera connected)
- [ ] Save Clip → clip appears in `~/Movies/High Speed Camera/`
- [ ] Close window → `pgrep -f main.py` returns nothing
- [ ] Webcam fallback: launch with `CAMERA_IP=` unset — webcam mode works

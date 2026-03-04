#!/usr/bin/env bash
# desktop/scripts/build.sh
# Build the High Speed Camera macOS .app / .dmg
# Run from the repo root: ./desktop/scripts/build.sh
set -euo pipefail

# ─── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DESKTOP_DIR="$REPO_ROOT/desktop"
BUILD_DIR="$DESKTOP_DIR/build"
PYTHON_DIR="$BUILD_DIR/python"
APP_DIR="$PYTHON_DIR/app"
CACHE_DIR="$DESKTOP_DIR/.cache"

# Expected location of the macOS ARM64 SDK library
MVSDK_SRC="$REPO_ROOT/spec/macos_sdk_arm64/libmvsdk.dylib"

# python-build-standalone release to use
PBS_VERSION="20241016"
PBS_FILENAME="cpython-3.13.0+${PBS_VERSION}-aarch64-apple-darwin-install_only.tar.gz"
PBS_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PBS_VERSION}/${PBS_FILENAME}"
PBS_CACHE="$CACHE_DIR/$PBS_FILENAME"

# ─── Colours ────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}▶${NC} $*"; }
warn()    { echo -e "${YELLOW}⚠${NC}  $*"; }
error()   { echo -e "${RED}✗${NC}  $*" >&2; exit 1; }
ok()      { echo -e "${GREEN}✓${NC} $*"; }

# ─── Step 1: Prerequisites ───────────────────────────────────────────────────
info "Checking prerequisites…"

command -v node >/dev/null 2>&1 || error "node not found. Install Node.js 20+ from https://nodejs.org"
command -v npm  >/dev/null 2>&1 || error "npm not found. Install Node.js 20+ from https://nodejs.org"
command -v uv   >/dev/null 2>&1 || error "uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"

NODE_MAJOR=$(node --version | sed 's/v\([0-9]*\).*/\1/')
if [[ "$NODE_MAJOR" -lt 20 ]]; then
  error "Node.js 20+ required (found $(node --version))"
fi
ok "node $(node --version), npm $(npm --version), uv $(uv --version)"

# ─── Step 2: Check libmvsdk.dylib ───────────────────────────────────────────
info "Checking for libmvsdk.dylib (ARM64)…"
if [[ ! -f "$MVSDK_SRC" ]]; then
  error "libmvsdk.dylib not found at: $MVSDK_SRC
Place the macOS ARM64 build of libmvsdk.dylib at that path before building.
The library should be the ARM64 (Apple Silicon) variant from the MindVision SDK."
fi
ok "Found: $MVSDK_SRC"

# ─── Step 3: Download python-build-standalone (cached) ──────────────────────
mkdir -p "$CACHE_DIR"

if [[ -f "$PBS_CACHE" ]]; then
  ok "python-build-standalone cache hit: $PBS_CACHE"
else
  info "Downloading python-build-standalone $PBS_VERSION (~65 MB)…"
  curl -fSL --progress-bar "$PBS_URL" -o "$PBS_CACHE" \
    || error "Download failed. Check your internet connection."
  ok "Downloaded: $PBS_CACHE"
fi

# ─── Step 4: Extract Python runtime ─────────────────────────────────────────
info "Extracting Python runtime to $PYTHON_DIR…"
rm -rf "$PYTHON_DIR"
mkdir -p "$PYTHON_DIR"
tar -xzf "$PBS_CACHE" -C "$PYTHON_DIR" --strip-components=1
ok "Python runtime extracted"

PYTHON_BIN="$PYTHON_DIR/bin/python3"
[[ -x "$PYTHON_BIN" ]] || error "Extracted Python binary not found at $PYTHON_BIN"

# ─── Step 5: Install project dependencies ───────────────────────────────────
info "Installing Python dependencies into bundled runtime…"
uv pip install \
  --python "$PYTHON_BIN" \
  gradio \
  numpy \
  "opencv-python-headless" \
  || error "uv pip install failed"
ok "Dependencies installed"

# ─── Step 6: Copy application files ─────────────────────────────────────────
info "Copying application files to $APP_DIR…"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"

# Core entry point and source tree
cp "$REPO_ROOT/main.py"      "$APP_DIR/main.py"
cp "$REPO_ROOT/pyproject.toml" "$APP_DIR/pyproject.toml"
cp -r "$REPO_ROOT/src"       "$APP_DIR/src"

# Copy libmvsdk.dylib into the app directory
cp "$MVSDK_SRC" "$APP_DIR/libmvsdk.dylib"
chmod +x "$APP_DIR/libmvsdk.dylib"

ok "Application files copied"

# ─── Step 7: npm install + electron-builder ──────────────────────────────────
info "Installing npm dependencies…"
cd "$DESKTOP_DIR"
npm install --prefer-offline
ok "npm install complete"

info "Building Electron app (this may take a few minutes)…"
npm run build
ok "Build complete"

# ─── Done ────────────────────────────────────────────────────────────────────
DIST="$DESKTOP_DIR/dist"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Build succeeded!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Output:"
ls "$DIST"/*.dmg 2>/dev/null && true
ls -d "$DIST"/*.app 2>/dev/null && true
echo ""
echo "To install: mount the .dmg and drag 'High Speed Camera.app' to /Applications"

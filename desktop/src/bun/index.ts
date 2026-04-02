/**
 * High Speed Camera — Electrobun main process
 *
 * Lifecycle:
 *  1. Show splash window while Python/FastAPI starts.
 *  2. Load main UI immediately via views:// scheme.
 *  3. Spawn Python HTTP service, poll GET /api/status for readiness.
 *  4. Inject port into webview via URL parameter.
 *  5. Kill the Python subprocess when the window is closed.
 */

import { BrowserWindow, BuildConfig } from "electrobun/bun";
import { dirname, join } from "path";

// ─── Configuration ────────────────────────────────────────────────────────────

const PORTS = [7860, 7861, 7862];
const POLL_INTERVAL_MS = 500;
const STARTUP_TIMEOUT_MS = 15_000;

// ─── Path resolution (packed vs dev) ─────────────────────────────────────────

const appCodePath = join(dirname(process.execPath), "..", "Resources", "app");

const bundledPythonBin = join(appCodePath, "python", "bin", "python3");
const isPacked = await Bun.file(bundledPythonBin).exists();

const pythonBin = isPacked ? bundledPythonBin : "python3";

const buildConfig = await BuildConfig.get();
const devRepoRoot = (buildConfig.runtime as Record<string, string>)?.devRepoRoot;

if (!isPacked && !devRepoRoot) {
  console.error(
    "BuildConfig.runtime.devRepoRoot is missing — run `bun build` first or check electrobun.config.ts"
  );
  process.exit(1);
}

const appEntry = isPacked
  ? join(appCodePath, "python", "app", "main.py")
  : join(devRepoRoot, "main.py");

const bundlePath = isPacked ? join(appCodePath, "python", "app") : null;

// ─── State ────────────────────────────────────────────────────────────────────

let splashWin: BrowserWindow | null = null;
let mainWin: BrowserWindow | null = null;
let pythonProc: ReturnType<typeof Bun.spawn> | null = null;

// ─── Splash ───────────────────────────────────────────────────────────────────

splashWin = new BrowserWindow({
  title: "High Speed Camera",
  url: "views://splash/index.html",
  width: 480,
  height: 320,
  frame: false,
});

// ─── Python subprocess ────────────────────────────────────────────────────────

function spawnPython(port: number): ReturnType<typeof Bun.spawn> {
  const env: Record<string, string> = {
    ...process.env,
    // Keep ELECTRON_RUN for backward compat with mvsdk.py bundle-path logic
    ELECTRON_RUN: "1",
  };
  if (bundlePath) {
    env.HSCAM_BUNDLE_PATH = bundlePath;
  }

  // Store clips in ~/Movies/High Speed Camera/ so they survive app updates.
  // Using the user's home directory keeps clips accessible and persistent.
  // Fall back to ./clips only if HOME is not set (unusual edge case).
  const home = process.env.HOME;
  if (home) {
    env.HSCAM_CLIPS_DIR = `${home}/Movies/High Speed Camera`;
  }

  // In dev mode, set cwd to repo root so relative paths (./clips, etc.) resolve correctly.
  // In packed mode, cwd is the app bundle's python/app directory.
  const cwd = isPacked ? join(appCodePath, "python", "app") : devRepoRoot;

  const proc = Bun.spawn([pythonBin, appEntry, "--port", String(port)], {
    env,
    cwd,
    stdout: "pipe",
    stderr: "pipe",
  });

  if (proc.stdout) {
    (async () => {
      for await (const chunk of proc.stdout as AsyncIterable<Uint8Array>) {
        process.stdout.write(`[python] ${Buffer.from(chunk)}`);
      }
    })();
  }
  if (proc.stderr) {
    (async () => {
      for await (const chunk of proc.stderr as AsyncIterable<Uint8Array>) {
        process.stderr.write(`[python/err] ${Buffer.from(chunk)}`);
      }
    })();
  }

  return proc;
}

// ─── HTTP health polling (now uses /api/status instead of Gradio root) ───────

async function waitForService(port: number): Promise<void> {
  const deadline = Date.now() + STARTUP_TIMEOUT_MS;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`http://localhost:${port}/api/status`);
      if (res.status === 200) return;
    } catch {
      // Not ready yet
    }
    await Bun.sleep(POLL_INTERVAL_MS);
  }
  throw new Error(
    `Python service did not respond on port ${port} within ${STARTUP_TIMEOUT_MS / 1000}s`
  );
}

// ─── Startup sequence ─────────────────────────────────────────────────────────

let activePort: number | null = null;

for (const port of PORTS) {
  pythonProc = spawnPython(port);
  try {
    await waitForService(port);
    activePort = port;
    break;
  } catch {
    pythonProc.kill();
    pythonProc = null;
    // Brief delay to allow the OS to release the port before we try the next one.
    await Bun.sleep(50);
  }
}

function cleanup() {
  if (pythonProc) {
    pythonProc.kill();
    pythonProc = null;
  }
}

process.on("SIGTERM", () => { cleanup(); process.exit(0); });
process.on("SIGINT",  () => { cleanup(); process.exit(0); });

if (activePort === null) {
  console.error(
    `Could not start camera service on any of ports ${PORTS.join(", ")}.\n` +
      "Check that Python dependencies are installed and no other process is using those ports."
  );
  // Transform the splash into an error screen so the user sees a message
  // instead of the app silently disappearing. Content is hardcoded — no user input.
  splashWin?.webview.executeJavascript(`
    var row = document.querySelector('.spinner-row');
    if (row) { row.textContent = 'Could not start the camera service.'; row.style.color = '#fc8181'; }
    var sub = document.querySelector('.subtitle');
    if (sub) { sub.textContent = 'Close this window and try again, or contact your administrator.'; }
    var btn = document.createElement('button');
    btn.textContent = 'Close';
    btn.style.cssText = 'margin-top:24px;padding:8px 24px;background:#fc8181;border:none;border-radius:6px;color:#1a202c;font-size:14px;font-weight:600;cursor:pointer;-webkit-app-region:no-drag';
    btn.addEventListener('click', function() { window.close(); });
    document.body.appendChild(btn);
  `);
  splashWin?.on("close", () => process.exit(1));
} else {
  splashWin?.close();
  splashWin = null;

  // ─── Main window (loads views:// with port injected as URL param) ──────────

  mainWin = new BrowserWindow({
    title: "High Speed Camera",
    url: "views://main/index.html",
    width: 1200,
    height: 900,
  });

  // Inject the active port into the webview via JavaScript once the page loads.
  // views:// doesn't support query parameters, so we set a global variable instead.
  // Note: Electrobun uses executeJavascript (lowercase 's') on BrowserView, not
  // executeJavaScript on webview.
  setTimeout(() => {
    mainWin?.webview.executeJavascript(
      `window.__HSCAM_PORT__ = ${activePort};`
    );
  }, 500);

  mainWin.on("close", () => {
    cleanup();
    process.exit(0);
  });
}

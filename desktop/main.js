'use strict';

const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const http = require('http');
const path = require('path');

// ─── Configuration ───────────────────────────────────────────────────────────

const PORTS = [7860, 7861, 7862];
const POLL_INTERVAL_MS = 500;
const STARTUP_TIMEOUT_MS = 15000;

// In production the Python runtime is bundled under resources/python/.
// In dev (electron .) the project root is two levels up from this file.
const isPacked = app.isPackaged;
const pythonBin = isPacked
  ? path.join(process.resourcesPath, 'python', 'bin', 'python3')
  : 'python3';
const appEntry = isPacked
  ? path.join(process.resourcesPath, 'python', 'app', 'main.py')
  : path.join(__dirname, '..', 'main.py');
const bundlePath = isPacked
  ? path.join(process.resourcesPath, 'python', 'app')
  : null;

// ─── State ───────────────────────────────────────────────────────────────────

let splashWindow = null;
let mainWindow = null;
let pythonProcess = null;
let activePort = null;

// ─── Splash window ───────────────────────────────────────────────────────────

function createSplash() {
  splashWindow = new BrowserWindow({
    width: 480,
    height: 320,
    frame: false,
    resizable: false,
    center: true,
    webPreferences: { nodeIntegration: false },
  });
  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
}

// ─── Main window ─────────────────────────────────────────────────────────────

function createMainWindow(port) {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 900,
    show: false,
    title: 'High Speed Camera',
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });

  mainWindow.loadURL(`http://localhost:${port}`);

  mainWindow.once('ready-to-show', () => {
    if (splashWindow) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
  });

  mainWindow.on('close', () => {
    killPython();
    app.quit();
  });
}

// ─── Python subprocess ───────────────────────────────────────────────────────

function spawnPython(port) {
  const env = { ...process.env, GRADIO_SERVER_PORT: String(port), ELECTRON_RUN: '1' };
  if (bundlePath) {
    env.HSCAM_BUNDLE_PATH = bundlePath;
  }
  // Pass through CAMERA_IP if the user has it set in their environment
  // (already inherited via process.env spread above)

  pythonProcess = spawn(pythonBin, [appEntry, '--port', String(port)], {
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  let stderrBuffer = '';

  pythonProcess.stdout.on('data', (data) => {
    process.stdout.write(`[python] ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    stderrBuffer += data.toString();
    process.stderr.write(`[python/err] ${data}`);
  });

  pythonProcess.on('exit', (code, signal) => {
    if (mainWindow) return; // Normal quit path — window already closed
    // Unexpected crash before the UI was shown
    showStartupError(
      `Python process exited (code ${code}, signal ${signal}).\n\n${stderrBuffer.slice(-2000)}`
    );
  });
}

function killPython() {
  if (pythonProcess) {
    try {
      pythonProcess.kill('SIGTERM');
    } catch (_) {}
    pythonProcess = null;
  }
}

// ─── Polling ─────────────────────────────────────────────────────────────────

function pollUntilReady(port, resolve, reject, deadline) {
  if (Date.now() > deadline) {
    reject(new Error(`Gradio did not respond on port ${port} within ${STARTUP_TIMEOUT_MS / 1000}s`));
    return;
  }

  http
    .get(`http://localhost:${port}/`, (res) => {
      if (res.statusCode >= 200 && res.statusCode < 400) {
        resolve(port);
      } else {
        setTimeout(() => pollUntilReady(port, resolve, reject, deadline), POLL_INTERVAL_MS);
      }
      res.resume();
    })
    .on('error', () => {
      setTimeout(() => pollUntilReady(port, resolve, reject, deadline), POLL_INTERVAL_MS);
    });
}

function waitForGradio(port) {
  return new Promise((resolve, reject) => {
    pollUntilReady(port, resolve, reject, Date.now() + STARTUP_TIMEOUT_MS);
  });
}

// ─── Error dialog ─────────────────────────────────────────────────────────────

function showStartupError(message) {
  if (splashWindow) {
    splashWindow.close();
    splashWindow = null;
  }
  dialog.showErrorBox('High Speed Camera — startup failed', message);
  app.quit();
}

// ─── App lifecycle ────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  createSplash();

  // Try ports in order until one works
  let launched = false;
  for (const port of PORTS) {
    spawnPython(port);
    try {
      await waitForGradio(port);
      activePort = port;
      launched = true;
      break;
    } catch (err) {
      killPython();
      // If we have more ports to try, continue; otherwise fall through to error
    }
  }

  if (!launched) {
    showStartupError(
      `Could not start the Gradio server on any of ports ${PORTS.join(', ')}.\n\n` +
      'Check that Python dependencies are installed and no other process is using those ports.'
    );
    return;
  }

  createMainWindow(activePort);
});

app.on('window-all-closed', () => {
  killPython();
  app.quit();
});

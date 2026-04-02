"""
FastAPI HTTP service for high-speed camera control.

Replaces the Gradio app with a lightweight JSON API + MJPEG stream.
Single-session model with module-level state.
"""

import logging
import os
import signal
import threading
import time
from collections import deque
from typing import Optional

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from src.camera.capture import CaptureSession
from src.camera.device import CameraDevice
from src.camera.highspeed_recorder import HighSpeedRecorder
from src.camera.init import enumerate_all_cameras, initialize_camera

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

SLOWDOWN_PRESETS = [2, 4, 8, 16, 32]
PLAYBACK_FPS_DEFAULT = 30

roi_options = {
    "Full Resolution": (816, 624),
    "720p (Max Width)": (816, 480),
    "Half Height (Fast)": (816, 312),
    "Quarter Height (Faster)": (816, 156),
    "Extreme High-Speed": (816, 64),
}

roi_max_fps = {
    "Full Resolution": 1594,
    "720p (Max Width)": 2000,
    "Half Height (Fast)": 3000,
    "Quarter Height (Faster)": 6000,
    "Extreme High-Speed": 10000,
}

# ── Module-level state (single-session model) ───────────────────────────────

_camera: Optional[CameraDevice] = None
_capture_session: Optional[CaptureSession] = None
_clips_dir = os.environ.get("HSCAM_CLIPS_DIR", "./clips")
_recorder: HighSpeedRecorder = HighSpeedRecorder(
    target_fps=120.0,
    buffer_duration_sec=10.0,
    output_dir=_clips_dir,
    playback_fps=30.0,
)
logger.info("Clips directory: %s", _clips_dir)

_settings_lock = threading.RLock()
_current_settings = {
    "camera": None,
    "roi_preset": "Half Height (Fast)",
    "target_fps": 120.0,
    "playback_fps": 30.0,
    "slowdown_factor": 4.0,
    "exposure_ms": 8.33,
    "gain": 1.0,
    "auto_exposure": False,
    "clip_duration_sec": 5.0,
}

_last_applied = {
    "roi_preset": None,
    "target_fps": None,
    "exposure_ms": None,
    "gain": None,
    "auto_exposure": None,
}

_record_state = {"state": "idle", "path": None, "error": None}

# Camera enumeration cache
_camera_list: Optional[list] = None
_camera_map: dict = {}

# ── Helpers ──────────────────────────────────────────────────────────────────


def compute_fps_from_slowdown(factor: float, roi_preset: str) -> tuple[float, float, float]:
    """Convert slowdown factor + ROI preset to (target_fps, playback_fps, actual_factor).

    Clamps target_fps to the ROI's maximum supported FPS.
    """
    max_fps = roi_max_fps.get(roi_preset, 60)
    target_fps = float(min(max_fps, PLAYBACK_FPS_DEFAULT * factor))
    playback_fps = float(PLAYBACK_FPS_DEFAULT)
    actual_factor = target_fps / playback_fps
    return target_fps, playback_fps, actual_factor


def _ensure_camera_list():
    """Enumerate cameras once and cache the result."""
    global _camera_list, _camera_map
    if _camera_list is None:
        cameras = enumerate_all_cameras()
        _camera_list = cameras
        _camera_map = {c.friendly_name: c for c in cameras}


def _connect_camera(friendly_name: str) -> Optional[str]:
    """Connect to a camera by friendly name. Returns error string or None."""
    global _camera, _capture_session

    _ensure_camera_list()
    info = _camera_map.get(friendly_name)
    if info is None:
        return f"Camera not found: {friendly_name}"

    # Tear down existing session
    if _capture_session and _capture_session._running:
        _capture_session.stop()
        _capture_session = None

    if _camera:
        try:
            _camera.__exit__(None, None, None)
        except Exception:
            pass

    device, error = initialize_camera(selected_info=info)
    if error:
        return error

    _camera = device

    # Reset applied tracking so settings get re-applied
    for key in _last_applied:
        _last_applied[key] = None

    # Start capture
    _capture_session = CaptureSession(_camera, _recorder)
    _capture_session.start()

    return None


def _apply_roi_settings():
    """Apply ROI settings if changed."""
    if _camera is None:
        return
    with _settings_lock:
        preset = _current_settings["roi_preset"]
    if _last_applied.get("roi_preset") == preset:
        return
    width, height = roi_options.get(preset, (816, 624))
    if isinstance(_camera, CameraDevice):
        try:
            _camera.set_roi(width, height)
            logger.info("ROI updated to %s (%dx%d)", preset, width, height)
            _last_applied["roi_preset"] = preset
            _last_applied["target_fps"] = None
            _last_applied["exposure_ms"] = None
        except Exception as e:
            logger.warning("Failed to set ROI: %s", e)


def _apply_fps_settings():
    """Apply target FPS to recorder and camera if changed."""
    if _camera is None:
        return
    with _settings_lock:
        target_fps = _current_settings["target_fps"]
    if _last_applied["target_fps"] == target_fps:
        return
    _recorder.set_target_fps(target_fps)
    if isinstance(_camera, CameraDevice):
        try:
            _camera.set_frame_rate(int(target_fps))
            _last_applied["exposure_ms"] = None
            _apply_exposure_settings()
        except Exception as e:
            logger.warning("Failed to set hardware frame rate: %s", e)
    _last_applied["target_fps"] = target_fps
    logger.info("Target FPS updated to %s", target_fps)


def _apply_exposure_settings():
    """Apply exposure and gain settings to camera."""
    if _camera is None or not isinstance(_camera, CameraDevice):
        return
    with _settings_lock:
        auto_exposure = _current_settings["auto_exposure"]
        exposure_ms = _current_settings["exposure_ms"]
        gain = _current_settings["gain"]
        target_fps = _current_settings["target_fps"]

    max_exposure_ms = (1000.0 / target_fps) * 0.9

    if not auto_exposure and exposure_ms > max_exposure_ms:
        if _last_applied["exposure_ms"] != max_exposure_ms:
            logger.warning(
                "Auto-lowering exposure %.1fms -> %.1fms to hit %s FPS",
                exposure_ms, max_exposure_ms, target_fps,
            )
        exposure_ms = max_exposure_ms

    if (
        _last_applied["auto_exposure"] == auto_exposure
        and _last_applied["exposure_ms"] == exposure_ms
        and _last_applied["gain"] == gain
    ):
        return

    try:
        if auto_exposure:
            max_exp_us = max_exposure_ms * 1000
            _camera.set_auto_exposure(True, int(max_exp_us))
            logger.info("Auto-exposure ENABLED (max %.1fms)", max_exposure_ms)
        else:
            exposure_us = exposure_ms * 1000
            _camera.set_exposure_time(exposure_us)
            logger.info("Manual exposure: %.1fms", exposure_ms)
        _camera.set_gain(gain)
        _last_applied["auto_exposure"] = auto_exposure
        _last_applied["exposure_ms"] = exposure_ms
        _last_applied["gain"] = gain
    except Exception as e:
        logger.error("Failed to apply exposure/gain: %s", e)


def _apply_all_settings():
    """Apply ROI, FPS, and exposure settings in order."""
    _apply_roi_settings()
    _apply_fps_settings()
    _apply_exposure_settings()


def _do_record():
    """Background thread: save a slow-motion clip from the ring buffer."""
    global _record_state
    try:
        _record_state["state"] = "saving"
        _record_state["error"] = None
        with _settings_lock:
            duration = _current_settings["clip_duration_sec"]
            playback_fps = _current_settings["playback_fps"]

        buf_stats = _recorder.get_buffer_stats()
        logger.info(
            "Recording: buffer has %d frames (%.1fs), requesting %.1fs @ %.0f playback fps",
            buf_stats.get("frame_count", 0),
            buf_stats.get("duration_sec", 0),
            duration,
            playback_fps,
        )
        path = _recorder.save_slowmo_clip(duration, playback_fps)
        if path:
            _record_state["state"] = "done"
            _record_state["path"] = path
        else:
            _record_state["state"] = "error"
            _record_state["error"] = (
                f"save_slowmo_clip returned None "
                f"(buffer: {buf_stats.get('frame_count', 0)} frames, "
                f"{buf_stats.get('duration_sec', 0):.1f}s)"
            )
    except Exception as e:
        logger.error("Recording failed: %s", e)
        _record_state["state"] = "error"
        _record_state["error"] = str(e)


def _make_placeholder_frame() -> np.ndarray:
    """Create a black placeholder frame with 'No Camera' text."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(
        frame, "No Camera", (180, 250),
        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (128, 128, 128), 2,
    )
    return frame


# ── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(title="High-Speed Camera API")

app.add_middleware(
    CORSMiddleware,
    # Restrict to the Electrobun views:// scheme and localhost origins only.
    # A wildcard here would let any webpage on the same Mac access the camera API.
    allow_origins=[
        "views://main",
        "views://splash",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ── Pydantic models ─────────────────────────────────────────────────────────

class SettingsRequest(BaseModel):
    camera: Optional[str] = None
    roi_preset: Optional[str] = None
    exposure_ms: Optional[float] = None
    gain: Optional[float] = None
    auto_exposure: Optional[bool] = None
    slowdown_factor: Optional[float] = None
    clip_duration_sec: Optional[float] = None


# ── GET /stream — MJPEG ─────────────────────────────────────────────────────

@app.get("/stream")
def stream():
    """MJPEG video stream endpoint."""

    def generate():
        frame_times: deque = deque(maxlen=30)
        interval = 1.0 / 30.0  # ~30 fps preview cap

        try:
            while True:
                # Apply pending settings each iteration
                if _camera is not None:
                    _apply_all_settings()

                frame = _recorder.get_latest_frame() if _camera else None
                if frame is None:
                    frame = _make_placeholder_frame()

                success, jpeg = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
                )
                if not success:
                    time.sleep(interval)
                    continue

                frame_times.append(time.time())
                jpeg_bytes = jpeg.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + jpeg_bytes
                    + b"\r\n"
                )
                time.sleep(interval)
        except GeneratorExit:
            # Client disconnected — Starlette raises GeneratorExit when the
            # response is closed. This ensures the generator stops and the
            # thread is released rather than running forever.
            logger.debug("MJPEG stream client disconnected")

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ── GET /api/config ──────────────────────────────────────────────────────────

@app.get("/api/config")
def get_config():
    """Return static hardware capabilities: ROI options, preset lists.

    The UI fetches this once on startup so these values have a single source of
    truth (server.py) rather than being duplicated in the frontend JS/HTML.
    """
    return {
        "roi_options": {
            name: {"w": w, "h": h, "maxFps": roi_max_fps[name]}
            for name, (w, h) in roi_options.items()
        },
        "slowdown_presets": SLOWDOWN_PRESETS,
        "playback_fps": PLAYBACK_FPS_DEFAULT,
    }


# ── GET /api/cameras ─────────────────────────────────────────────────────────

@app.get("/api/cameras")
def get_cameras():
    """List available cameras."""
    _ensure_camera_list()
    names = [c.friendly_name for c in (_camera_list or [])]
    return {"cameras": names}


# ── GET /api/status ──────────────────────────────────────────────────────────

@app.get("/api/status")
def get_status():
    """Return current camera state, settings, FPS, and buffer info."""
    connected = _camera is not None
    with _settings_lock:
        settings = _current_settings.copy()

    capture_fps = _recorder.get_actual_fps() if connected else 0.0
    buffer_stats = _recorder.get_buffer_stats()

    target_dur = settings["clip_duration_sec"]
    buf_dur = buffer_stats.get("duration_sec", 0.0)
    fill_pct = min(100.0, (buf_dur / target_dur * 100.0) if target_dur > 0 else 0.0)

    return {
        "connected": connected,
        "settings": {
            "camera": settings["camera"],
            "roi_preset": settings["roi_preset"],
            "exposure_ms": settings["exposure_ms"],
            "gain": settings["gain"],
            "auto_exposure": settings["auto_exposure"],
            "clip_duration_sec": settings["clip_duration_sec"],
        },
        "fps": {
            "target": settings["target_fps"],
            "capture": capture_fps,
            "preview": 0.0,  # computed client-side from stream frame rate
        },
        "buffer": {
            "duration_sec": buf_dur,
            "fill_pct": fill_pct,
            "is_full": buf_dur >= target_dur,
        },
        "slowdown_factor": settings["slowdown_factor"],
    }


# ── POST /api/settings ──────────────────────────────────────────────────────

@app.post("/api/settings")
def post_settings(req: SettingsRequest):
    """Apply camera/recording settings. Returns effective settings."""
    global _camera

    # Validate inputs
    if req.roi_preset is not None and req.roi_preset not in roi_options:
        raise HTTPException(status_code=422, detail=f"Invalid roi_preset: {req.roi_preset}")
    if req.slowdown_factor is not None and req.slowdown_factor <= 0:
        raise HTTPException(status_code=422, detail="slowdown_factor must be positive")
    if req.exposure_ms is not None and req.exposure_ms <= 0:
        raise HTTPException(status_code=422, detail="exposure_ms must be positive")
    if req.gain is not None and req.gain < 0:
        raise HTTPException(status_code=422, detail="gain must be non-negative")
    if req.clip_duration_sec is not None and req.clip_duration_sec <= 0:
        raise HTTPException(status_code=422, detail="clip_duration_sec must be positive")

    # Connect camera if requested
    camera_error = None
    if req.camera is not None:
        camera_error = _connect_camera(req.camera)
        if camera_error:
            raise HTTPException(status_code=422, detail=camera_error)

    with _settings_lock:
        if req.camera is not None:
            _current_settings["camera"] = req.camera

        if req.roi_preset is not None:
            _current_settings["roi_preset"] = req.roi_preset

        if req.auto_exposure is not None:
            _current_settings["auto_exposure"] = req.auto_exposure

        if req.exposure_ms is not None:
            _current_settings["exposure_ms"] = req.exposure_ms

        if req.gain is not None:
            _current_settings["gain"] = req.gain

        if req.clip_duration_sec is not None:
            _current_settings["clip_duration_sec"] = req.clip_duration_sec

        # Compute FPS from slowdown factor (or re-derive if ROI changed)
        if req.slowdown_factor is not None:
            _current_settings["slowdown_factor"] = req.slowdown_factor

        # Recompute target/playback fps from current slowdown + ROI
        factor = _current_settings["slowdown_factor"]
        roi = _current_settings["roi_preset"]
        target_fps, playback_fps, actual_factor = compute_fps_from_slowdown(factor, roi)
        _current_settings["target_fps"] = target_fps
        _current_settings["playback_fps"] = playback_fps

        # Update recorder playback fps
        _recorder.playback_fps = playback_fps

        effective = _current_settings.copy()

    # Apply hardware settings
    _apply_all_settings()

    return {
        "settings": {
            "camera": effective["camera"],
            "roi_preset": effective["roi_preset"],
            "exposure_ms": effective["exposure_ms"],
            "gain": effective["gain"],
            "auto_exposure": effective["auto_exposure"],
            "clip_duration_sec": effective["clip_duration_sec"],
        },
        "target_fps": effective["target_fps"],
        "playback_fps": effective["playback_fps"],
        "slowdown_factor": effective["slowdown_factor"],
        "actual_slowdown": actual_factor,
        "roi_max_fps": roi_max_fps.get(effective["roi_preset"], 60),
    }


# ── POST /api/record + GET /api/record/status ────────────────────────────────

@app.post("/api/record")
def start_record():
    """Trigger saving a slow-motion clip from the ring buffer."""
    if _camera is None:
        raise HTTPException(status_code=422, detail="No camera connected")
    if _record_state["state"] == "saving":
        raise HTTPException(status_code=409, detail="Recording already in progress")

    _record_state["state"] = "saving"
    _record_state["path"] = None
    _record_state["error"] = None

    # Non-daemon so the thread can finish flushing the H.264 encoder on shutdown.
    # The SIGTERM handler waits up to 10 s for it before exiting.
    t = threading.Thread(target=_do_record, daemon=False)
    t.start()
    _record_state["_thread"] = t

    return {"state": "saving"}


@app.get("/api/record/status")
def record_status():
    """Poll recording state."""
    return {
        "state": _record_state["state"],
        "path": _record_state["path"],
        "error": _record_state["error"],
    }


# ── GET /api/record/download ────────────────────────────────────────────────

@app.get("/api/record/download")
def record_download():
    """Download the last saved clip as an MP4 file."""
    path = _record_state.get("path")
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="No recording available")

    filename = os.path.basename(path)
    return FileResponse(
        path,
        media_type="video/mp4",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/record/reveal")
def record_reveal():
    """Open the saved clip's folder in Finder (macOS)."""
    path = _record_state.get("path")
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="No recording available")
    import subprocess
    subprocess.Popen(["open", "-R", path])
    return {"revealed": path}


# ── SIGTERM handler ──────────────────────────────────────────────────────────

_server_ref: Optional[uvicorn.Server] = None


def _sigterm_handler(signum, frame):
    """Gracefully release camera and shut down on SIGTERM."""
    global _camera, _capture_session
    logger.info("SIGTERM received, shutting down...")

    # Wait for any in-progress clip save so the H.264 encoder can flush.
    record_thread = _record_state.get("_thread")
    if record_thread and record_thread.is_alive():
        logger.info("Waiting up to 10 s for recording thread to finish...")
        record_thread.join(timeout=10)

    if _capture_session and _capture_session._running:
        _capture_session.stop()
        _capture_session = None

    if _camera:
        try:
            _camera.__exit__(None, None, None)
        except Exception:
            pass
        _camera = None

    if _server_ref:
        _server_ref.should_exit = True


signal.signal(signal.SIGTERM, _sigterm_handler)


# ── Entry point ──────────────────────────────────────────────────────────────

def run_server(port: int = 7860):
    """Launch the FastAPI server via uvicorn."""
    global _server_ref
    config = uvicorn.Config(app, host="127.0.0.1", port=port)
    server = uvicorn.Server(config)
    _server_ref = server
    server.run()

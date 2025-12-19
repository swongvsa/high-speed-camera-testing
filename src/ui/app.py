"""
Gradio application interface for camera streaming.
Implements patterns from research.md section 1 (Gradio Real-Time Streaming).
Maps to FR-001 through FR-012.

Simplified version: Displays raw camera feed without processing.
High-speed recording: Supports slow-motion capture and playback with decoupled capture thread.
"""

import logging
import threading
import time
from collections import deque
from typing import Iterator, Optional

import gradio as gr
import numpy as np

from src.camera import highspeed_recorder
from src.camera.capture import CaptureSession
from src.camera.init import enumerate_all_cameras
from src.ui.lifecycle import SessionLifecycle
from src.ui.session import ViewerSession

logger = logging.getLogger(__name__)


def create_camera_app() -> gr.Blocks:
    """
    Create Gradio app for camera streaming (raw feed only).
    """
    # Create session manager and lifecycle
    session_manager = ViewerSession()
    lifecycle = SessionLifecycle(session_manager)

    # Initial camera enumeration
    available_cameras = enumerate_all_cameras()
    camera_choices = [c.friendly_name for c in available_cameras]
    camera_map = {c.friendly_name: c for c in available_cameras}

    # Create high-speed video recorder for slow-motion clips (buffer up to 10 seconds)
    recorder = highspeed_recorder.HighSpeedRecorder(
        target_fps=60.0,
        buffer_duration_sec=10.0,
        output_dir="./clips",
        playback_fps=30.0,
    )

    # Background capture session (initialized on demand)
    capture_session: list[Optional[CaptureSession]] = [None]

    # Thread-safe settings for streaming
    settings_lock = threading.RLock()
    current_settings = {
        "auto_exposure": False,
        "exposure_time_ms": 15.0,
        "analog_gain": 1.0,
        "target_fps": 60.0,
        "playback_fps": 30.0,
        "roi_preset": "Half Height (Fast)",  # Demo-friendly default
    }

    # Track last applied settings
    last_applied_settings = {
        "auto_exposure": None,
        "exposure_time_ms": None,
        "analog_gain": None,
        "target_fps": None,
        "roi_preset": None,
    }

    # Global clip duration setting
    clip_duration_sec = {"value": 5.0}

    # Stream epoch token to prevent multiple concurrent generators
    stream_epoch = {"value": 0}

    def check_exposure_guardrails(exposure_ms, target_fps):
        """Check exposure safety and return warnings/status"""
        frame_time_ms = 1000.0 / target_fps
        exposure_ratio = exposure_ms / frame_time_ms

        if exposure_ratio > 1.0:
            return "🚨 DANGER", "Exposure exceeds frame time - motion blur guaranteed!"
        elif exposure_ratio > 0.8:
            return (
                "⚠️ WARNING",
                f"Exposure >80% of frame time ({exposure_ms:.1f}ms > {frame_time_ms * 0.8:.1f}ms)",
            )
        else:
            return "✅ SAFE", f"Exposure OK ({exposure_ms:.1f}ms < {frame_time_ms * 0.8:.1f}ms)"

    def update_status_bar():
        """Update the persistent status bar with current system state"""
        if not lifecycle.camera:
            return "🔌 Connected: No | 🎯 FPS: 0/0 | 📉 Drops: 0 | 📐 ROI: None | 📷 Exp: None | ⏸️ Recording: Idle"

        with settings_lock:
            target_fps = current_settings["target_fps"]
            roi = current_settings["roi_preset"]
            exposure_ms = current_settings["exposure_time_ms"]
            auto_exp = current_settings["auto_exposure"]

        capture_fps = recorder.get_actual_fps()
        buffer_stats = recorder.get_buffer_stats()

        # Calculate drops (simplified - could be enhanced)
        drops = max(0, target_fps - capture_fps) if capture_fps > 0 else 0

        # Exposure status
        if auto_exp:
            exp_display = "Auto"
            exp_status = "✅ AUTO"
        else:
            status_icon, exp_msg = check_exposure_guardrails(exposure_ms, target_fps)
            exp_display = f"{exposure_ms:.1f}ms"
            exp_status = f"{status_icon} {exp_display}"

        # Recording status
        rec_status = "⏸️ Idle"
        if buffer_stats["duration_sec"] > 0:
            rec_status = f"⏺️ Buffering ({buffer_stats['duration_sec']:.1f}s)"

        return f"🔌 Connected: Yes | 🎯 FPS: {capture_fps:.0f}/{target_fps:.0f} | 📉 Drops: {drops:.0f} | 📐 ROI: {roi} | 📷 Exp: {exp_status} | {rec_status}"

    def should_disable_recording():
        """Check if recording should be disabled due to unsafe exposure"""
        if not lifecycle.camera:
            return True, "No camera connected"

        with settings_lock:
            exposure_ms = current_settings["exposure_time_ms"]
            target_fps = current_settings["target_fps"]
            auto_exp = current_settings["auto_exposure"]

        if auto_exp:
            return False, "Recording enabled (auto-exposure)"

        frame_time_ms = 1000.0 / target_fps
        if exposure_ms > frame_time_ms:
            return (
                True,
                f"🚨 Recording disabled: exposure ({exposure_ms:.1f}ms) exceeds frame time ({frame_time_ms:.1f}ms)",
            )

        return False, "Recording enabled"

    # ROI Presets
    roi_options = {
        "Full Resolution": (816, 624),
        "720p (Max Width)": (816, 480),
        "Half Height (Fast)": (816, 312),
        "Quarter Height (Faster)": (816, 156),
        "Extreme High-Speed": (816, 64),
    }

    def _apply_roi_settings():
        """Apply ROI settings if changed"""
        if lifecycle.camera is None:
            return

        with settings_lock:
            preset = current_settings["roi_preset"]
        if last_applied_settings.get("roi_preset") == preset:
            return

        width, height = roi_options.get(preset, (816, 624))

        from src.camera.device import CameraDevice

        if isinstance(lifecycle.camera, CameraDevice):
            try:
                lifecycle.camera.set_roi(width, height)
                logger.info(f"📐 ROI updated to {preset} ({width}x{height})")
                last_applied_settings["roi_preset"] = preset
                # Reset FPS/Exposure so they re-apply to new resolution
                last_applied_settings["target_fps"] = None
                last_applied_settings["exposure_time_ms"] = None
            except Exception as e:
                logger.warning(f"Failed to set ROI: {e}")

    def _apply_exposure_settings():
        """Apply exposure and gain settings to camera based on current settings"""
        if lifecycle.camera is None:
            return

        from src.camera.device import CameraDevice

        if not isinstance(lifecycle.camera, CameraDevice):
            return

        with settings_lock:
            settings = current_settings.copy()
        auto_exposure = settings["auto_exposure"]
        exposure_time_ms = settings["exposure_time_ms"]
        analog_gain = settings["analog_gain"]
        target_fps = settings["target_fps"]

        # Coordination: Ensure exposure time doesn't exceed 1/FPS limit (with 10% safety margin)
        max_exposure_ms = (1000.0 / target_fps) * 0.9

        if not auto_exposure and exposure_time_ms > max_exposure_ms:
            if last_applied_settings["exposure_time_ms"] != max_exposure_ms:
                logger.warning(
                    f"⚡ Auto-lowering exposure {exposure_time_ms}ms -> {max_exposure_ms:.1f}ms to hit {target_fps} FPS"
                )
            exposure_time_ms = max_exposure_ms

        # Skip if settings haven't changed (avoid redundant SDK calls)
        if (
            last_applied_settings["auto_exposure"] == auto_exposure
            and last_applied_settings["exposure_time_ms"] == exposure_time_ms
            and last_applied_settings["analog_gain"] == analog_gain
        ):
            return

        try:
            if auto_exposure:
                max_exp_us = max_exposure_ms * 1000
                lifecycle.camera.set_auto_exposure(True, int(max_exp_us))
                logger.info(f"📸 Auto-exposure ENABLED (Max limit: {max_exposure_ms:.1f}ms)")
            else:
                exposure_us = exposure_time_ms * 1000
                lifecycle.camera.set_exposure_time(exposure_us)
                logger.info(f"📸 Manual exposure: {exposure_time_ms:.1f}ms ({exposure_us:.0f}µs)")

            # Apply analog gain
            lifecycle.camera.set_gain(analog_gain)

            last_applied_settings["auto_exposure"] = auto_exposure
            last_applied_settings["exposure_time_ms"] = exposure_time_ms
            last_applied_settings["analog_gain"] = analog_gain
        except Exception as e:
            logger.error(f"Failed to apply exposure/gain settings: {e}")

    def _apply_fps_settings():
        """Apply target FPS to recorder and camera if changed"""
        if lifecycle.camera is None:
            return

        with settings_lock:
            target_fps = current_settings["target_fps"]
        if last_applied_settings["target_fps"] == target_fps:
            return

        recorder.set_target_fps(target_fps)

        from src.camera.device import CameraDevice

        if isinstance(lifecycle.camera, CameraDevice):
            try:
                lifecycle.camera.set_frame_rate(int(target_fps))
                last_applied_settings["exposure_time_ms"] = None
                _apply_exposure_settings()
            except Exception as e:
                logger.warning(f"Failed to set hardware frame rate: {e}")

        last_applied_settings["target_fps"] = target_fps
        logger.info(f"🎯 Target FPS updated to {target_fps}")

    def frame_stream(
        camera_name: str,
        request: gr.Request,
    ) -> Iterator[tuple[np.ndarray, str, str, str]]:
        """
        Generator function for display-only streaming.
        Samples from background capture thread.
        """
        session_hash = request.session_hash or "unknown"
        current_epoch = stream_epoch["value"]
        logger.info(f"🎬 Stream function called for {camera_name} (epoch: {current_epoch})")

        selected_info = camera_map.get(camera_name)
        error = lifecycle.on_session_start(session_hash, selected_camera=selected_info)
        if error:
            logger.warning(f"Session blocked: {session_hash}")
            gr.Warning(error)
            return

        # Stop existing capture session when camera changes
        if capture_session[0] and capture_session[0]._running:
            capture_session[0].stop()
            capture_session[0] = None

        if lifecycle.camera and (not capture_session[0] or not capture_session[0]._running):
            capture_session[0] = CaptureSession(lifecycle.camera, recorder)
            capture_session[0].start()

        logger.info(f"📹 Camera session active: {session_hash}")

        try:
            display_interval = 1.0 / 25.0
            display_times = deque(maxlen=30)
            last_display_time = time.time()

            while lifecycle.session_manager.is_session_active(session_hash):
                # Check if epoch has changed (camera switched)
                if stream_epoch["value"] != current_epoch:
                    logger.info(
                        f"Stream epoch changed, terminating stream (was {current_epoch}, now {stream_epoch['value']})"
                    )
                    break

                _apply_roi_settings()
                _apply_exposure_settings()
                _apply_fps_settings()

                frame = recorder.get_latest_frame()
                if frame is not None:
                    curr_time = time.time()
                    display_times.append((curr_time - last_display_time) * 1000)
                    last_display_time = curr_time

                    avg_display_time = (
                        sum(display_times) / len(display_times) if display_times else 0
                    )
                    preview_fps = 1000.0 / avg_display_time if avg_display_time > 0 else 0
                    capture_fps = recorder.get_actual_fps()
                    with settings_lock:
                        target_fps = current_settings["target_fps"]

                    cam_info_str = lifecycle.camera.info() if lifecycle.camera else "Unknown Camera"
                    camera_info = (
                        f"📹 Camera: {cam_info_str}\n\n"
                        f"📊 Performance:\n"
                        f"Target FPS: {target_fps:.0f}\n"
                        f"Capture FPS: {capture_fps:.1f} ⚡\n"
                        f"Preview FPS: {preview_fps:.1f}\n"
                        f"Display lag: {avg_display_time:.1f}ms"
                    )

                    buffer_stats = recorder.get_buffer_stats()
                    buffer_duration = buffer_stats["duration_sec"]
                    buffer_frames = buffer_stats["frame_count"]
                    slowmo_factor = buffer_stats["slowmo_factor"]
                    with settings_lock:
                        playback_fps = current_settings["playback_fps"]
                    target_duration = clip_duration_sec["value"]

                    if buffer_duration >= target_duration:
                        buffer_status = (
                            f"Buffer: {buffer_duration:.1f}s / {target_duration:.1f}s ✅\n"
                            f"{buffer_frames} frames | {slowmo_factor:.1f}x slow-mo @ {playback_fps:.0f}fps"
                        )
                    else:
                        buffer_status = (
                            f"Buffer: {buffer_duration:.1f}s / {target_duration:.1f}s\n"
                            f"{buffer_frames} frames (filling...) | {slowmo_factor:.1f}x slow-mo"
                        )

                    status_info = update_status_bar()
                    yield frame, camera_info, buffer_status, status_info

                time.sleep(display_interval)
        except Exception as e:
            logger.error(f"Display stream error: {e}")
            gr.Error(f"Display error: {e}")
        finally:
            # Always cleanup on exit
            if capture_session[0] and capture_session[0]._running:
                capture_session[0].stop()
                capture_session[0] = None
            lifecycle.on_session_end(session_hash)
            logger.info(f"📹 Camera session ended: {session_hash}")

    def on_unload(request: gr.Request):
        """Handle browser close/navigate away."""
        session_hash = request.session_hash or "unknown"
        if capture_session[0]:
            capture_session[0].stop()
            capture_session[0] = None
        lifecycle.on_session_end(session_hash)
        logger.info(f"📹 Camera session ended: {session_hash}")

    # Build Gradio interface
    with gr.Blocks(title="High-Speed Camera Testing") as app:
        # Define helper functions inside Blocks context
        gr.Markdown("# 🚀 High-Speed Camera Testing")
        gr.Markdown("True decoupled high-speed capture (up to 1600 FPS)")

        # Quick Start Section
        with gr.Accordion("🚀 Quick Start Guide", open=True):
            gr.Markdown("""
            **Get started in 3 easy steps:**
            1. **Select ROI**: Choose 'Half Height (Fast)' for best performance
            2. **Set FPS**: Adjust target capture FPS (30-1600)
            3. **Configure Exposure**: Use auto-exposure or manual settings

            **Demo defaults are already set for optimal performance!**
            """)

        with gr.Row():
            with gr.Column(scale=3):
                # Status Bar
                status_bar = gr.Textbox(
                    label="📊 System Status",
                    lines=2,
                    max_lines=2,
                    interactive=False,
                    value="🔌 Connected: No | 🎯 FPS: 0/60 | 📉 Drops: 0 | 📐 ROI: Full | 📷 Exp: 15.0ms | ⏸️ Recording: Idle",
                )

                camera_info_display = gr.Textbox(
                    label="📹 Camera & Performance Info",
                    lines=6,
                    max_lines=6,
                    interactive=False,
                )
                image = gr.Image(label="Live Preview (Decoupled)", show_label=True)

            with gr.Column(scale=1):
                gr.Markdown("### 📹 Hardware Selection")
                camera_dropdown = gr.Dropdown(
                    label="Camera Source",
                    choices=camera_choices,
                    value=camera_choices[0] if camera_choices else None,
                )

                with gr.Accordion("⚡ Capture Performance", open=True):
                    roi_preset = gr.Dropdown(
                        label="Resolution / ROI Preset (px)",
                        choices=list(roi_options.keys()),
                        value="Half Height (Fast)",
                        info="Lower resolution = Higher possible FPS (GigE bandwidth limit ~100MB/s)",
                    )

                    target_fps_slider = gr.Slider(
                        label="Target Capture FPS",
                        minimum=30,
                        maximum=1600,
                        value=60,
                        step=5,
                        info="Hardware frame rate limit. For >100 FPS, use smaller ROI presets above.",
                    )

                with gr.Accordion("📷 Exposure & Brightness", open=True):
                    auto_exposure_checkbox = gr.Checkbox(
                        label="Auto Exposure",
                        value=False,
                        info="Automatically adjust shutter speed for optimal brightness",
                    )
                    exposure_slider = gr.Slider(
                        label="Shutter Speed (ms)",
                        minimum=0.05,
                        maximum=100.0,
                        value=15.0,
                        step=0.05,
                        info="Lower = Faster motion freezing. Max 80% of frame time recommended.",
                    )
                    gain_slider = gr.Slider(
                        label="Analog Gain (x)",
                        minimum=1.0,
                        maximum=16.0,
                        value=1.0,
                        step=0.1,
                        info="Digital amplification. Use when exposure alone isn't enough.",
                    )

                with gr.Accordion("🎬 Recording", open=False):
                    playback_fps_slider = gr.Slider(
                        label="Playback FPS",
                        minimum=15,
                        maximum=60,
                        value=30,
                        step=5,
                        info="Slow-motion playback speed",
                    )
                    clip_duration_slider = gr.Slider(
                        label="Clip Duration (s)",
                        minimum=1.0,
                        maximum=10.0,
                        value=5.0,
                        step=0.5,
                        info="Length of slow-motion clip to save",
                    )

                    recording_status = gr.Textbox(
                        label="Recording Buffer Status",
                        value="Buffer: 0.0s / 5.0s",
                        interactive=False,
                    )
                    record_button = gr.Button("📹 Save Slow-Mo Clip", variant="primary", size="lg")
                    download_button = gr.DownloadButton(label="⬇️ Download Clip", visible=False)

        # Event Handlers (defined inside Blocks context)
        app.load(
            fn=frame_stream,
            inputs=[camera_dropdown],
            outputs=[image, camera_info_display, recording_status, status_bar],
        )

        def on_camera_change(camera_name):
            """Handle camera selection change - increment epoch to terminate old stream"""
            stream_epoch["value"] += 1
            logger.info(f"Camera changed to {camera_name}, new epoch: {stream_epoch['value']}")
            return frame_stream(camera_name, gr.Request())

        camera_dropdown.change(
            fn=on_camera_change,
            inputs=[camera_dropdown],
            outputs=[image, camera_info_display, recording_status, status_bar],
        )

        settings_state = gr.State(current_settings)

        def update_settings(target_fps, auto_ae, exp_ms, playback_fps, roi, analog_gain):
            with settings_lock:
                # Apply exposure guardrails
                corrected_exp_ms = exp_ms
                if not auto_ae:
                    frame_time_ms = 1000.0 / target_fps
                    if exp_ms > frame_time_ms:
                        # Auto-clamp to 90% of frame time
                        corrected_exp_ms = frame_time_ms * 0.9
                        logger.warning(
                            f"Auto-clamped exposure to {corrected_exp_ms:.1f}ms (was over frame time)"
                        )

                new_settings = {
                    "target_fps": target_fps,
                    "auto_exposure": auto_ae,
                    "exposure_time_ms": corrected_exp_ms,
                    "playback_fps": playback_fps,
                    "roi_preset": roi,
                    "analog_gain": analog_gain,
                }
                if new_settings != current_settings:
                    current_settings.update(new_settings)
                    recorder.playback_fps = playback_fps
                    logger.info(f"🔄 Settings: {current_settings}")
                return new_settings, gr.update(value=corrected_exp_ms)

        def update_recording_button():
            """Update recording button state based on safety checks"""
            disabled, tooltip = should_disable_recording()
            return gr.update(interactive=not disabled, label=f"📹 Save Slow-Mo Clip ({tooltip})")

        all_inputs = [
            target_fps_slider,
            auto_exposure_checkbox,
            exposure_slider,
            playback_fps_slider,
            roi_preset,
            gain_slider,
        ]

        def combined_update(*args):
            settings_result, exposure_update = update_settings(*args)
            button_update = update_recording_button()
            return settings_result, exposure_update, button_update

        for ctrl in all_inputs:
            ctrl.change(
                fn=combined_update,
                inputs=all_inputs,
                outputs=[settings_state, exposure_slider, record_button],
            )

        def on_record_click():
            try:
                requested_duration = clip_duration_sec["value"]
                with settings_lock:
                    playback_fps = current_settings["playback_fps"]
                buffer_stats = recorder.get_buffer_stats()

                # Require buffer >= requested duration (not just min(1.0, requested_duration))
                if buffer_stats["duration_sec"] < requested_duration:
                    return (
                        gr.DownloadButton(visible=False),
                        f"⚠️ Buffer too short: {buffer_stats['duration_sec']:.1f}s < {requested_duration:.1f}s",
                    )

                clip_path = recorder.save_slowmo_clip(
                    duration_sec=requested_duration, playback_fps=playback_fps
                )
                if clip_path:
                    return gr.DownloadButton(
                        label="⬇️ Download Clip", value=clip_path, visible=True
                    ), f"✅ Saved {buffer_stats['slowmo_factor']:.1f}x slow-mo"
                return gr.DownloadButton(visible=False), "❌ Failed to save"
            except Exception as e:
                logger.error(f"Record error: {e}")
                return gr.DownloadButton(visible=False), f"❌ Error: {e}"

        def on_duration_change(d):
            clip_duration_sec["value"] = d
            return f"📹 Save Slow-Mo Clip ({d}s)"

        clip_duration_slider.change(
            fn=on_duration_change, inputs=[clip_duration_slider], outputs=[record_button]
        )
        record_button.click(fn=on_record_click, outputs=[download_button, recording_status])
        app.unload(fn=on_unload)

    return app


def launch_app(
    app: gr.Blocks,
    server_name: str = "127.0.0.1",
    server_port: int = 7860,
    share: bool = False,
    inbrowser: bool = True,
) -> None:
    if server_name != "127.0.0.1":
        raise ValueError("Localhost only")
    if share:
        raise ValueError("No sharing")
    logger.info(f"Launching on {server_name}:{server_port}")
    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        inbrowser=inbrowser,
        quiet=False,
    )

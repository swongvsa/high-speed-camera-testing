"""
Gradio application interface for camera streaming.
Implements patterns from research.md section 1 (Gradio Real-Time Streaming).
Maps to FR-001 through FR-012.

Simplified version: Displays raw camera feed without processing.
"""

import logging
import time
from collections import deque
from typing import Iterator

import gradio as gr
import numpy as np

from src.camera.capture import create_frame_generator
from src.camera.init import enumerate_all_cameras
from src.camera.recorder import VideoRecorder
from src.ui.lifecycle import SessionLifecycle
from src.ui.session import ViewerSession

logger = logging.getLogger(__name__)


def create_camera_app() -> gr.Blocks:
    """
    Create Gradio app for camera streaming (raw feed only).

    Implements pattern from research.md section 1:
    - gr.Image with generator-based streaming (FR-006)
    - Session start/end callbacks (FR-006a)
    - Error display (FR-004)
    - Auto-start streaming (FR-003)

    Returns:
        Gradio Blocks application ready to launch

    Contract:
        - Must enforce localhost-only access (FR-012)
        - Must support single viewer only (FR-006a)
        - Must display errors gracefully (FR-004)
        - Must stream continuously (FR-006)
    """
    # Create session manager and lifecycle
    session_manager = ViewerSession()
    lifecycle = SessionLifecycle(session_manager)

    # Initial camera enumeration
    available_cameras = enumerate_all_cameras()
    camera_choices = [c.friendly_name for c in available_cameras]
    camera_map = {c.friendly_name: c for c in available_cameras}

    # Create video recorder for clip saving (buffer up to 10 seconds)
    recorder = VideoRecorder(max_duration_sec=10.0, output_dir="./clips")

    # Global settings for streaming (camera settings only)
    current_settings = {
        "auto_exposure": False,
        "exposure_time_ms": 30.0,  # Stored in ms for UI, converted to us for SDK
    }

    # Global clip duration setting (user-configurable 1-10 seconds)
    clip_duration_sec = {"value": 5.0}  # Use dict to allow modification in nested functions

    def _apply_exposure_settings():
        """Apply exposure settings to camera based on current settings"""
        if lifecycle.camera is None:
            return

        # Exposure control only supported for MindVision cameras for now
        from src.camera.device import CameraDevice

        if not isinstance(lifecycle.camera, CameraDevice):
            return

        settings = current_settings.copy()
        auto_exposure = settings["auto_exposure"]
        exposure_time_ms = settings["exposure_time_ms"]

        try:
            if auto_exposure:
                # Enable auto-exposure (SDK spec section 5.2)
                import src.lib.mvsdk as mvsdk

                mvsdk.CameraSetAeState(lifecycle.camera._handle, 1)  # 1 = auto
                logger.debug("📸 Auto-exposure enabled")
            else:
                # Manual exposure mode - apply exposure time (SDK spec section 5.1)
                exposure_us = exposure_time_ms * 1000  # Convert ms to microseconds
                lifecycle.camera.set_exposure_time(exposure_us)
                logger.debug(f"📸 Manual exposure: {exposure_time_ms}ms ({exposure_us}µs)")
        except Exception as e:
            logger.error(f"Failed to apply exposure settings: {e}")

    def frame_stream(
        camera_name: str,
        request: gr.Request,
    ) -> Iterator[tuple[np.ndarray, str, str]]:
        """
        Generator function for streaming raw camera frames to Gradio.

        Args:
            camera_name: Selected camera name from dropdown
            request: Gradio request with session_hash

        Yields:
            tuple: (frame, camera_info, buffer_status)
                - frame: np.ndarray with raw video frame
                - camera_info: str with camera status and metrics
                - buffer_status: str with recording buffer status

        Contract:
            - FR-003: Auto-start on load
            - FR-006: Continuous updates
            - FR-006a: Block if camera in use
        """
        session_hash = request.session_hash or "unknown"
        camera_info = "Waiting for camera..."
        buffer_status = "Buffer: 0.0s / 5.0s"

        logger.info(f"🎬 Stream function called for {camera_name} - Raw camera feed mode")

        # Get selected camera info
        selected_info = camera_map.get(camera_name)

        # Start or switch session
        error = lifecycle.on_session_start(session_hash, selected_camera=selected_info)
        if error:
            logger.warning(f"Session blocked: {session_hash}")
            # Display error and stop generator
            gr.Warning(error)
            return
        logger.info(f"📹 Camera session active: {session_hash}")

        # Stream frames if camera initialized
        if lifecycle.camera:
            try:
                logger.info("🎥 Starting raw camera frame stream")

                frame_count = 0

                # Performance monitoring - track recent frame times
                frame_times = deque(maxlen=30)  # Last 30 frames for FPS calculation
                last_frame_time = time.time()

                for frame in create_frame_generator(lifecycle.camera):
                    frame_count += 1

                    # Add frame to recorder buffer
                    recorder.add_frame(frame)

                    # Apply exposure settings if changed (check every 10 frames)
                    if frame_count % 10 == 0 or frame_count == 1:
                        _apply_exposure_settings()

                    # Calculate performance metrics
                    current_time = time.time()
                    frame_time_ms = (current_time - last_frame_time) * 1000
                    frame_times.append(frame_time_ms)
                    last_frame_time = current_time

                    # Calculate average FPS from recent frames
                    if len(frame_times) > 0:
                        avg_frame_time = sum(frame_times) / len(frame_times)
                        fps = 1000.0 / avg_frame_time if avg_frame_time > 0 else 0.0
                    else:
                        avg_frame_time = 0.0
                        fps = 0.0

                    # Build camera info (no processing metrics)
                    camera_info = (
                        f"📹 Camera: {lifecycle.camera.info()}\n\n"
                        f"📊 Performance:\n"
                        f"FPS: {fps:.1f}\n"
                        f"Frame time: {avg_frame_time:.1f}ms"
                    )

                    # Build recording buffer status (use selected clip duration)
                    buffer_duration = recorder.get_buffer_duration()
                    buffer_frames = recorder.get_buffer_frame_count()
                    target_duration = clip_duration_sec["value"]

                    if buffer_duration >= target_duration:
                        buffer_status = (
                            f"Buffer: {buffer_duration:.1f}s / {target_duration:.1f}s ✅\n"
                            f"{buffer_frames} frames ready to save"
                        )
                    else:
                        buffer_status = (
                            f"Buffer: {buffer_duration:.1f}s / {target_duration:.1f}s\n"
                            f"{buffer_frames} frames (filling...)"
                        )

                    yield frame, camera_info, buffer_status

            except Exception as e:
                logger.error(f"Stream error: {e}")
                gr.Error(f"Camera error: {e}")
        else:
            logger.error("Camera not initialized")
            gr.Error("Failed to initialize camera")

    def on_unload(request: gr.Request):
        """
        Handle browser close/navigate away.

        Args:
            request: Gradio request with session_hash

        Contract:
            - FR-005: Must release camera resources
            - Must allow next viewer to connect
        """
        session_hash = request.session_hash or "unknown"
        lifecycle.on_session_end(session_hash)
        logger.info(f"📹 Camera session ended: {session_hash}")

    # Build Gradio interface
    with gr.Blocks(title="Camera Feed Display") as app:
        gr.Markdown("# Camera Feed Display")
        gr.Markdown("Live camera stream (raw feed)")

        with gr.Row():
            with gr.Column(scale=3):
                # Camera info display
                camera_info_display = gr.Textbox(
                    label="📹 Camera Info",
                    lines=4,
                    max_lines=4,
                    interactive=False,
                    show_copy_button=False,
                )

                # Image component with streaming
                image = gr.Image(
                    label="Live Camera Feed",
                    show_label=True,
                    show_download_button=False,
                )

            with gr.Column(scale=1):
                gr.Markdown("### Camera Selection")
                camera_dropdown = gr.Dropdown(
                    label="Select Camera Source",
                    choices=camera_choices,
                    value=camera_choices[0] if camera_choices else None,
                    interactive=True,
                )

                gr.Markdown("### Camera Controls")

                gr.Markdown("### Exposure Control (Shutter Speed)")

                # Auto/Manual exposure toggle
                auto_exposure_checkbox = gr.Checkbox(
                    label="Auto Exposure",
                    value=False,
                    info="Enable automatic exposure control",
                )

                # Exposure time slider (disabled when auto-exposure is on)
                exposure_slider = gr.Slider(
                    label="Shutter Speed (Exposure Time)",
                    minimum=0.1,
                    maximum=100.0,
                    value=30.0,
                    step=0.1,
                    info="Exposure in milliseconds (lower=faster/darker, higher=slower/brighter)",
                    interactive=True,
                )

                gr.Markdown("---")
                gr.Markdown(
                    "**📸 Exposure Guide:**\n"
                    "- **Fast motion**: Use shorter exposure (1-10ms) to freeze motion\n"
                    "- **Low light**: Use longer exposure (30-100ms) for brighter image\n"
                    "- **Auto mode**: Camera adjusts exposure automatically\n"
                    "- Default: 30ms (good balance for most scenarios)\n\n"
                    "**SDK Reference:** Spec section 5.1-5.2\n"
                    "- Manual: CameraSetAeState(0) + CameraSetExposureTime()\n"
                    "- Auto: CameraSetAeState(1)"
                )

                gr.Markdown("---")
                gr.Markdown("### 🎬 Video Recording")

                # Clip duration slider
                clip_duration_slider = gr.Slider(
                    label="Clip Duration",
                    minimum=1.0,
                    maximum=10.0,
                    value=5.0,
                    step=0.5,
                    info="Duration of video clip to save (in seconds)",
                    interactive=True,
                )

                # Recording status display
                recording_status = gr.Textbox(
                    label="Recording Buffer Status",
                    value="Buffer: 0.0s / 5.0s",
                    interactive=False,
                    lines=2,
                )

                # Record button
                record_button = gr.Button(
                    "📹 Save Last 5 Seconds",
                    variant="primary",
                    size="lg",
                )

                # Download button (initially hidden)
                download_button = gr.DownloadButton(
                    label="⬇️ Download Clip",
                    visible=False,
                )

                gr.Markdown(
                    "**📹 Recording Guide:**\n"
                    "- Recording buffer constantly stores last 10 seconds\n"
                    "- Adjust 'Clip Duration' slider to choose length (1-10s)\n"
                    "- Click 'Save' button to create video file\n"
                    "- Download button appears when clip is ready\n"
                    "- Clips are saved as MP4 files"
                )

        # Auto-start streaming on page load (FR-003)
        # Use native streaming generator for stable video feed
        app.load(
            fn=frame_stream,
            inputs=[camera_dropdown],
            outputs=[image, camera_info_display, recording_status],
        )

        # Handle camera source change
        camera_dropdown.change(
            fn=frame_stream,
            inputs=[camera_dropdown],
            outputs=[image, camera_info_display, recording_status],
        )

        # Use state to store current settings for streaming
        settings_state = gr.State(
            {
                "auto_exposure": False,
                "exposure_time_ms": 30.0,
            }
        )

        # Function to update settings state
        def update_settings(*args):
            """
            Update global settings for streaming.

            Accepts positional values from the controls in the following order:
            auto_exposure, exposure_time_ms
            """
            keys = [
                "auto_exposure",
                "exposure_time_ms",
            ]
            # Map provided args to keys
            values = list(args)
            new_settings = dict(zip(keys, values))

            # Only log if settings actually changed
            if new_settings != current_settings:
                current_settings.update(new_settings)
                logger.info(f"🔄 Settings updated: {current_settings}")

            return new_settings

        # Recording button callback
        def on_record_click():
            """
            Handle record button click - save buffered frames to video file.

            Returns:
                tuple: (download_button_update, status_message)
            """
            try:
                # Get selected clip duration
                requested_duration = clip_duration_sec["value"]

                # Check buffer status
                buffer_duration = recorder.get_buffer_duration()
                if buffer_duration < min(2.0, requested_duration):
                    gr.Warning(
                        f"Buffer only has {buffer_duration:.1f}s of video. Wait for buffer to fill."
                    )
                    return gr.DownloadButton(
                        visible=False
                    ), "⚠️ Buffer too short, wait for more frames"

                # Save clip with user-selected duration
                logger.info(f"Saving video clip from buffer ({requested_duration:.1f}s)...")
                clip_path = recorder.save_clip(duration_sec=requested_duration)

                if clip_path:
                    logger.info(f"Video clip saved: {clip_path}")
                    return (
                        gr.DownloadButton(label="⬇️ Download Clip", value=clip_path, visible=True),
                        f"✅ Clip saved successfully! ({requested_duration:.1f}s)",
                    )
                else:
                    gr.Warning("Failed to save video clip")
                    return gr.DownloadButton(visible=False), "❌ Failed to save clip"

            except Exception as e:
                logger.error(f"Error saving clip: {e}")
                gr.Error(f"Recording error: {e}")
                return gr.DownloadButton(visible=False), f"❌ Error: {e}"

        # Clip duration change callback
        def on_clip_duration_change(duration: float):
            """
            Handle clip duration slider change.

            Args:
                duration: Selected duration in seconds

            Returns:
                Updated button label
            """
            # Update global duration setting
            clip_duration_sec["value"] = duration

            # Return updated button label
            if duration == int(duration):
                return f"📹 Save Last {int(duration)} Seconds"
            else:
                return f"📹 Save Last {duration:.1f} Seconds"

        # Set up change handlers to update state
        all_controls = [
            auto_exposure_checkbox,
            exposure_slider,
        ]

        for control in all_controls:
            control.change(
                fn=update_settings,
                inputs=all_controls,
                outputs=settings_state,
            )

        # Set up clip duration slider handler
        clip_duration_slider.change(
            fn=on_clip_duration_change,
            inputs=[clip_duration_slider],
            outputs=[record_button],
        )

        # Set up record button handler
        record_button.click(
            fn=on_record_click,
            outputs=[download_button, recording_status],
        )

        # Cleanup on browser close (FR-005)
        app.unload(
            fn=on_unload,
        )

    return app


def launch_app(
    app: gr.Blocks,
    server_name: str = "127.0.0.1",
    server_port: int = 7860,
    share: bool = False,
    inbrowser: bool = True,
) -> None:
    """
    Launch Gradio server with localhost-only access.

    Args:
        app: Gradio application to launch
        server_name: Server bind address (must be "127.0.0.1")
        server_port: Port to bind to
        share: Enable public URL sharing (must be False)
        inbrowser: Auto-open browser on launch

    Raises:
        ValueError: If server_name != "127.0.0.1" or share == True

    Contract:
        - FR-012: Localhost-only access enforced
        - server_name must be "127.0.0.1"
        - share must be False
    """
    # Enforce localhost-only access (FR-012)
    if server_name != "127.0.0.1":
        raise ValueError(
            f"Server must be localhost only. Got server_name='{server_name}', expected '127.0.0.1'"
        )

    if share:
        raise ValueError("Public sharing is not allowed. share must be False.")

    logger.info(f"Launching Gradio server on {server_name}:{server_port}")

    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        inbrowser=inbrowser,
        quiet=False,
    )

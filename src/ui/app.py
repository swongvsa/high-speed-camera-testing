"""
Gradio application interface for camera streaming.
Implements patterns from research.md section 1 (Gradio Real-Time Streaming).
Maps to FR-001 through FR-012.

Extended with:
- Object segmentation capabilities using Ultralytics and Supervision
- Face recognition capabilities using DeepFace
"""

import logging
import time
from collections import deque
from typing import Iterator, Optional

import gradio as gr
import numpy as np

from src.camera.capture import create_frame_generator
from src.face_recognition import (
    EmbeddingsManager,
    FaceRecognitionConfig,
    FaceRecognitionProcessor,
)
from src.segmentation import COCO_CLASSES, SegmentationConfig, SegmentationProcessor
from src.ui.lifecycle import SessionLifecycle
from src.ui.session import ViewerSession

logger = logging.getLogger(__name__)


def create_camera_app() -> gr.Blocks:
    """
    Create Gradio app for camera streaming with optional segmentation.

    Implements pattern from research.md section 1:
    - gr.Image with generator-based streaming (FR-006)
    - Session start/end callbacks (FR-006a)
    - Error display (FR-004)
    - Auto-start streaming (FR-003)
    - Optional object segmentation with Ultralytics

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

    # Segmentation processor (lazy-loaded)
    seg_processor: Optional[SegmentationProcessor] = None

    # Face recognition processor (lazy-loaded)
    face_processor: Optional[FaceRecognitionProcessor] = None
    embeddings_mgr = EmbeddingsManager()  # Shared embeddings manager

    # Global settings for streaming (updated by change handlers)
    current_settings = {
        "enable_segmentation": False,
        "model_size": "n",
        "confidence": 0.25,
        "enable_tracking": False,
        "selected_classes": None,
        "enable_face_recognition": False,
        "face_model": "Facenet",
        "face_detector": "retinaface",
        "face_threshold": 0.6,
        "auto_exposure": False,
        "exposure_time_ms": 30.0,  # Stored in ms for UI, converted to us for SDK
    }

    def _ensure_processors_initialized():
        """Initialize or update processors based on current settings"""
        nonlocal seg_processor, face_processor

        settings = current_settings.copy()

        # Initialize segmentation processor if needed
        if settings["enable_segmentation"]:
            try:
                # Convert class names to IDs
                class_filter = None
                if settings["selected_classes"]:
                    class_filter = [
                        class_id
                        for class_id, name in COCO_CLASSES.items()
                        if name in settings["selected_classes"]
                    ]

                config = SegmentationConfig(
                    model_size=settings["model_size"],
                    confidence_threshold=settings["confidence"],
                    enable_tracking=settings["enable_tracking"],
                    enable_smoothing=False,
                    show_labels=True,
                    show_confidence=True,
                    mask_opacity=0.5,
                    class_filter=class_filter,
                )

                # Only reload model if model_size changed or processor doesn't exist
                need_reload = (
                    seg_processor is None
                    or seg_processor._config.model_size != config.model_size
                )

                if need_reload:
                    logger.info(f"Creating segmentation processor: {config.model_path}")
                    seg_processor = SegmentationProcessor(config)
                    logger.info("✅ Segmentation processor ready")
                else:
                    # Just update config without reloading model
                    seg_processor._config = config
                    logger.debug(f"Updated segmentation config (no reload): conf={config.confidence_threshold}, track={config.enable_tracking}")

            except Exception as e:
                logger.error(f"Failed to initialize segmentation: {e}")
                seg_processor = None

        # Initialize face recognition processor if needed
        if settings["enable_face_recognition"]:
            try:
                config = FaceRecognitionConfig(
                    model_name=settings["face_model"],
                    detector_backend=settings["face_detector"],
                    recognition_threshold=settings["face_threshold"],
                    distance_metric="cosine",
                    show_labels=True,
                    show_confidence=True,
                )

                # Only reload if model or detector backend changed
                need_reload = (
                    face_processor is None
                    or face_processor._config.model_name != config.model_name
                    or face_processor._config.detector_backend != config.detector_backend
                )

                if need_reload:
                    logger.info(f"Creating face recognition processor: {config.model_name}")
                    face_processor = FaceRecognitionProcessor(config, embeddings_mgr)
                    num_enrolled = face_processor.num_enrolled
                    logger.info(f"✅ Face recognition ready ({num_enrolled} enrolled)")
                else:
                    # Just update config without reloading
                    face_processor._config = config
                    logger.debug(f"Updated face recognition config (no reload): threshold={config.recognition_threshold}")

            except Exception as e:
                logger.error(f"Failed to initialize face recognition: {e}")
                face_processor = None

    def _apply_exposure_settings():
        """Apply exposure settings to camera based on current settings"""
        if lifecycle.camera is None:
            return

        settings = current_settings.copy()
        auto_exposure = settings["auto_exposure"]
        exposure_time_ms = settings["exposure_time_ms"]

        try:
            if auto_exposure:
                # Enable auto-exposure (SDK spec section 5.2)
                import src.lib.mvsdk as mvsdk
                mvsdk.CameraSetAeState(lifecycle.camera._handle, 1)  # 1 = auto
                logger.info("📸 Auto-exposure enabled")
            else:
                # Manual exposure mode - apply exposure time (SDK spec section 5.1)
                exposure_us = exposure_time_ms * 1000  # Convert ms to microseconds
                lifecycle.camera.set_exposure_time(exposure_us)
                logger.info(f"📸 Manual exposure: {exposure_time_ms}ms ({exposure_us}µs)")
        except Exception as e:
            logger.error(f"Failed to apply exposure settings: {e}")

    def get_single_frame(request: gr.Request) -> tuple[np.ndarray, str]:
        """Get a single frame using current settings (for periodic updates)"""
        # Use current settings
        settings = current_settings.copy()
        enable_segmentation = settings["enable_segmentation"]
        enable_face_recognition = settings["enable_face_recognition"]

        session_hash = request.session_hash or "unknown"

        # Only start session if not already started
        if lifecycle.camera is None:
            error = lifecycle.on_session_start(session_hash)
            if error:
                logger.warning(f"Session blocked: {session_hash}")
                return np.zeros((480, 640, 3), dtype=np.uint8), f"❌ {error}"

        # Ensure processors are initialized based on current settings
        _ensure_processors_initialized()

        try:
            # Get frame from camera
            frame = lifecycle.camera.get_frame()

            # Handle timeout indicated by returning None
            if frame is None:
                # Return a placeholder image and a gentle timeout message
                return np.zeros(
                    (480, 640, 3), dtype=np.uint8
                ), "⏳ Frame timeout: no frame received"

            debug_info = f"📹 Camera: {lifecycle.camera.info()}"

            # Apply processing based on current settings
            if enable_segmentation and seg_processor:
                frame, seg_debug = seg_processor.process_frame(frame)
                debug_info += f" | 🎯 {seg_debug}"

            if enable_face_recognition and face_processor:
                frame, face_debug = face_processor.process_frame(frame)
                debug_info += f" | 👤 {face_debug}"

            return frame, debug_info

        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return np.zeros((480, 640, 3), dtype=np.uint8), f"❌ Error: {str(e)}"

    def frame_stream(
        request: gr.Request,
        enable_segmentation: bool = False,
        model_size: str = "n",
        confidence: float = 0.25,
        enable_tracking: bool = False,
        selected_classes: Optional[list] = None,
        enable_face_recognition: bool = False,
        face_model: str = "Facenet512",
        face_detector: str = "retinaface",
        face_threshold: float = 0.6,
    ) -> Iterator[tuple[np.ndarray, str]]:
        """
        Generator function for streaming camera frames to Gradio.

        Args:
            request: Gradio request with session_hash
            enable_segmentation: Enable object segmentation
            model_size: YOLO model size (n/s/m/l/x)
            confidence: Confidence threshold (0.0-1.0)
            enable_tracking: Enable object tracking
            selected_classes: List of class names to detect (empty = all)
            enable_face_recognition: Enable face recognition
            face_model: Face recognition model
            face_detector: Face detection backend
            face_threshold: Recognition confidence threshold (0.0-1.0)

        Yields:
            tuple: (frame, debug_info)
                - frame: np.ndarray with video frame (optionally annotated)
                - debug_info: str with detection/recognition info

        Contract:
            - FR-003: Auto-start on load
            - FR-006: Continuous updates
            - FR-006a: Block if camera in use
        """
        nonlocal seg_processor, face_processor

        session_hash = request.session_hash or "unknown"
        debug_info = "Waiting for camera..."

        # Use current settings instead of function parameters for dynamic updates
        settings = current_settings.copy()
        enable_segmentation = settings["enable_segmentation"]
        model_size = settings["model_size"]
        confidence = settings["confidence"]
        enable_tracking = settings["enable_tracking"]

        selected_classes = settings["selected_classes"]
        enable_face_recognition = settings["enable_face_recognition"]
        face_model = settings["face_model"]
        face_detector = settings["face_detector"]
        face_threshold = settings["face_threshold"]

        logger.info(
            f"🎬 Stream function called - "
            f"Segmentation: {enable_segmentation}, "
            f"Face Recognition: {enable_face_recognition}, "
            f"Model: {model_size}, "
            f"Confidence: {confidence}"
        )

        # Only start session if not already started
        # Check if camera already initialized for this session
        if lifecycle.camera is None:
            # First time - start session
            error = lifecycle.on_session_start(session_hash)
            if error:
                logger.warning(f"Session blocked: {session_hash}")
                # Display error and stop generator
                gr.Warning(error)
                return
            logger.info(f"📹 Camera session started: {session_hash}")
        else:
            # Session already active - just update settings
            logger.debug(f"Reusing existing camera session: {session_hash}")

        # Initialize segmentation processor if needed
        if enable_segmentation:
            logger.info("🔍 Segmentation is ENABLED - initializing processor")
            try:
                # Convert class names to IDs
                class_filter = None
                if selected_classes:  # None or empty list = detect all classes
                    class_filter = [
                        class_id
                        for class_id, name in COCO_CLASSES.items()
                        if name in selected_classes
                    ]

                config = SegmentationConfig(
                    model_size=model_size,
                    confidence_threshold=confidence,
                    enable_tracking=enable_tracking,
                    enable_smoothing=False,
                    show_labels=True,
                    show_confidence=True,
                    mask_opacity=0.5,
                    class_filter=class_filter,
                )

                # Create or recreate processor if config changed
                if seg_processor is None or seg_processor._config != config:
                    logger.info(f"Creating NEW segmentation processor: {config.model_path}")

                    # Show info about first-time download
                    gr.Info(
                        f"Loading {config.model_path}... "
                        "(First use may download model, please wait)"
                    )

                    seg_processor = SegmentationProcessor(config)

                    # Confirm ready
                    gr.Info("✅ Segmentation ready!")

            except Exception as e:
                logger.error(f"Failed to initialize segmentation: {e}")
                error_msg = str(e)
                if "internet connection" in error_msg.lower():
                    gr.Error("Failed to download model. Please check your internet connection.")
                else:
                    gr.Error(f"Segmentation initialization failed: {e}")
                enable_segmentation = False

        # Initialize face recognition processor if needed
        if enable_face_recognition:
            logger.info("👤 Face recognition is ENABLED - initializing processor")
            try:
                config = FaceRecognitionConfig(
                    model_name=face_model,
                    detector_backend=face_detector,
                    recognition_threshold=face_threshold,
                    distance_metric="cosine",
                    show_labels=True,
                    show_confidence=True,
                )

                # Create or recreate processor if config changed
                if face_processor is None or face_processor._config != config:
                    logger.info(f"Creating NEW face recognition processor: {config.model_name}")

                    # Show info about first-time download
                    gr.Info(
                        f"Loading {config.model_name} face recognition... "
                        "(First use may download models, please wait)"
                    )

                    face_processor = FaceRecognitionProcessor(config, embeddings_mgr)

                    # Confirm ready
                    num_enrolled = face_processor.num_enrolled
                    gr.Info(f"✅ Face recognition ready! ({num_enrolled} enrolled faces)")

            except Exception as e:
                logger.error(f"Failed to initialize face recognition: {e}")
                error_msg = str(e)
                if "internet connection" in error_msg.lower():
                    gr.Error(
                        "Failed to download face model. Please check your internet connection."
                    )
                else:
                    gr.Error(f"Face recognition initialization failed: {e}")
                enable_face_recognition = False

        # Stream frames if camera initialized
        if lifecycle.camera:
            try:
                logger.info(
                    f"🎥 Starting frame stream - Segmentation: {enable_segmentation}, "
                    f"Face Recognition: {enable_face_recognition}"
                )

                frame_count = 0

                # Performance monitoring - track recent processing times
                frame_times = deque(maxlen=30)  # Last 30 frames for FPS calculation
                seg_times = deque(maxlen=30)    # Segmentation processing times
                face_times = deque(maxlen=30)   # Face recognition processing times
                last_frame_time = time.time()

                for frame in create_frame_generator(lifecycle.camera):
                    frame_count += 1

                    # Refresh settings periodically (every 10 frames to reduce overhead)
                    if frame_count % 10 == 0 or frame_count == 1:
                        settings = current_settings.copy()
                        enable_segmentation = settings["enable_segmentation"]
                        enable_face_recognition = settings["enable_face_recognition"]

                        # Initialize processors if settings changed
                        _ensure_processors_initialized()

                        # Apply exposure settings if changed
                        _apply_exposure_settings()

                    debug_info = ""
                    seg_time_ms = 0.0
                    face_time_ms = 0.0

                    # Apply segmentation if enabled
                    if enable_segmentation and seg_processor:
                        if frame_count == 1:
                            logger.info("✅ Applying segmentation to frames")
                        seg_start = time.time()
                        frame, seg_debug = seg_processor.process_frame(frame)
                        seg_time_ms = (time.time() - seg_start) * 1000
                        seg_times.append(seg_time_ms)
                        debug_info = seg_debug

                    # Apply face recognition if enabled (can stack with segmentation)
                    if enable_face_recognition and face_processor:
                        if frame_count == 1:
                            logger.info("✅ Applying face recognition to frames")
                        face_start = time.time()
                        frame, face_debug = face_processor.process_frame(frame)
                        face_time_ms = (time.time() - face_start) * 1000
                        face_times.append(face_time_ms)
                        # Combine debug info if both are enabled
                        if debug_info:
                            debug_info = f"{debug_info}\n\n--- Face Recognition ---\n{face_debug}"
                        else:
                            debug_info = face_debug

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
                        fps = 0.0

                    # Calculate average processing times
                    avg_seg_time = sum(seg_times) / len(seg_times) if seg_times else 0.0
                    avg_face_time = sum(face_times) / len(face_times) if face_times else 0.0
                    total_processing_time = seg_time_ms + face_time_ms

                    # Add performance info to debug output
                    perf_info = (
                        f"\n\n📊 Performance (avg over {len(frame_times)} frames):\n"
                        f"FPS: {fps:.1f} | Frame time: {avg_frame_time:.1f}ms\n"
                    )

                    if enable_segmentation:
                        perf_info += f"Segmentation: {avg_seg_time:.1f}ms (current: {seg_time_ms:.1f}ms)\n"

                    if enable_face_recognition:
                        perf_info += f"Face Recognition: {avg_face_time:.1f}ms (current: {face_time_ms:.1f}ms)\n"

                    if enable_segmentation and enable_face_recognition:
                        perf_info += f"Total processing: {total_processing_time:.1f}ms\n"

                    # Warn if processing is taking too long
                    if total_processing_time > 100:
                        perf_info += "⚠️  High processing load - may cause timeouts"

                    # If neither enabled, show message
                    if not enable_segmentation and not enable_face_recognition:
                        if frame_count == 1:
                            logger.info("⏸️  No processing enabled - showing raw frames")
                        debug_info = (
                            "No processing enabled\n\n"
                            "Enable Segmentation or Face Recognition to start"
                        )
                        perf_info = ""  # No need for perf info when nothing is processing

                    # Combine debug info with performance info
                    if perf_info:
                        debug_info = f"{debug_info}{perf_info}"

                    yield frame, debug_info

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

    def enroll_face_handler(image, name: str) -> tuple[str, list[str]]:
        """
        Enroll a new face from uploaded image.

        Args:
            image: Uploaded image (numpy array or path)
            name: Person's name

        Returns:
            Tuple of (status_message, updated_face_list)
        """
        nonlocal face_processor

        if image is None:
            return "❌ Please upload an image", embeddings_mgr.list_faces()

        if not name or not name.strip():
            return "❌ Please enter a name", embeddings_mgr.list_faces()

        try:
            # Initialize face processor if needed (with default config)
            if face_processor is None:
                config = FaceRecognitionConfig()
                face_processor = FaceRecognitionProcessor(config, embeddings_mgr)

            # Enroll the face
            result = face_processor.enroll_face(name.strip(), image)

            status = (
                f"✅ Successfully enrolled '{result['name']}'\n"
                f"Model: {result['model']}\n"
                f"Embedding dimension: {result['embedding_dim']}"
            )

            return status, embeddings_mgr.list_faces()

        except ValueError as e:
            logger.error(f"Enrollment validation error: {e}")
            return f"❌ {str(e)}", embeddings_mgr.list_faces()
        except Exception as e:
            logger.error(f"Enrollment failed: {e}", exc_info=True)
            return f"❌ Enrollment failed: {str(e)}", embeddings_mgr.list_faces()

    def delete_face_handler(name: str) -> tuple[str, list[str]]:
        """
        Delete a face from the database.

        Args:
            name: Person's name to delete

        Returns:
            Tuple of (status_message, updated_face_list)
        """
        if not name or not name.strip():
            return "❌ Please select a face to delete", embeddings_mgr.list_faces()

        if embeddings_mgr.remove_face(name.strip()):
            return f"✅ Deleted '{name}' from database", embeddings_mgr.list_faces()
        else:
            return f"❌ Face '{name}' not found", embeddings_mgr.list_faces()

    # Build Gradio interface
    with gr.Blocks(title="Camera Feed Display") as app:
        gr.Markdown("# Camera Feed Display")
        gr.Markdown("Live camera stream with object segmentation and face recognition")

        with gr.Row():
            with gr.Column(scale=3):
                # Debug info display
                debug_display = gr.Textbox(
                    label="🔍 Detection & Recognition Info (Debug)",
                    lines=8,
                    max_lines=8,
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
                gr.Markdown("### Processing Controls")

                # Enable/disable segmentation (outside tabs for event handling)
                enable_seg = gr.Checkbox(
                    label="Enable Object Segmentation",
                    value=False,
                    info="Turn on/off object detection and masking",
                )

                # Enable/disable face recognition (outside tabs for event handling)
                enable_face_recog = gr.Checkbox(
                    label="Enable Face Recognition",
                    value=False,
                    info="Turn on/off face recognition",
                )

                gr.Markdown("---")

                with gr.Tabs():
                    with gr.Tab("Segmentation"):
                        gr.Markdown("### Segmentation Settings")

                        # Model selection
                        model_dropdown = gr.Dropdown(
                            label="Model Size",
                            choices=["n", "s", "m", "l", "x"],
                            value="n",
                            info="Nano (fastest) to XLarge (most accurate)",
                        )

                        # Confidence threshold
                        confidence_slider = gr.Slider(
                            label="Confidence Threshold",
                            minimum=0.0,
                            maximum=1.0,
                            value=0.25,
                            step=0.05,
                            info="Lower = more detections (0.20-0.30 recommended)",
                        )

                        # Tracking toggle
                        tracking_checkbox = gr.Checkbox(
                            label="Enable Tracking",
                            value=False,
                            info="Track objects across frames",
                        )

                        # Class selection
                        class_choices = sorted(COCO_CLASSES.values())
                        class_selector = gr.Dropdown(
                            label="Objects to Detect",
                            choices=class_choices,
                            value=[],
                            multiselect=True,
                            info="Leave empty to detect all 80 COCO classes",
                        )

                        with gr.Row():
                            select_all_btn = gr.Button("Select All Classes", size="sm")
                            clear_all_btn = gr.Button("Clear Selection", size="sm")

                        gr.Markdown("---")
                        gr.Markdown(
                            "**Model Info:**\n"
                            "- Models auto-download on first use (~6MB for nano, ~50MB for xlarge)\n"
                            "- Cached in `~/.ultralytics/weights/` for reuse\n"
                            "- GPU acceleration used automatically if available\n"
                            "- First load may take 10-30 seconds"
                        )

                        gr.Markdown(
                            "**💡 Troubleshooting:**\n"
                            "- **No detections?** Lower confidence threshold to 0.25-0.30\n"
                            "- **Check logs** for detection counts in terminal\n"
                            "- **Status indicator** shows on frame when active\n"
                            "- Point camera at common objects (person, chair, laptop, phone)"
                        )

                    with gr.Tab("Face Recognition"):
                        gr.Markdown("### Recognition Settings")

                        # Model selection
                        face_model_dropdown = gr.Dropdown(
                            label="Recognition Model",
                            choices=[
                                "Facenet512",
                                "Facenet",
                                "VGG-Face",
                                "ArcFace",
                                "Dlib",
                                "SFace",
                            ],
                            value="Facenet",
                            info="Facenet recommended for speed (Facenet512 for max accuracy)",
                        )

                        # Detector backend
                        face_detector_dropdown = gr.Dropdown(
                            label="Face Detector",
                            choices=["retinaface", "mtcnn", "opencv", "ssd", "dlib", "yunet"],
                            value="retinaface",
                            info="RetinaFace recommended for robustness",
                        )

                        # Recognition threshold
                        face_threshold_slider = gr.Slider(
                            label="Recognition Threshold",
                            minimum=0.0,
                            maximum=1.0,
                            value=0.6,
                            step=0.05,
                            info="Higher = stricter matching (0.5-0.7 recommended)",
                        )

                        gr.Markdown("---")
                        gr.Markdown("### Enroll New Face")

                        # Face enrollment
                        enroll_image = gr.Image(
                            label="Upload Face Photo",
                            type="numpy",
                            sources=["upload"],
                        )

                        enroll_name = gr.Textbox(
                            label="Person's Name",
                            placeholder="Enter name...",
                        )

                        enroll_btn = gr.Button("Enroll Face", variant="primary")

                        enroll_status = gr.Textbox(
                            label="Enrollment Status",
                            lines=3,
                            interactive=False,
                        )

                        gr.Markdown("---")
                        gr.Markdown("### Face Database")

                        # Face database management
                        face_list = gr.Dropdown(
                            label="Enrolled Faces",
                            choices=embeddings_mgr.list_faces(),
                            value=None,
                            interactive=True,
                        )

                        delete_btn = gr.Button("Delete Selected Face", variant="stop")

                        delete_status = gr.Textbox(
                            label="Status",
                            lines=1,
                            interactive=False,
                        )

                        gr.Markdown(
                            "**💡 Tips:**\n"
                            "- Use clear, well-lit photos\n"
                            "- Photo should contain exactly 1 face\n"
                            "- Face should be front-facing\n"
                            "- Higher quality images = better recognition"
                        )

                    with gr.Tab("Camera Settings"):
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

        # Button handlers for class selection
        select_all_btn.click(
            fn=lambda: class_choices,
            outputs=[class_selector],
        )
        clear_all_btn.click(
            fn=lambda: [],
            outputs=[class_selector],
        )

        # Face enrollment handler
        enroll_btn.click(
            fn=enroll_face_handler,
            inputs=[enroll_image, enroll_name],
            outputs=[enroll_status, face_list],
        )

        # Face deletion handler
        delete_btn.click(
            fn=delete_face_handler,
            inputs=[face_list],
            outputs=[delete_status, face_list],
        )

        # Auto-start streaming on page load (FR-003)
        # Use native streaming generator for stable video feed
        app.load(
            fn=frame_stream,
            outputs=[image, debug_display],
        )

        # Use state to store current settings for streaming
        settings_state = gr.State(
            {
                "enable_segmentation": False,
                "model_size": "n",
                "confidence": 0.25,
                "enable_tracking": False,
                "selected_classes": None,
                "enable_face_recognition": False,
                "face_model": "Facenet",
                "face_detector": "retinaface",
                "face_threshold": 0.6,
                "auto_exposure": False,
                "exposure_time_ms": 30.0,
            }
        )

        # Function to update settings state
        def update_settings(*args):
            """
            Update global settings for streaming.

            Accepts positional values from the controls in the following order:
            enable_segmentation, model_size, confidence, enable_tracking,
            selected_classes, enable_face_recognition, face_model,
            face_detector, face_threshold, auto_exposure, exposure_time_ms
            """
            keys = [
                "enable_segmentation",
                "model_size",
                "confidence",
                "enable_tracking",
                "selected_classes",
                "enable_face_recognition",
                "face_model",
                "face_detector",
                "face_threshold",
                "auto_exposure",
                "exposure_time_ms",
            ]
            # Map provided args to keys; missing args are ignored
            values = list(args)
            new_settings = dict(zip(keys, values))
            # Normalize empty selection to None
            if "selected_classes" in new_settings and new_settings.get("selected_classes") == []:
                new_settings["selected_classes"] = None
            # Update global settings
            current_settings.update(new_settings)
            logger.info(f"🔄 Settings updated: {current_settings}")
            return new_settings

        # Set up change handlers to update state (don't restart stream)

        # Set up change handlers to update state (don't restart stream)
        all_controls = [
            enable_seg,
            model_dropdown,
            confidence_slider,
            tracking_checkbox,
            class_selector,
            enable_face_recog,
            face_model_dropdown,
            face_detector_dropdown,
            face_threshold_slider,
            auto_exposure_checkbox,
            exposure_slider,
        ]

        for control in all_controls:
            control.change(
                fn=update_settings,
                inputs=all_controls,
                outputs=settings_state,
            )

        # All change handlers now use state-based approach above

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

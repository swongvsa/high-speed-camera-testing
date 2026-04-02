// ── High-Speed Camera UI ─────────────────────────────────────────────────────
// Static frontend that talks to the Python HTTP service via REST + MJPEG.
// NOTE: All innerHTML usage below constructs markup solely from local numeric
// constants and state (never from user input or raw API strings), so XSS risk
// is not applicable here.

(function () {
    "use strict";

    // ── Constants ────────────────────────────────────────────────────────────
    // ROI_OPTIONS and SLOWDOWN_PRESETS are defaults only. On first connection,
    // fetchConfig() replaces these with server-authoritative values from
    // /api/config, so server.py is the single source of truth.

    var SLOWDOWN_PRESETS = [2, 4, 8, 16, 32];
    var PLAYBACK_FPS = 30;
    var ROI_OPTIONS = {
        "Full Resolution":       { w: 816, h: 624, maxFps: 1594 },
        "720p (Max Width)":      { w: 816, h: 480, maxFps: 2000 },
        "Half Height (Fast)":    { w: 816, h: 312, maxFps: 3000 },
        "Quarter Height (Faster)": { w: 816, h: 156, maxFps: 6000 },
        "Extreme High-Speed":    { w: 816, h: 64,  maxFps: 10000 },
    };
    var DURATION_PRESETS = [2, 3, 5, 7, 10];
    var STATUS_POLL_MS = 1000;
    var RECORD_POLL_MS = 500;

    // ── Port / Base URL ──────────────────────────────────────────────────────
    // Try multiple sources for the port:
    // 1. window.__HSCAM_PORT__ (injected by Electrobun after page load)
    // 2. URL query param ?port=XXXX (for dev/browser testing)
    // 3. Auto-discover by probing known ports [7860, 7861, 7862]

    var KNOWN_PORTS = [7860, 7861, 7862];
    var port = window.__HSCAM_PORT__
        || new URLSearchParams(window.location.search).get("port")
        || null;
    var BASE = port ? ("http://localhost:" + port) : "";
    var portDiscovered = !!port;

    async function discoverPort() {
        if (portDiscovered) return true;
        // Check if Electrobun injected it late
        if (window.__HSCAM_PORT__) {
            port = window.__HSCAM_PORT__;
            BASE = "http://localhost:" + port;
            portDiscovered = true;
            return true;
        }
        for (var i = 0; i < KNOWN_PORTS.length; i++) {
            try {
                var res = await fetch("http://localhost:" + KNOWN_PORTS[i] + "/api/status");
                if (res.ok) {
                    port = KNOWN_PORTS[i];
                    BASE = "http://localhost:" + port;
                    portDiscovered = true;
                    return true;
                }
            } catch (_e) { /* try next */ }
        }
        return false;
    }

    // ── Application State ────────────────────────────────────────────────────

    var state = {
        connected: false,
        cameraName: "",
        roiPreset: "Half Height (Fast)",
        slowdownFactor: 8,
        clipDurationSec: 5,
        exposureMs: 8.33,
        gain: 1.0,
        autoExposure: false,
        targetFps: 240,
        captureFps: 0,
        previewFps: 0,
        bufferDurationSec: 0,
        bufferTargetSec: 10,
        bufferFillPct: 0,
        bufferIsFull: false,
        recording: false,
        recordState: "idle",
        recordPath: "",
        recordError: "",
    };

    // ── DOM References ───────────────────────────────────────────────────────

    function $(sel) { return document.querySelector(sel); }

    var dom = {
        overlay:        $("#connecting-overlay"),
        viewfinder:     $("#viewfinder"),
        chipCamera:     $("#chip-camera"),
        chipResolution: $("#chip-resolution"),
        chipFps:        $("#chip-fps"),
        chipExposure:   $("#chip-exposure"),
        chipBuffer:     $("#chip-buffer"),
        perfMetrics:    $("#perf-metrics"),
        cameraSelect:   $("#camera-select"),
        roiSelect:      $("#roi-select"),
        fpsHint:        $("#fps-hint"),
        slowdownRow:    $("#slowdown-presets"),
        discFps:        $("#disc-fps"),
        discShutter:    $("#disc-shutter"),
        discResolution: $("#disc-resolution"),
        discPlayback:   $("#disc-playback"),
        discFactor:     $("#disc-factor"),
        methodsText:    $("#methods-text"),
        copyCitationBtn:$("#copy-citation-btn"),
        autoExposureCb: $("#auto-exposure-cb"),
        exposureSlider: $("#exposure-slider"),
        exposureValue:  $("#exposure-value"),
        gainSlider:     $("#gain-slider"),
        gainValue:      $("#gain-value"),
        exposureSafety: $("#exposure-safety"),
        bufferText:     $("#buffer-text"),
        bufferBarFill:  $("#buffer-bar-fill"),
        durationRow:    $("#duration-presets"),
        outputDurValue: $("#output-dur-value"),
        outputDurSub:   $("#output-dur-sub"),
        recordBtn:      $("#record-btn"),
        savePanel:      $("#save-panel"),
        savePanelContent: $("#save-panel-content"),
        clipPreview:    $("#clip-preview"),
        clipVideo:      $("#clip-video"),
        clipDownload:   $("#clip-download"),
    };

    // ── Helpers ──────────────────────────────────────────────────────────────

    function apiUrl(path) {
        return BASE + path;
    }

    async function apiFetch(path, opts) {
        var resp = await fetch(apiUrl(path), opts);
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
    }

    function formatFactor(f) {
        return f === Math.floor(f) ? f + "x" : f.toFixed(1) + "x";
    }

    function getRoi() {
        return ROI_OPTIONS[state.roiPreset] || ROI_OPTIONS["Half Height (Fast)"];
    }

    function computeTargetFps() {
        return Math.min(getRoi().maxFps, PLAYBACK_FPS * state.slowdownFactor);
    }

    function computeActualFactor() {
        return computeTargetFps() / PLAYBACK_FPS;
    }

    function shutterDenominator(exposureMs) {
        if (exposureMs <= 0) return computeTargetFps();
        return Math.max(1, Math.round(1000.0 / exposureMs));
    }

    // ── Safe DOM helpers ─────────────────────────────────────────────────────

    function clearChildren(el) {
        while (el.firstChild) el.removeChild(el.firstChild);
    }

    function createEl(tag, className, text) {
        var el = document.createElement(tag);
        if (className) el.className = className;
        if (text != null) el.textContent = text;
        return el;
    }

    // ── UI Update Functions ──────────────────────────────────────────────────

    function updateHeaderChips() {
        // Camera chip
        if (state.connected) {
            var name = state.cameraName || "Camera";
            if (name.length > 24) name = name.substring(0, 24);
            dom.chipCamera.className = "status-chip chip-active";
            dom.chipCamera.textContent = name;
        } else {
            dom.chipCamera.className = "status-chip chip-danger";
            dom.chipCamera.textContent = "No Camera";
        }

        // Resolution chip
        var roi = getRoi();
        dom.chipResolution.textContent = roi.w + "\u00d7" + roi.h;

        // FPS chip
        var ratio = state.targetFps > 0 ? state.captureFps / state.targetFps : 0;
        var fpsCls = ratio >= 0.95 ? "chip-safe" : (ratio >= 0.80 ? "chip-warning" : "chip-danger");
        dom.chipFps.className = "status-chip " + fpsCls;
        dom.chipFps.textContent = Math.round(state.captureFps) + "/" + Math.round(state.targetFps) + " FPS";

        // Exposure chip
        if (state.autoExposure) {
            dom.chipExposure.className = "status-chip chip-active";
            dom.chipExposure.textContent = "Auto Exp";
        } else {
            var frameTime = state.targetFps > 0 ? 1000.0 / state.targetFps : 1000;
            var expRatio = state.exposureMs / frameTime;
            var expCls = expRatio > 1.0 ? "chip-danger" : (expRatio > 0.8 ? "chip-warning" : "chip-safe");
            dom.chipExposure.className = "status-chip " + expCls;
            dom.chipExposure.textContent = state.exposureMs.toFixed(1) + "ms";
        }

        // Buffer chip
        var bufPct = state.bufferFillPct;
        var bufCls = bufPct >= 100 ? "chip-safe" : (bufPct >= 50 ? "chip-active" : "chip-idle");
        dom.chipBuffer.className = "status-chip " + bufCls;
        dom.chipBuffer.textContent = state.bufferDurationSec.toFixed(1) + "s (" + Math.round(bufPct) + "%)";
    }

    function updatePerfMetrics() {
        var targetFps = state.targetFps;
        var capFps = state.captureFps;
        var fpsCls = capFps >= targetFps * 0.95 ? "val-ok" : "val-warn";

        // Build perf metrics using DOM methods
        clearChildren(dom.perfMetrics);
        dom.perfMetrics.appendChild(document.createTextNode("Target: "));
        var s1 = createEl("span", "val", Math.round(targetFps).toString());
        dom.perfMetrics.appendChild(s1);
        dom.perfMetrics.appendChild(document.createTextNode(" fps  |  Capture: "));
        var s2 = createEl("span", fpsCls, capFps.toFixed(1));
        dom.perfMetrics.appendChild(s2);
        dom.perfMetrics.appendChild(document.createTextNode(" fps  |  Preview: "));
        var s3 = createEl("span", "val", state.previewFps.toFixed(1));
        dom.perfMetrics.appendChild(s3);
        dom.perfMetrics.appendChild(document.createTextNode(" fps"));
    }

    function updateFpsHint() {
        var roi = getRoi();
        dom.fpsHint.textContent = "Max ~" + roi.maxFps + " FPS for " + state.roiPreset;
    }

    function updateSlowdownButtons() {
        var roi = getRoi();
        var btns = dom.slowdownRow.querySelectorAll(".preset-btn");
        btns.forEach(function (btn) {
            var factor = parseInt(btn.getAttribute("data-factor"), 10);
            var achievable = (PLAYBACK_FPS * factor) <= roi.maxFps;
            var active = (factor === state.slowdownFactor);
            btn.className = "preset-btn";
            if (active) btn.className += " preset-btn-active";
            if (!achievable) btn.className += " preset-btn-dim";
        });
    }

    function updateDisclosureCard() {
        var targetFps = computeTargetFps();
        var actualFactor = computeActualFactor();
        var roi = getRoi();
        var shutterN = shutterDenominator(state.exposureMs);

        dom.discFps.textContent = Math.round(targetFps) + " fps";
        dom.discShutter.textContent = "1/" + shutterN + "s";
        dom.discResolution.textContent = roi.w + "\u00d7" + roi.h + " px";
        dom.discPlayback.textContent = PLAYBACK_FPS + " fps";
        dom.discFactor.textContent = formatFactor(actualFactor);
    }

    function buildCitationText() {
        var targetFps = computeTargetFps();
        var actualFactor = computeActualFactor();
        var roi = getRoi();
        var shutterN = shutterDenominator(state.exposureMs);
        var factorStr = formatFactor(actualFactor);

        return (
            "Video was captured at " + Math.round(targetFps) + " fps using a MindVision GigE camera " +
            "(" + roi.w + "\u00d7" + roi.h + " px ROI) with a 1/" + shutterN + "s shutter speed and " +
            "played back at " + PLAYBACK_FPS + " fps, resulting in " + factorStr + " slow motion."
        );
    }

    function updateMethodsCitation() {
        dom.methodsText.textContent = buildCitationText();
    }

    function updateExposureSafety() {
        var el = dom.exposureSafety;
        if (state.autoExposure) {
            el.className = "safety-safe";
            el.textContent = "Auto-exposure active";
            return;
        }
        var frameTime = state.targetFps > 0 ? 1000.0 / state.targetFps : 1000;
        var ratio = state.exposureMs / frameTime;
        if (ratio > 1.0) {
            el.className = "safety-danger";
            el.textContent = "Exceeds frame time \u2014 motion blur guaranteed!";
        } else if (ratio > 0.8) {
            var rec = (frameTime * 0.8).toFixed(1);
            el.className = "safety-warning";
            el.textContent = state.exposureMs.toFixed(1) + "ms > " + rec + "ms recommended max";
        } else {
            el.className = "safety-safe";
            el.textContent = state.exposureMs.toFixed(1) + "ms \u2014 OK";
        }
    }

    function updateBufferBar() {
        var pct = Math.min(100, Math.round(state.bufferFillPct));
        dom.bufferText.textContent =
            state.bufferDurationSec.toFixed(1) + "s / " +
            state.bufferTargetSec.toFixed(1) + "s \u00b7 " + pct + "%";
        dom.bufferBarFill.style.width = pct + "%";
        if (pct >= 100) {
            dom.bufferBarFill.classList.add("full");
        } else {
            dom.bufferBarFill.classList.remove("full");
        }
    }

    function updateOutputDuration() {
        var actualFactor = computeActualFactor();
        var outputSec = Math.round(state.clipDurationSec * actualFactor);
        dom.outputDurValue.textContent = outputSec + " seconds";
        dom.outputDurSub.textContent =
            "of slow-motion video from " + state.clipDurationSec + "s of real footage";
    }

    function updateDurationButtons() {
        var btns = dom.durationRow.querySelectorAll(".dur-btn");
        btns.forEach(function (btn) {
            var dur = parseInt(btn.getAttribute("data-dur"), 10);
            btn.className = "dur-btn" + (dur === state.clipDurationSec ? " dur-btn-active" : "");
        });
    }

    function updateRecordButton() {
        var btn = dom.recordBtn;
        if (state.recording) {
            btn.className = "record-btn record-btn-saving";
            btn.textContent = "Saving...";
            btn.disabled = true;
            return;
        }
        if (!state.connected) {
            btn.className = "record-btn record-btn-disabled";
            btn.textContent = "Connect Camera First";
            btn.disabled = true;
            return;
        }
        if (!state.bufferIsFull) {
            btn.className = "record-btn record-btn-disabled";
            btn.textContent = "Buffering...";
            btn.disabled = true;
            return;
        }
        btn.className = "record-btn record-btn-ready";
        btn.textContent = "Save Slow-Mo Clip";
        btn.disabled = false;
    }

    function updateAllDerived() {
        updateFpsHint();
        updateSlowdownButtons();
        updateDisclosureCard();
        updateMethodsCitation();
        updateExposureSafety();
        updateOutputDuration();
        updateDurationButtons();
        updateRecordButton();
    }

    // ── Stream ───────────────────────────────────────────────────────────────

    function startStream() {
        dom.viewfinder.src = apiUrl("/stream");
    }

    // ── API: Fetch Config ────────────────────────────────────────────────────

    async function fetchConfig() {
        try {
            var data = await apiFetch("/api/config");
            // Update ROI_OPTIONS from server (single source of truth)
            if (data.roi_options && typeof data.roi_options === "object") {
                ROI_OPTIONS = data.roi_options;
                // Rebuild ROI select dropdown from server-authoritative values
                clearChildren(dom.roiSelect);
                Object.keys(ROI_OPTIONS).forEach(function (name) {
                    var opt = createEl("option", null, name);
                    opt.value = name;
                    if (name === state.roiPreset) opt.selected = true;
                    dom.roiSelect.appendChild(opt);
                });
            }
            if (Array.isArray(data.slowdown_presets)) {
                SLOWDOWN_PRESETS = data.slowdown_presets;
            }
            if (data.playback_fps != null) {
                PLAYBACK_FPS = data.playback_fps;
            }
        } catch (_e) {
            // Config fetch failed — keep the hardcoded defaults
        }
    }

    // ── API: Fetch Cameras ───────────────────────────────────────────────────

    async function fetchCameras() {
        try {
            var data = await apiFetch("/api/cameras");
            var cameras = data.cameras || [];
            clearChildren(dom.cameraSelect);
            if (cameras.length === 0) {
                var opt = createEl("option", null, "No cameras found");
                opt.value = "";
                dom.cameraSelect.appendChild(opt);
            } else {
                cameras.forEach(function (cam) {
                    var opt = createEl("option", null, cam);
                    opt.value = cam;
                    dom.cameraSelect.appendChild(opt);
                });
                // Auto-select first camera if none is connected yet
                if (!state.connected && cameras.length > 0) {
                    dom.cameraSelect.value = cameras[0];
                    state.cameraName = cameras[0];
                    sendSettings({ camera: cameras[0] });
                }
            }
        } catch (_e) {
            // Will retry on next status poll
        }
    }

    // ── API: Send Settings ───────────────────────────────────────────────────

    async function sendSettings(patch) {
        try {
            var data = await apiFetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(patch),
            });
            var s = data && data.settings;
            if (s && s.roi_preset) state.roiPreset = s.roi_preset;
            if (s && s.exposure_ms != null) state.exposureMs = s.exposure_ms;
            if (s && s.gain != null) state.gain = s.gain;
            if (s && s.auto_exposure != null) state.autoExposure = s.auto_exposure;
            if (data && data.target_fps != null) state.targetFps = data.target_fps;
        } catch (_e) {
            // Will catch up on next poll
        }
    }

    // ── API: Status Polling ──────────────────────────────────────────────────

    var firstStatusReceived = false;

    async function pollStatus() {
        try {
            if (!portDiscovered) {
                var found = await discoverPort();
                if (!found) throw new Error("no port");
            }
            var data = await apiFetch("/api/status");

            if (!firstStatusReceived) {
                firstStatusReceived = true;
                dom.overlay.classList.add("hidden");
                await fetchConfig();
                await fetchCameras();
                startStream();
            }

            state.connected = !!data.connected;
            if (data.settings) {
                var s = data.settings;
                if (s.roi_preset) state.roiPreset = s.roi_preset;
                if (s.exposure_ms != null) state.exposureMs = s.exposure_ms;
                if (s.gain != null) state.gain = s.gain;
                if (s.auto_exposure != null) state.autoExposure = s.auto_exposure;
                if (s.target_fps != null) state.targetFps = s.target_fps;
                if (s.slowdown_factor != null) state.slowdownFactor = s.slowdown_factor;
                if (s.clip_duration_sec != null) state.clipDurationSec = s.clip_duration_sec;
            }
            if (data.fps) {
                if (data.fps.capture != null) state.captureFps = data.fps.capture;
                if (data.fps.preview != null) state.previewFps = data.fps.preview;
                if (data.fps.target != null) state.targetFps = data.fps.target;
            }
            if (data.buffer) {
                if (data.buffer.duration_sec != null) state.bufferDurationSec = data.buffer.duration_sec;
                if (data.buffer.fill_pct != null) state.bufferFillPct = data.buffer.fill_pct;
                if (data.buffer.is_full != null) state.bufferIsFull = data.buffer.is_full;
            }
            if (data.settings && data.settings.clip_duration_sec != null) {
                state.bufferTargetSec = data.settings.clip_duration_sec;
            }

            syncControlsFromState();
            updateHeaderChips();
            updatePerfMetrics();
            updateBufferBar();
            updateAllDerived();
        } catch (_e) {
            // Server not ready yet
        }

        setTimeout(pollStatus, STATUS_POLL_MS);
    }

    function syncControlsFromState() {
        if (dom.roiSelect.value !== state.roiPreset) {
            dom.roiSelect.value = state.roiPreset;
        }
        if (document.activeElement !== dom.exposureSlider) {
            dom.exposureSlider.value = state.exposureMs;
            dom.exposureValue.textContent = state.exposureMs.toFixed(2);
        }
        if (document.activeElement !== dom.gainSlider) {
            dom.gainSlider.value = state.gain;
            dom.gainValue.textContent = state.gain.toFixed(1);
        }
        dom.autoExposureCb.checked = state.autoExposure;
    }

    // ── API: Record Flow ─────────────────────────────────────────────────────

    async function startRecording() {
        if (state.recording || !state.connected || !state.bufferIsFull) return;

        state.recording = true;
        state.recordState = "saving";
        updateRecordButton();
        dom.clipPreview.style.display = "none";
        dom.savePanel.style.display = "none";

        try {
            await apiFetch("/api/record", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    clip_duration_sec: state.clipDurationSec,
                    slowdown_factor: state.slowdownFactor,
                }),
            });
            _recordPollRetries = 0;
            pollRecordStatus();
        } catch (e) {
            state.recording = false;
            state.recordState = "error";
            state.recordError = e.message || "Record request failed";
            showRecordError(state.recordError);
            updateRecordButton();
        }
    }

    var _recordPollRetries = 0;
    var RECORD_POLL_MAX_RETRIES = 40; // 40 × 500ms = 20s max wait

    async function pollRecordStatus() {
        _recordPollRetries++;
        if (_recordPollRetries > RECORD_POLL_MAX_RETRIES) {
            // Python took too long or crashed — reset UI so operator can try again.
            state.recording = false;
            state.recordState = "idle";
            state.recordError = "Recording timed out — please try again.";
            showRecordError(state.recordError);
            updateRecordButton();
            return;
        }

        try {
            var data = await apiFetch("/api/record/status");
            state.recordState = data.state || "idle";

            if (state.recordState === "done") {
                state.recording = false;
                state.recordPath = data.path || "";
                showRecordSuccess();
                updateRecordButton();
                return;
            }

            if (state.recordState === "error") {
                state.recording = false;
                state.recordError = data.error || "Unknown error";
                showRecordError(state.recordError);
                updateRecordButton();
                return;
            }

            setTimeout(pollRecordStatus, RECORD_POLL_MS);
        } catch (_e) {
            setTimeout(pollRecordStatus, RECORD_POLL_MS);
        }
    }

    function showRecordSuccess() {
        var actualFactor = computeActualFactor();
        var outputSec = Math.round(state.clipDurationSec * actualFactor);
        var factorStr = formatFactor(actualFactor);

        // Build save panel with safe DOM methods
        clearChildren(dom.savePanelContent);
        var panel = createEl("div", "save-panel-saved");
        panel.appendChild(createEl("div", "save-check", "\u2705"));
        panel.appendChild(createEl("div", "save-title", "Saved!"));
        panel.appendChild(createEl("div", "save-subtitle",
            outputSec + " seconds of " + factorStr + " slow motion"));
        var anotherBtn = createEl("button", "save-another-btn", "\u21a9 Save Another Clip");
        anotherBtn.addEventListener("click", resetRecordFlow);
        panel.appendChild(anotherBtn);
        dom.savePanelContent.appendChild(panel);
        dom.savePanel.style.display = "block";

        // Show clip preview — fetch as blob to avoid cross-origin issues in WKWebView
        dom.clipPreview.style.display = "block";
        fetch(apiUrl("/api/record/download"))
            .then(function (res) { return res.blob(); })
            .then(function (blob) {
                var videoBlob = new Blob([blob], { type: "video/mp4" });
                var url = URL.createObjectURL(videoBlob);
                dom.clipVideo.src = url;
                dom.clipVideo.load();
            })
            .catch(function () {
                dom.clipVideo.src = apiUrl("/api/record/download");
            });
    }

    function showRecordError(msg) {
        clearChildren(dom.savePanelContent);
        dom.savePanelContent.appendChild(
            createEl("div", "save-panel-error", "\u274c " + msg)
        );
        dom.savePanel.style.display = "block";
    }

    function resetRecordFlow() {
        state.recording = false;
        state.recordState = "idle";
        state.recordPath = "";
        state.recordError = "";
        dom.savePanel.style.display = "none";
        dom.clipPreview.style.display = "none";
        dom.clipVideo.src = "";
        updateRecordButton();
    }

    // ── Event Handlers ───────────────────────────────────────────────────────

    function bindEvents() {
        dom.cameraSelect.addEventListener("change", function () {
            var cam = dom.cameraSelect.value;
            if (cam) {
                state.cameraName = cam;
                sendSettings({ camera: cam });
            }
        });

        dom.roiSelect.addEventListener("change", function () {
            state.roiPreset = dom.roiSelect.value;
            state.targetFps = computeTargetFps();
            sendSettings({ roi_preset: state.roiPreset });
            updateAllDerived();
            updateHeaderChips();
        });

        dom.slowdownRow.addEventListener("click", function (e) {
            var btn = e.target.closest(".preset-btn");
            if (!btn || btn.classList.contains("preset-btn-dim")) return;
            var factor = parseInt(btn.getAttribute("data-factor"), 10);
            state.slowdownFactor = factor;
            state.targetFps = computeTargetFps();
            sendSettings({ slowdown_factor: factor });
            updateAllDerived();
            updateHeaderChips();
        });

        dom.durationRow.addEventListener("click", function (e) {
            var btn = e.target.closest(".dur-btn");
            if (!btn) return;
            var dur = parseInt(btn.getAttribute("data-dur"), 10);
            state.clipDurationSec = dur;
            sendSettings({ clip_duration_sec: dur });
            updateAllDerived();
        });

        dom.autoExposureCb.addEventListener("change", function () {
            state.autoExposure = dom.autoExposureCb.checked;
            sendSettings({ auto_exposure: state.autoExposure });
            updateExposureSafety();
            updateHeaderChips();
        });

        dom.exposureSlider.addEventListener("input", function () {
            var val = parseFloat(dom.exposureSlider.value);
            state.exposureMs = val;
            dom.exposureValue.textContent = val.toFixed(2);
            updateExposureSafety();
            updateDisclosureCard();
            updateMethodsCitation();
            updateHeaderChips();
        });
        dom.exposureSlider.addEventListener("change", function () {
            sendSettings({ exposure_ms: state.exposureMs });
        });

        dom.gainSlider.addEventListener("input", function () {
            var val = parseFloat(dom.gainSlider.value);
            state.gain = val;
            dom.gainValue.textContent = val.toFixed(1);
        });
        dom.gainSlider.addEventListener("change", function () {
            sendSettings({ gain: state.gain });
        });

        dom.recordBtn.addEventListener("click", function () {
            if (!dom.recordBtn.disabled) {
                startRecording();
            }
        });

        // Reveal clip in Finder (WKWebView doesn't support file downloads)
        dom.clipDownload.addEventListener("click", function () {
            fetch(apiUrl("/api/record/reveal"), { method: "POST" })
                .catch(function () {});
        });

        dom.copyCitationBtn.addEventListener("click", function () {
            var text = buildCitationText();
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(function () {
                    dom.copyCitationBtn.textContent = "Copied \u2713";
                    setTimeout(function () {
                        dom.copyCitationBtn.textContent = "Copy";
                    }, 2000);
                });
            } else {
                var range = document.createRange();
                range.selectNodeContents(dom.methodsText);
                var sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
                dom.copyCitationBtn.textContent = "Select All";
                setTimeout(function () {
                    dom.copyCitationBtn.textContent = "Copy";
                }, 2000);
            }
        });
    }

    // ── Initialization ───────────────────────────────────────────────────────

    function init() {
        state.targetFps = computeTargetFps();
        updateAllDerived();
        updateHeaderChips();
        updatePerfMetrics();
        updateBufferBar();
        bindEvents();
        pollStatus();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

})();

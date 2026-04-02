## Context

The app is a single-file Gradio `app.py` (~750 lines) with a three-column dark-themed layout. The current speed control uses two separate `gr.Slider` components (`target_fps_slider`, `playback_fps_slider`) across different tabs. Settings are managed via a `current_settings` dict and a `settings_lock` thread lock. The `HighSpeedRecorder` consumes `target_fps` and `playback_fps` directly — these values don't change, only how the UI derives them changes. Reference design is in `interface.pen`.

## Goals / Non-Goals

**Goals:**
- Replace FPS sliders with a `slowdown_factor` selector that auto-computes `target_fps` and `playback_fps`
- Surface camera settings below the selector for in-app documentation
- Provide a one-tap clipboard copy of a formatted methods citation
- Redesign the save panel to show output duration before saving and a post-save transition state
- Add a collapsible Advanced Settings panel for manual exposure/gain override
- Simplify the header to show a camera connection status chip

**Non-Goals:**
- Changes to `HighSpeedRecorder` or camera SDK layer
- Mobile layout or responsive design
- User accounts, saving settings between sessions
- Video trimming or editing after save

## Decisions

### D1: Slowdown factor as derived input, not stored state

The `HighSpeedRecorder` expects `target_fps` and `playback_fps`. Rather than adding a new `slowdown_factor` state variable and changing the recorder API, the UI converts the user's selected multiplier into FPS values before storing them in `current_settings`.

Formula: `target_fps = min(roi_max_fps[preset], playback_fps * slowdown_factor)`. If the ROI can't support the requested slowdown (e.g., 32× at Full Resolution), the UI clamps and shows the actual achieved factor.

**Alternatives considered:** Storing `slowdown_factor` in `current_settings` and updating the recorder API — rejected because it changes a stable interface unnecessarily.

### D2: Preset buttons as radio-style HTML buttons, not `gr.Radio`

Gradio's `gr.Radio` doesn't support the large, styled button appearance needed. The presets will be rendered as a `gr.HTML` component with `<button>` tags, and clicks captured via a `gr.State` + `gr.Textbox(visible=False)` bridge pattern (standard Gradio custom-click workaround).

**Alternatives considered:** `gr.Button` row — rejected because styling active/inactive states requires per-button updates (5 round-trips vs. 1 HTML update).

### D3: Methods citation generated server-side, copied via JS

The "Copy for Methods Section" button triggers a Gradio event that returns the citation string. Client-side copy is executed via `gr.HTML` injecting a small `<script>` that calls `navigator.clipboard.writeText(...)`. This avoids Pyperclip or subprocess dependencies.

### D4: Post-save state as CSS class toggle on the save column

Rather than rebuilding the save panel as a new component, the save column will use a `gr.HTML` block that renders either the "buffer/duration/save" state or the "saved/download/reset" state. A single Python function returns the full HTML for whichever state is active.

### D5: Advanced Settings as `gr.Accordion`

Gradio has a native `gr.Accordion` component — use it rather than a custom HTML accordion. It handles open/close state natively and is accessible. The accordion sits below the preset section inside the controls column.

## Risks / Trade-offs

- **Slowdown clamping UX** → If a student picks 32× but the ROI only supports 16×, they see a different actual factor than selected. Mitigation: show the actual achieved factor prominently in the settings disclosure card and gray out presets that aren't achievable at the current ROI.
- **JS clipboard in Gradio** → `navigator.clipboard` requires HTTPS or localhost. In the school lab (likely localhost), this works. Over HTTP on a LAN, it silently fails. Mitigation: show the citation text in a selectable text area as fallback.
- **HTML button bridge pattern** → Custom HTML buttons require a hidden Gradio input to route events back to Python. This pattern is well-established in Gradio but adds ~20 lines of boilerplate. No functional risk.
- **Post-save state reset** → "Save Another Clip" must reset the buffer display while the circular buffer continues filling in the background. Since the buffer runs independently in the recorder thread, only the UI state needs resetting — low risk.

## Open Questions

- Should the 5-preset set (2×/4×/8×/16×/32×) be hardcoded or derived from `roi_max_fps`? Hardcoded is simpler; derived would auto-grey unavailable presets. Decision: hardcode the 5 presets, grey out those exceeding current ROI max FPS.

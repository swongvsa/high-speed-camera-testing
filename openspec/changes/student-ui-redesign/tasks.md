## 1. Slowdown Preset Control

- [x] 1.1 Add `SLOWDOWN_PRESETS = [2, 4, 8, 16, 32]` constant and `PLAYBACK_FPS_DEFAULT = 30` to `app.py`
- [x] 1.2 Add `slowdown_factor_state = gr.State(8)` and replace `target_fps_slider` + `playback_fps_slider` with a hidden `gr.Number(visible=False)` for each value
- [x] 1.3 Implement `compute_fps_from_slowdown(factor, roi_preset)` → returns `(target_fps, playback_fps, actual_factor)` using `roi_max_fps` dict, clamping target to ROI max
- [x] 1.4 Render slowdown preset buttons as `gr.HTML` with active/dimmed states; add hidden `gr.Textbox` bridge for capturing click events via JS `onclick` → `gradio_client` pattern
- [x] 1.5 Wire preset button clicks to update `slowdown_factor_state`, recompute FPS, and update `current_settings`
- [x] 1.6 Update `combined_update()` to call `compute_fps_from_slowdown()` instead of reading the removed sliders

## 2. Settings Disclosure Card

- [x] 2.1 Add `render_settings_disclosure_html(target_fps, shutter_ms, roi_preset, playback_fps, actual_factor)` renderer function
- [x] 2.2 Add `settings_disclosure_display = gr.HTML(...)` component in the controls column, below preset buttons
- [x] 2.3 Wire disclosure to update on every `combined_update()` call

## 3. Methods Citation

- [x] 3.1 Add `render_methods_citation(target_fps, shutter_ms, roi_preset, playback_fps, actual_factor, camera_name)` → returns formatted citation string
- [x] 3.2 Add `render_methods_card_html(citation_str)` → returns the green-bordered card HTML with Copy button
- [x] 3.3 Add `methods_card_display = gr.HTML(...)` component below disclosure card
- [x] 3.4 Implement clipboard copy via injected `<script>` in the Copy button's `onclick`: `navigator.clipboard.writeText(...)` with 2s "Copied ✓" feedback; fallback `<textarea>` when clipboard unavailable
- [x] 3.5 Wire methods card to update on `combined_update()` calls

## 4. Advanced Settings Accordion

- [x] 4.1 Replace `auto_exposure_checkbox`, `exposure_slider`, `gain_slider` with a `gr.Accordion("Advanced Settings", open=False)` wrapping the same controls
- [x] 4.2 Add shutter speed display showing auto-calculated value with "auto-set from N× preset · tap to override" note
- [x] 4.3 Wire accordion controls into existing `combined_update()` inputs list (no logic change, just layout move)

## 5. Save Panel Redesign

- [x] 5.1 Replace `clip_duration_slider` with three `gr.Button` components (2s, 5s, 10s) using radio-style active state management
- [x] 5.2 Add `render_output_duration_html(clip_duration_sec, slowdown_factor)` → shows "YOUR CLIP WILL BE N seconds" card
- [x] 5.3 Add `output_duration_display = gr.HTML(...)` above the save button
- [x] 5.4 Wire duration buttons to update `clip_duration_sec` state and refresh `output_duration_display`

## 6. Post-Save State

- [x] 6.1 Add `render_save_panel_saved_html(output_duration_sec, slowdown_factor)` → returns full HTML for post-save state (checkmark, "Saved!", duration, preview tap, Download, Save Another)
- [x] 6.2 Add `save_panel_html = gr.HTML(render_save_panel_default_html(...))` as the save panel container; replace the existing button/video/download layout
- [x] 6.3 Update `on_record_click()` to return `render_save_panel_saved_html(...)` on success and `render_save_panel_default_html(...)` on failure
- [x] 6.4 Add "Save Another Clip" click handler (via JS bridge) that resets `save_panel_html` to default state

## 7. Camera Connection Status Chip

- [x] 7.1 Update `render_camera_chip()` to include a "Fix Connection" inline link when disconnected (renders as `<a href="#" onclick="...">` that scrolls to/exposes a help text block)
- [x] 7.2 Add a collapsed `gr.Accordion("Camera Connection Help")` at the bottom of the page with the IP troubleshooting steps from `fix_camera_ip.py`

## 8. Cleanup

- [x] 8.1 Remove the `gr.TabItem("⚡ Capture")` and `gr.TabItem("📷 Exposure")` tab structure from the controls column (replaced by preset + accordion layout)
- [x] 8.2 Remove `playback_fps_slider` component and all references
- [x] 8.3 Remove `target_fps_slider` component and all references
- [x] 8.4 Remove `gr.Tabs()` wrapper from controls column
- [x] 8.5 Update `DARK_CSS` with new styles for preset buttons, methods card, output duration card, and post-save state

## 9. Testing

- [ ] 9.1 Manually verify: selecting each preset updates disclosure card with correct FPS/shutter/resolution/playback
- [ ] 9.2 Manually verify: Copy button writes correct citation to clipboard (test on localhost)
- [ ] 9.3 Manually verify: 32× preset is dimmed at "Full Resolution" ROI, active at "Half Height (Fast)" ROI
- [ ] 9.4 Manually verify: save panel shows correct output duration (5s × 8× = 40s)
- [ ] 9.5 Manually verify: post-save state appears after saving, "Save Another Clip" resets to default state
- [x] 9.6 Run existing test suite: `cd src && pytest`

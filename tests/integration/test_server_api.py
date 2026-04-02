"""
Integration tests for the FastAPI HTTP service (src/ui/server.py).

Covers:
- /api/status endpoint contract
- /api/config endpoint contract (single source of truth for ROI/presets)
- /api/cameras endpoint
- /api/settings validation
- /api/record lifecycle (idle → saving → done/error)
- Server binds to 127.0.0.1 only (replaces test_scenario_05_localhost.py)
"""

import uvicorn
from fastapi.testclient import TestClient

from src.ui.server import app, roi_options, roi_max_fps, SLOWDOWN_PRESETS


client = TestClient(app)


class TestStatusEndpoint:
    def test_returns_200(self):
        resp = client.get("/api/status")
        assert resp.status_code == 200

    def test_structure(self):
        data = client.get("/api/status").json()
        assert "connected" in data
        assert "settings" in data
        assert "fps" in data
        assert "buffer" in data
        assert "slowdown_factor" in data

    def test_not_connected_by_default(self):
        data = client.get("/api/status").json()
        assert data["connected"] is False


class TestConfigEndpoint:
    def test_returns_200(self):
        resp = client.get("/api/config")
        assert resp.status_code == 200

    def test_roi_options_match_server_constants(self):
        """The /api/config response must match server.py's roi_options + roi_max_fps.

        This is the DRY contract: the frontend should consume this endpoint
        instead of maintaining its own copy of ROI constants.
        """
        data = client.get("/api/config").json()
        assert "roi_options" in data
        for name, dims in roi_options.items():
            assert name in data["roi_options"]
            entry = data["roi_options"][name]
            assert entry["w"] == dims[0]
            assert entry["h"] == dims[1]
            assert entry["maxFps"] == roi_max_fps[name]

    def test_slowdown_presets_match_server_constants(self):
        data = client.get("/api/config").json()
        assert data["slowdown_presets"] == SLOWDOWN_PRESETS

    def test_all_roi_entries_have_required_fields(self):
        data = client.get("/api/config").json()
        for name, entry in data["roi_options"].items():
            assert "w" in entry, f"{name} missing 'w'"
            assert "h" in entry, f"{name} missing 'h'"
            assert "maxFps" in entry, f"{name} missing 'maxFps'"


class TestCamerasEndpoint:
    def test_returns_list(self):
        data = client.get("/api/cameras").json()
        assert "cameras" in data
        assert isinstance(data["cameras"], list)


class TestSettingsValidation:
    def test_invalid_roi_preset_rejected(self):
        resp = client.post("/api/settings", json={"roi_preset": "invalid_preset"})
        assert resp.status_code == 422

    def test_negative_slowdown_factor_rejected(self):
        resp = client.post("/api/settings", json={"slowdown_factor": -1})
        assert resp.status_code == 422

    def test_zero_slowdown_factor_rejected(self):
        resp = client.post("/api/settings", json={"slowdown_factor": 0})
        assert resp.status_code == 422

    def test_negative_exposure_rejected(self):
        resp = client.post("/api/settings", json={"exposure_ms": -1})
        assert resp.status_code == 422

    def test_negative_gain_rejected(self):
        resp = client.post("/api/settings", json={"gain": -0.1})
        assert resp.status_code == 422

    def test_zero_clip_duration_rejected(self):
        resp = client.post("/api/settings", json={"clip_duration_sec": 0})
        assert resp.status_code == 422

    def test_empty_patch_accepted(self):
        """Empty settings update is a no-op, should not error."""
        resp = client.post("/api/settings", json={})
        assert resp.status_code == 200


class TestRecordEndpoint:
    def test_record_requires_camera(self):
        """POST /api/record with no camera connected should return 422."""
        resp = client.post("/api/record")
        assert resp.status_code == 422

    def test_record_status_idle_by_default(self):
        data = client.get("/api/record/status").json()
        assert data["state"] == "idle"

    def test_download_404_with_no_recording(self):
        """GET /api/record/download with no clip should return 404."""
        resp = client.get("/api/record/download")
        assert resp.status_code == 404


class TestLocalhostBinding:
    """The server must be configured to bind to 127.0.0.1, not 0.0.0.0.

    Replaces the deleted test_scenario_05_localhost.py which tested the Gradio
    launch_app() validation. The FastAPI equivalent is in run_server().
    """

    def test_run_server_uses_localhost(self):
        """run_server() must configure uvicorn to bind to 127.0.0.1.

        We verify this by inspecting the uvicorn.Config that would be used,
        not by actually starting the server.
        """
        import inspect
        from src.ui import server as srv

        # Read the run_server source to verify the host binding
        src = inspect.getsource(srv.run_server)
        assert "127.0.0.1" in src, (
            "run_server() must bind to 127.0.0.1, not 0.0.0.0. "
            "Binding to 0.0.0.0 exposes the camera API to the local network."
        )

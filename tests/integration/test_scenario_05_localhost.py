"""
Integration test for Scenario 5: Localhost-only access.

Reference: specs/001-using-gradio-as/quickstart.md Scenario 5
Maps to FR-012 (localhost-only security)
"""

from typing import Any, cast
import pytest

from src.ui.app import launch_app


def test_localhost_enforcement():
    """
    Scenario 5: Server only accepts connections from 127.0.0.1.
    """
    # Valid: localhost only
    # (Don't actually launch, just test validation)
    # This would succeed if we called launch_app(cast(Any, None), server_name="127.0.0.1")

    # Invalid: external server_name
    with pytest.raises(ValueError, match="localhost only"):
        launch_app(cast(Any, None), server_name="0.0.0.0")

    with pytest.raises(ValueError, match="localhost only"):
        launch_app(cast(Any, None), server_name="192.168.1.100")


def test_share_disabled():
    """Public sharing must be disabled"""
    # Invalid: share=True
    with pytest.raises(ValueError, match="sharing.*not allowed"):
        launch_app(cast(Any, None), share=True)


def test_default_localhost_settings():
    """Default settings enforce localhost"""
    # The default server_name should be "127.0.0.1"
    # This test verifies the function signature
    import inspect

    sig = inspect.signature(launch_app)

    # Check defaults
    assert sig.parameters["server_name"].default == "127.0.0.1"
    assert sig.parameters["share"].default == False

"""
Error display utilities for Gradio UI.
Provides user-friendly error components.
Maps to FR-004 (friendly error messages).
"""

import gradio as gr


def display_error(message: str):
    """
    Display user-friendly error in Gradio UI.

    Args:
        message: Error message (user-friendly, no stack traces)

    Returns:
        Gradio Error component for display

    Contract:
        - FR-004: Messages must be clear and actionable
        - No technical details or stack traces
        - Messages suggest recovery actions
    """
    return gr.Error(message)


def display_warning(message: str):
    """
    Display warning message in Gradio UI.

    Args:
        message: Warning message

    Returns:
        Gradio Warning component for display
    """
    return gr.Warning(message)


def display_info(message: str):
    """
    Display informational message in Gradio UI.

    Args:
        message: Info message

    Returns:
        Gradio Info component for display
    """
    return gr.Info(message)

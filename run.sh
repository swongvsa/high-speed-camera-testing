#!/bin/bash

# High-Speed Camera Testing - Startup Script for macOS/Linux
# This script will attempt to use 'uv' if installed, otherwise fallback to '.venv'.

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if command -v uv &> /dev/null
then
    echo "Starting application with uv..."
    uv run python main.py "$@"
else
    if [ -d ".venv" ]; then
        echo "Starting application with virtual environment (.venv)..."
        source .venv/bin/activate
        python main.py "$@"
    else
        echo "Error: Virtual environment (.venv) not found and 'uv' is not installed."
        echo ""
        echo "Please set up your environment first:"
        echo "Option A (Recommended): Install 'uv' from https://astral.sh/uv"
        echo "Option B: Run 'python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]'"
        exit 1
    fi
fi

#!/usr/bin/env bash
set -e

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment with uv..."
    uv venv "$VENV_DIR"

    echo "Activating environment and installing dependencies..."
    source "$VENV_DIR/bin/activate"

    if ! uv pip install fastapi uvicorn huggingface_hub; then
        echo "Network or installation error detected with uv. Trying fallback to standard pip..."
        pip install fastapi uvicorn huggingface_hub || {
            echo "Warning: Package installation failed, trying to run with existing environment..."
        }
    fi
else
    echo "Environment already exists. Skipping installation."
    source "$VENV_DIR/bin/activate"
fi

echo "Starting application..."
exec python main.py

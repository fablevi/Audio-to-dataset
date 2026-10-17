#!/usr/bin/env bash
set -e

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment with uv..."
    uv venv "$VENV_DIR"

    echo "Activating environment and installing dependencies..."
    source "$VENV_DIR/bin/activate"

    if ! uv pip install torch transformers librosa pillow numpy huggingface_hub fastapi uvicorn tensorflow tensorflow_hub "setuptools<74"; then
        echo "Network or installation error detected with uv. Trying fallback to standard pip..."
        pip install torch transformers librosa pillow numpy huggingface_hub fastapi uvicorn tensorflow tensorflow_hub "setuptools<74" || {
            echo "Warning: Package installation failed, trying to run with existing environment..."
        }
    fi
else
    echo "Environment already exists. Ensuring correct setuptools version..."
    source "$VENV_DIR/bin/activate"
    # Biztosítjuk, hogy a meglévő venv-ben is a kompatibilis setuptools legyen
    uv pip install "setuptools<74" || pip install "setuptools<74" || true
fi

echo "Starting application..."
exec python main.py
#!/usr/bin/env bash
# One-click setup: create venv and install dev dependencies.
# Usage: bash scripts/setup_env.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"

echo "[setup] repo root: $REPO_ROOT"

if [ -d "$VENV_DIR" ]; then
    echo "[setup] .venv already exists at $VENV_DIR — skipping creation."
else
    echo "[setup] creating venv at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

echo "[setup] activating venv and installing dependencies ..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install -U pip --quiet
python -m pip install -r "$REPO_ROOT/requirements-dev.txt" --quiet

echo "[setup] installed packages:"
# Avoid `head` here: with `pipefail` it can trigger a broken pipe error and fail the script.
python -m pip list --format=columns | sed -n '1,20p'

echo ""
echo "[setup] done.  Activate with:"
echo "  source $VENV_DIR/bin/activate"

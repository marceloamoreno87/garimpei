#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BACKEND_DIR="$PROJECT_DIR/apps/backend"
if ! command -v uv >/dev/null 2>&1; then
    echo "uv: expected version documented in F02 versions.md" >&2
    exit 64
fi
if [ ! -f "$BACKEND_DIR/pyproject.toml" ] || [ ! -f "$BACKEND_DIR/uv.lock" ] || [ ! -f "$BACKEND_DIR/.python-version" ]; then
    echo "Backend scaffold/lock absent; prepare the Python foundation first." >&2
    exit 64
fi
for REQUIRED_TOOL in git node; do
    if ! command -v "$REQUIRED_TOOL" >/dev/null 2>&1; then
        echo "$REQUIRED_TOOL: expected tool prepared for the Garimpei harness" >&2
        exit 64
    fi
done
read -r REQUIRED_PYTHON < "$BACKEND_DIR/.python-version"
if ! uv python find --no-python-downloads "$REQUIRED_PYTHON" >/dev/null 2>&1; then
    echo "Python $REQUIRED_PYTHON: expected interpreter prepared explicitly with uv python install" >&2
    exit 64
fi
export UV_PYTHON_DOWNLOADS=never
if ! command -v docker >/dev/null 2>&1; then
    echo "docker: expected Docker with Compose" >&2
    exit 64
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "docker compose: expected available Compose plugin" >&2
    exit 64
fi
uv sync --project "$BACKEND_DIR" --locked --all-groups
exec uv run --project "$BACKEND_DIR" --frozen --no-sync python -m garimpei.infra.runtime.cli init "$@"

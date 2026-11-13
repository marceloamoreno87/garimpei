#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
BACKEND_DIR="$PROJECT_DIR/apps/backend"
if ! command -v uv >/dev/null 2>&1; then
    echo "uv: expected version documented in F02 versions.md" >&2
    exit 64
fi
if [ ! -f "$BACKEND_DIR/pyproject.toml" ] || [ ! -f "$BACKEND_DIR/uv.lock" ] || [ ! -f "$BACKEND_DIR/.python-version" ]; then
    echo "Backend scaffold/lock absent; prepare the Python foundation first." >&2
    exit 64
fi
read -r REQUIRED_PYTHON < "$BACKEND_DIR/.python-version"
if ! uv python find --no-python-downloads "$REQUIRED_PYTHON" >/dev/null 2>&1; then
    echo "Python $REQUIRED_PYTHON: expected interpreter prepared explicitly with uv python install" >&2
    exit 64
fi
export UV_PYTHON_DOWNLOADS=never
exec uv run --project "$BACKEND_DIR" --frozen --no-sync python -m garimpei.infra.runtime.cli migrate "$@"

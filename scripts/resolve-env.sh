#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [ "${GARIMPEI_RUNTIME:-docker}" = host ]; then
    exec "$BASH" "$PROJECT_DIR/scripts/legacy/resolve-env.sh" "$@"
fi
exec "$BASH" "$PROJECT_DIR/scripts/docker-runtime.sh" resolve "$@"

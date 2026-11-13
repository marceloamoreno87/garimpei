#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [ "${GARIMPEI_RUNTIME:-docker}" = host ]; then
    exec "$PROJECT_DIR/scripts/legacy/migrate-dev.sh" "$@"
fi
exec "$PROJECT_DIR/scripts/docker-runtime.sh" migrate "$@"

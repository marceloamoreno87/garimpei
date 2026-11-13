#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
exec "$BASH" "$PROJECT_DIR/scripts/docker-runtime.sh" quality "$@"

#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [ "${1:-}" = --test-display ]; then
 exec "$PROJECT_DIR/scripts/docker-runtime.sh" display-test
fi
[ -z "${1:-}" ] || { echo 'Expected facebook-login.sh [--test-display]' >&2; exit 64; }
exec "$PROJECT_DIR/scripts/docker-runtime.sh" login

#!/usr/bin/env bash
# Host controller: requires shell, standard Unix utilities and Docker/Compose only.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
operation="${1:?operation required}"; shift
[ -f "$PROJECT_DIR/apps/backend/uv.lock" ] || { echo 'Backend scaffold/lock absent' >&2; exit 64; }
command -v docker >/dev/null || { echo 'docker: expected Docker with Compose' >&2; exit 64; }
docker compose version >/dev/null
[ -n "${GARIMPEI_ENV_FILE:-}" ] && [ -f "$GARIMPEI_ENV_FILE" ] || { echo 'GARIMPEI_ENV_FILE: expected absolute private data file' >&2; exit 64; }
case "$GARIMPEI_ENV_FILE" in /*) ;; *) echo 'GARIMPEI_ENV_FILE: expected absolute path' >&2; exit 64;; esac
[ "$(stat -c '%a' "$GARIMPEI_ENV_FILE")" = 600 ] || { echo 'GARIMPEI_ENV_FILE: expected mode 0600' >&2; exit 64; }
value() { awk -v key="$1" '$0 ~ "^"key"=" { sub("^[^=]*=", ""); gsub(/^['\''"]|['\''"]$/, ""); print; exit }' "$GARIMPEI_ENV_FILE"; }
export GARIMPEI_ENV="${GARIMPEI_ENV:-$(value GARIMPEI_ENV)}"
GARIMPEI_ENV="${GARIMPEI_ENV:-dev}"
export GARIMPEI_INSTANCE="${GARIMPEI_INSTANCE:-$(value GARIMPEI_INSTANCE)}"
if [ -z "$GARIMPEI_INSTANCE" ] && [ "$GARIMPEI_ENV" = dev ]; then GARIMPEI_INSTANCE="docker_$(printf '%s' "$PROJECT_DIR" | cksum | awk '{print $1}')"; fi
[[ "$GARIMPEI_INSTANCE" =~ ^[a-z0-9_]{1,40}$ ]] || { echo 'GARIMPEI_INSTANCE: expected [a-z0-9_]{1,40}' >&2; exit 64; }
[[ "$GARIMPEI_ENV" = dev || "$GARIMPEI_ENV" = eval ]] || { echo 'GARIMPEI_ENV: expected dev or eval' >&2; exit 64; }
export GARIMPEI_ENVIRONMENT_ID="${GARIMPEI_ENV}_${GARIMPEI_INSTANCE}" GARIMPEI_CHECKOUT="$PROJECT_DIR"
export GARIMPEI_IMAGE_REVISION="${GARIMPEI_IMAGE_REVISION:-f23-$GARIMPEI_ENVIRONMENT_ID}"
export GARIMPEI_STATE_DIR="$PROJECT_DIR/.runtime"
export GARIMPEI_PRIVATE_DIR="${GARIMPEI_PRIVATE_DIR:-$HOME/.local/share/garimpei/docker/$GARIMPEI_ENVIRONMENT_ID}"
case "$GARIMPEI_PRIVATE_DIR" in /*) ;; *) echo 'Private directory must be absolute' >&2; exit 64;; esac
GARIMPEI_PRIVATE_DIR="$(realpath -m -- "$GARIMPEI_PRIVATE_DIR")"
case "$GARIMPEI_PRIVATE_DIR" in /|/tmp|/home|/etc|/usr|/var|"$HOME"|"$PROJECT_DIR"|"$PROJECT_DIR"/*) echo 'Expected dedicated private directory outside checkout' >&2; exit 64;; esac
private_owner="$GARIMPEI_PRIVATE_DIR/.garimpei-owner"
expected_owner="$(printf '%s\n%s' "$PROJECT_DIR" "$GARIMPEI_ENVIRONMENT_ID")"
if [ -f "$private_owner" ]; then
 [ "$(cat "$private_owner")" = "$expected_owner" ] || { echo 'Private directory ownership mismatch' >&2; exit 64; }
elif [ -d "$GARIMPEI_PRIVATE_DIR" ] && [ -n "$(ls -A "$GARIMPEI_PRIVATE_DIR")" ]; then
 echo 'Private directory has unverified existing content; use adoption procedure' >&2; exit 64
fi
export GARIMPEI_GPU_DIR="${GARIMPEI_GPU_DIR:-$HOME/.local/share/garimpei}"
export GARIMPEI_UID="$(id -u)" GARIMPEI_GID="$(id -g)"
export GARIMPEI_DOCKER_GID="$(stat -c %g /var/run/docker.sock)"
seed=$((18000 + $(printf '%s' "$PROJECT_DIR:$GARIMPEI_ENVIRONMENT_ID" | cksum | awk '{print $1}') % 20000))
export GARIMPEI_WEB_PORT="${GARIMPEI_WEB_PORT:-$(value GARIMPEI_WEB_PORT)}" GARIMPEI_PG_PORT="${GARIMPEI_PG_PORT:-$(value GARIMPEI_PG_PORT)}" GARIMPEI_WAHA_PORT="${GARIMPEI_WAHA_PORT:-$(value GARIMPEI_WAHA_PORT)}"
GARIMPEI_WEB_PORT="${GARIMPEI_WEB_PORT:-$seed}"; GARIMPEI_PG_PORT="${GARIMPEI_PG_PORT:-$((seed+1))}"; GARIMPEI_WAHA_PORT="${GARIMPEI_WAHA_PORT:-$((seed+2))}"
export GARIMPEI_AI_PORT="${GARIMPEI_AI_PORT:-$((seed+3))}" GARIMPEI_DB_NAME="garimpei_$GARIMPEI_ENVIRONMENT_ID"
instance_dir="$GARIMPEI_STATE_DIR/$GARIMPEI_ENVIRONMENT_ID"
export GARIMPEI_DISPOSABLE=false
if [ -f "$instance_dir/docker-disposable" ]; then GARIMPEI_DISPOSABLE=true; fi
mkdir -p "$instance_dir" "$GARIMPEI_PRIVATE_DIR" "$GARIMPEI_GPU_DIR"
chmod 700 "$instance_dir" "$GARIMPEI_PRIVATE_DIR"
printf '%s\n' "$expected_owner" > "$private_owner"
chmod 600 "$private_owner"
for name in media integrations backups facebook-profile; do mkdir -p "$GARIMPEI_PRIVATE_DIR/$name"; chmod 700 "$GARIMPEI_PRIVATE_DIR/$name"; done
export GARIMPEI_RUN_ID="${GARIMPEI_RUN_ID:-$(cat "$instance_dir/run-id" 2>/dev/null || true)}"
if [ -z "$GARIMPEI_RUN_ID" ]; then GARIMPEI_RUN_ID="$(cat /proc/sys/kernel/random/uuid)"; printf '%s' "$GARIMPEI_RUN_ID" > "$instance_dir/run-id"; fi
compose() { docker compose --env-file "$GARIMPEI_ENV_FILE" -p "garimpei-$GARIMPEI_ENVIRONMENT_ID" -f "$PROJECT_DIR/compose.yaml" "$@"; }
# Canonical source file contains only read-only ownership checks.
source "$PROJECT_DIR/scripts/docker-ownership.sh"
verify() { verify_docker_ownership; }

exec 9>"$instance_dir/docker-operation.lock"
flock -n 9 || { echo 'Another lifecycle operation owns this environment' >&2; exit 1; }
# All mutating operations, including AI/tools dispatch, share this preflight.
if [ "$operation" != resolve ]; then verify; fi
case "$operation" in
 quality-detached)
  compose --profile tools run -d --no-deps --name "garimpei-$GARIMPEI_ENVIRONMENT_ID-quality-journey" quality sleep infinity ;;
 quality)
  compose --profile tools build quality
  compose --profile tools run --rm --no-deps quality "$@" ;;
 resolve) printf '%s database=%s web=%s postgres=%s waha=%s\n' "$GARIMPEI_ENVIRONMENT_ID" "$GARIMPEI_DB_NAME" "$GARIMPEI_WEB_PORT" "$GARIMPEI_PG_PORT" "$GARIMPEI_WAHA_PORT" ;;
 login|display-test)
  verify
  [ -n "${DISPLAY:-}" ] && [ -d /tmp/.X11-unix ] || { echo "Display unavailable: prepare WSLg/X11; login remains required" >&2; exit 64; }
  compose stop --timeout 30 worker
  trap 'compose start worker >/dev/null' EXIT
  display_args=(-e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro)
  if [ -d /mnt/wslg ]; then display_args+=(-v /mnt/wslg:/mnt/wslg:ro -e WAYLAND_DISPLAY -e XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir); fi
  compose --profile tools run --rm "${display_args[@]}" manage "$operation"
  ;;
 init)
  case "${1:-}" in
   --prepare-ai) exec "$PROJECT_DIR/scripts/docker-ai.sh" prepare ;;
   --recover-ai) exec "$PROJECT_DIR/scripts/docker-ai.sh" recover ;;
   ''|--disposable) ;;
   *) echo 'Expected init [--disposable|--prepare-ai|--recover-ai]' >&2; exit 64;;
  esac
  verify
  if compose exec -T web python -m garimpei.infra.runtime.container_entrypoint ready >/dev/null 2>&1; then
   echo "Ready $GARIMPEI_ENVIRONMENT_ID: already running at http://127.0.0.1:$GARIMPEI_WEB_PORT"; exit 0
  fi
  if [ -n "$(compose ps --status running --quiet web worker)" ]; then
   echo 'Existing web/worker is not ready; stop the owned instance before restarting' >&2; exit 1
  fi
  GARIMPEI_RUN_ID="$(cat /proc/sys/kernel/random/uuid)"; export GARIMPEI_RUN_ID
  printf '%s' "$GARIMPEI_RUN_ID" > "$instance_dir/run-id"
  if [ "${1:-}" = --disposable ]; then [ "$GARIMPEI_ENV" = eval ] || { echo 'Disposable requires eval' >&2; exit 64; }; touch "$instance_dir/docker-disposable"; export GARIMPEI_DISPOSABLE=true; fi
  compose build web worker manage
  compose up -d --wait postgres waha
  compose --profile tools run --rm --no-deps manage prepare
  compose up -d web worker
  for attempt in $(seq 1 60); do
   if compose exec -T web python -m garimpei.infra.runtime.container_entrypoint ready >/dev/null 2>&1; then
    compose ps --format json > "$instance_dir/docker-inventory.json"
    echo "Ready $GARIMPEI_ENVIRONMENT_ID: http://127.0.0.1:$GARIMPEI_WEB_PORT (AI requires explicit preparation; WAHA pairing is separate)"; exit 0
   fi
   sleep 2
  done
  echo 'Readiness failed: inspect owned container logs; persistent data preserved' >&2; exit 1 ;;
 stop)
  verify
  if [ "${1:-}" = --clean ]; then
   [ "$GARIMPEI_ENV" = eval ] && [ -f "$instance_dir/docker-disposable" ] || { echo '--clean requires owned disposable eval' >&2; exit 64; }
   echo '--clean requires verified synthetic WAHA session and migration inventory; use normal stop; data preserved' >&2; exit 64
  fi
  [ -z "${1:-}" ] || { echo 'Expected stop [--clean]' >&2; exit 64; }
  compose --profile tools run --rm --no-deps --entrypoint python manage -m garimpei.infra.runtime.container_artifacts shutdown || echo "Worker stop state could not be recorded; database retained" >&2
  compose --profile "*" stop --timeout 30
  model_id="$(compose --profile ai ps --all --quiet ollama)"
  if [ -n "$model_id" ] && [ "$(docker inspect -f '{{.State.Running}}' "$model_id")" != false ]; then
   echo 'Ollama termination not confirmed; GPU reservation retained' >&2; exit 1
  fi
  compose --profile tools run --rm --no-deps --entrypoint python manage -m garimpei.infra.runtime.container_artifacts release
  echo "Stopped $GARIMPEI_ENVIRONMENT_ID: database, profiles, sessions and all volumes retained" ;;
 migrate)
  verify
  case "${1:-}" in
   --check) compose --profile tools run --rm manage manage migrate --check ;;
   --apply) compose --profile tools run --rm manage prepare ;;
   --make) [[ "${2:-}" =~ ^[a-z][a-z0-9_]*$ ]] || exit 64; echo 'Generate migrations in the quality container with a source mount; immutable runtime does not edit source' >&2; exit 64;;
   *) echo 'Expected migrate --check or --apply' >&2; exit 64;;
  esac ;;
 *) echo 'Expected init, stop, migrate or resolve' >&2; exit 64;;
esac

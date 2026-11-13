#!/usr/bin/env bash
# Called only by docker-runtime after its per-environment lock and ownership checks.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
compose() { docker compose --env-file "$GARIMPEI_ENV_FILE" -p "garimpei-$GARIMPEI_ENVIRONMENT_ID" -f "$PROJECT_DIR/compose.yaml" "$@"; }
artifact() { compose --profile tools run --rm --no-deps --entrypoint python manage -m garimpei.infra.runtime.container_artifacts "$@"; }
identifier="$(compose --profile ai ps --all --quiet ollama)"
verify() {
 [ -n "$identifier" ] && [ "$(docker inspect -f '{{index .Config.Labels "com.garimpei.checkout"}}' "$identifier")" = "$PROJECT_DIR" ] && [ "$(docker inspect -f '{{index .Config.Labels "com.garimpei.environment"}}' "$identifier")" = "$GARIMPEI_ENVIRONMENT_ID" ] || { echo 'Ollama ownership not confirmed; reservation retained' >&2; exit 1; }
}
case "${1:-}" in
 prepare)
  artifact reserve || { echo 'GPU reserved by another environment; nothing stopped' >&2; exit 1; }
  compose --profile ai up -d ollama
  identifier="$(compose --profile ai ps --quiet ollama)"; verify
  expected_image="$(artifact image)"
  [ "$(docker inspect -f '{{.Config.Image}}' "$identifier")" = "$expected_image" ] || { echo 'Ollama image pin mismatch' >&2; exit 1; }
  network="garimpei-${GARIMPEI_ENVIRONMENT_ID}_outbound"
  trap 'docker network disconnect "$network" "$identifier" >/dev/null 2>&1 || true' EXIT
  docker network connect "$network" "$identifier"
  model="$(artifact model)"
  docker exec "$identifier" ollama pull "$model"
  layers="$(artifact layers)"
  while IFS= read -r digest; do
   [[ "$digest" =~ ^sha256:[a-f0-9]{64}$ ]] || exit 1
   actual="$(docker exec "$identifier" sha256sum "/root/.ollama/models/blobs/${digest/:/-}" | awk '{print $1}')"
   [ "$actual" = "${digest#sha256:}" ] || { echo 'Model blob digest mismatch' >&2; exit 1; }
  done <<< "$layers"
  artifact tokenizer
  docker network disconnect "$network" "$identifier"
  trap - EXIT
  artifact diagnose
  echo 'Pinned local artifacts verified; Ollama is restricted to its internal inference network' ;;
 recover)
  verify
  artifact owned || { echo 'GPU ownership not confirmed; recovery refused' >&2; exit 1; }
  docker stop --time 3 "$identifier" >/dev/null
  [ "$(docker inspect -f '{{.State.Running}}' "$identifier")" = false ] || { echo 'Prior execution termination unconfirmed; blocked' >&2; exit 1; }
  docker start "$identifier" >/dev/null
  artifact recovered
  echo 'Owned prior Ollama execution stopped and confirmed; recovery recorded' ;;
 *) echo 'Expected prepare or recover' >&2; exit 64;;
esac

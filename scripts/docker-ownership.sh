#!/usr/bin/env bash
# Read-only preflight shared by host controllers, before Compose or GPU mutations.
verify_owned_resource() {
 local kind="$1" resource="$2" labels template
 template='{{index .Labels "com.garimpei.checkout"}}|{{index .Labels "com.garimpei.environment"}}'
 if [ "$kind" = container ]; then template='{{index .Config.Labels "com.garimpei.checkout"}}|{{index .Config.Labels "com.garimpei.environment"}}'; fi
 labels="$(docker "$kind" inspect -f "$template" "$resource")" || return 1
 if [ "$labels" != "$PROJECT_DIR|$GARIMPEI_ENVIRONMENT_ID" ]; then
  echo "Docker $kind ownership mismatch; operation refused before mutation" >&2
  return 1
 fi
}

verify_docker_ownership() {
 local project="garimpei-$GARIMPEI_ENVIRONMENT_ID" containers kind existing candidates suffixes suffix resource
 containers="$(docker ps -aq --filter "label=com.docker.compose.project=$project")" || return 1
 for resource in $containers; do verify_owned_resource container "$resource" || return 1; done
 for kind in volume network; do
  existing="$(docker "$kind" ls --format '{{.Name}}')" || return 1
  candidates="$(docker "$kind" ls --filter "label=com.docker.compose.project=$project" --format '{{.Name}}')" || return 1
  if [ "$kind" = volume ]; then suffixes='postgres_data waha_sessions ollama_models'; else suffixes='data outbound inference default'; fi
  # Compose can encounter a resource with the expected name but missing project labels.
  for suffix in $suffixes; do
   resource="${project}_$suffix"
   if printf '%s\n' "$existing" | grep -Fxq -- "$resource"; then candidates="${candidates}"$'\n'"$resource"; fi
  done
  candidates="$(printf '%s\n' "$candidates" | awk 'NF && !seen[$0]++')"
  for resource in $candidates; do verify_owned_resource "$kind" "$resource" || return 1; done
 done
}

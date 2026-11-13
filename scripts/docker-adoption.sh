#!/usr/bin/env bash
# Full private cold copy complements F17's business backup; never starts automation.
set -euo pipefail
umask 077
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
refuse() { echo "Adoption refused: $*" >&2; exit 64; }
[ "$#" = 3 ] || refuse 'expected snapshot|restore-check COMPOSE_PROJECT ABSOLUTE_PRIVATE_DIRECTORY'
action="$1"; project="$2"; folder="$3"
[[ "$project" =~ ^garimpei-(eval|dev)_[a-z0-9_]{1,40}$ ]] || refuse 'expected owned garimpei_ project'
[[ "$folder" = /* && "$folder" != / && ! -L "$folder" ]] || refuse 'expected absolute non-symlink private directory'
folder="$(realpath -m -- "$folder")"
[[ "$action" = snapshot || "$action" = restore-check ]] || refuse 'expected snapshot or restore-check'

verify_copy() {
 [ -f "$folder/READY" ] && [ "$(cat "$folder/READY")" = snapshot-complete-v1 ] || refuse 'copy is incomplete'
 [ -f "$folder/checksums" ] && [ ! -L "$folder/checksums" ] || refuse 'checksums missing'
 # The checksum file is data, never a list of arbitrary host paths to read.
 awk 'NF != 2 || length($1) != 64 || $1 ~ /[^0-9a-f]/ || $2 !~ /^(database.dump|inventory.tsv|counts.tsv|private.tar|inference.tar|waha.tar|ollama.tar)$/ {bad=1} END {exit bad}' "$folder/checksums" || refuse 'checksum entries outside snapshot'
 for name in database.dump inventory.tsv counts.tsv; do
  [ "$(awk -v name="$name" '$2 == name {n++} END {print n+0}' "$folder/checksums")" = 1 ] || refuse 'required checksum missing'
 done
 for name in private.tar inference.tar waha.tar ollama.tar; do
  [ ! -e "$folder/$name" ] || [ "$(awk -v name="$name" '$2 == name {n++} END {print n+0}' "$folder/checksums")" = 1 ] || refuse 'archive checksum missing or duplicated'
 done
 while read -r digest name; do
  [ -f "$folder/$name" ] && [ ! -L "$folder/$name" ] || refuse 'archive absent or symlink'
 done < "$folder/checksums"
 (cd "$folder" && sha256sum --status -c checksums) || refuse 'checksum mismatch'
}
[ "$action" != restore-check ] || verify_copy
command -v docker >/dev/null || refuse 'Docker required'
ids="$(docker ps -aq --filter "label=com.docker.compose.project=$project")"
[ -n "$ids" ] || refuse 'owned containers not found'
pg=''; worker=''; waha=''; ollama=''; environment=''
for identity in $ids; do
 details="$(docker inspect -f '{{index .Config.Labels "com.garimpei.checkout"}}|{{index .Config.Labels "com.garimpei.environment"}}|{{index .Config.Labels "com.docker.compose.service"}}|{{.State.Running}}' "$identity")"
 IFS='|' read -r checkout current_environment service running <<< "$details"
 [ "$checkout" = "$root" ] && [ "garimpei-$current_environment" = "$project" ] || refuse 'resource ownership mismatch'
 environment="$current_environment"
 if [ "$service" = postgres ]; then
  [ "$running" = true ] && [ -z "$pg" ] || refuse 'expected one running PostgreSQL'
  pg="$identity"
 else
  [ "$running" = false ] || refuse 'automation, sessions and inference must be stopped first'
 fi
 case "$service" in worker) worker="$identity";; waha) waha="$identity";; ollama) ollama="$identity";; esac
 # Named data volumes must belong to this checkout and environment as well.
 volumes="$(docker inspect -f '{{range .Mounts}}{{if eq .Type "volume"}}{{println .Name}}{{end}}{{end}}' "$identity")"
 for volume in $volumes; do
  labels="$(docker volume inspect -f '{{index .Labels "com.garimpei.checkout"}}|{{index .Labels "com.garimpei.environment"}}' "$volume")"
  [ "$labels" = "$root|$environment" ] || refuse 'volume ownership mismatch'
 done
done
[ -n "$pg" ] || refuse 'PostgreSQL missing'
database="$(docker exec "$pg" printenv POSTGRES_DB)"
[ "$database" = "garimpei_$environment" ] || refuse 'database ownership mismatch'
counts() {
 local selects
 selects="$(query "SELECT string_agg(format('SELECT %L AS relation, count(*) AS rows FROM %I.%I', schemaname||'.'||tablename, schemaname, tablename), ' UNION ALL ') FROM pg_catalog.pg_tables WHERE schemaname !~ '^pg_' AND schemaname <> 'information_schema'")"
 [ -n "$selects" ] || refuse 'no application tables to inventory'
 query "SELECT * FROM ($selects) AS inventory ORDER BY relation"
}
query() { docker exec "$pg" psql -X -v ON_ERROR_STOP=1 -U garimpei -d "$database" -Atqc "$1"; }

if [ "$action" = snapshot ]; then
 [ ! -e "$folder" ] || refuse 'snapshot directory must not exist'
 [ "$(query "SELECT NOT requested_enabled FROM runtime_robotcontrol WHERE installation='local'")" = t ] || refuse 'robot admission must be paused'
 [ "$(query "SELECT count(*) FROM runtime_robotoperation WHERE state='active'")" = 0 ] || refuse 'admitted work must drain before copying'
 # Avoid recursively copying this backup into its own private-data archive.
 if [ -n "$worker" ]; then
  private_root="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/private"}}{{.Source}}{{end}}{{end}}' "$worker")"
  case "$folder/" in "$private_root/"*) [ -z "$private_root" ] || refuse 'backup must be outside private source directory';; esac
 fi
 mkdir -m 700 "$folder"
 printf 'format\tcold-copy-v1\nproject\t%s\nenvironment\t%s\n' "$project" "$environment" > "$folder/inventory.tsv"
 for identity in $ids; do
  docker inspect -f 'container{{printf "\t"}}{{index .Config.Labels "com.docker.compose.service"}}{{printf "\t"}}{{.Image}}' "$identity" >> "$folder/inventory.tsv"
 done
 counts > "$folder/counts.tsv"
 docker exec "$pg" pg_dump -U garimpei -d "$database" --format=custom --no-owner > "$folder/database.dump.partial"
 mv "$folder/database.dump.partial" "$folder/database.dump"
 capture() {
  docker cp "$1:$2/." - > "$folder/$3.partial"
  mv "$folder/$3.partial" "$folder/$3"
 }
 [ -z "$worker" ] || capture "$worker" /private private.tar
 # Inference artifacts are mandatory when a worker exists; copy failure is not absence.
 [ -z "$worker" ] || capture "$worker" "/state/$environment/inference" inference.tar
 [ -z "$waha" ] || capture "$waha" /app/.sessions waha.tar
 [ -z "$ollama" ] || capture "$ollama" /root/.ollama ollama.tar
 (cd "$folder" && sha256sum inventory.tsv database.dump counts.tsv ./*.tar 2>/dev/null | sed 's|  ./|  |' > checksums.partial) || {
  # No optional archives is valid for a database-only snapshot.
  (cd "$folder" && sha256sum inventory.tsv database.dump counts.tsv > checksums.partial)
 }
 mv "$folder/checksums.partial" "$folder/checksums"
 printf 'snapshot-complete-v1\n' > "$folder/READY"
 verify_copy
 echo 'Private cold copy complete; restoration still requires an empty owned eval.'
 exit 0
fi

[[ "$environment" = eval_* ]] || refuse 'restoration requires eval'
[ -f "$root/.runtime/$environment/docker-disposable" ] || refuse 'restoration requires owned disposable marker'
[ "$(query "SELECT count(*) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema' AND c.relkind IN ('r','p','S','v','m')")" = 0 ] || refuse 'restoration requires an empty database'
for pair in "private:$worker" "inference:$worker" "waha:$waha" "ollama:$ollama"; do
 name="${pair%%:*}"; target="${pair#*:}"
 [ ! -f "$folder/$name.tar" ] || [ -n "$target" ] || refuse 'archive target container missing'
done
check_empty() {
 local image
 image="$(docker inspect -f '{{.Image}}' "$1")"
 docker run --rm --network none --read-only --volumes-from "$1:ro" --entrypoint sh "$image" -c 'test -z "$(find "$1" -type f -print -quit)"' sh "$2" || refuse 'target files must be empty'
}
[ ! -f "$folder/private.tar" ] || check_empty "$worker" /private
[ ! -f "$folder/waha.tar" ] || check_empty "$waha" /app/.sessions
[ ! -f "$folder/ollama.tar" ] || check_empty "$ollama" /root/.ollama
[ ! -f "$folder/inference.tar" ] || check_empty "$worker" "/state/$environment/inference"
# All checks precede the first write. A failed restore stays paused and is never started.
docker exec -i "$pg" pg_restore -U garimpei -d "$database" --no-owner --exit-on-error < "$folder/database.dump"
[ "$(query "SELECT NOT requested_enabled FROM runtime_robotcontrol WHERE installation='local'")" = t ] || refuse 'restored admission is not paused; do not start automation'
counts > "$folder/restored-counts.partial"
cmp -s "$folder/counts.tsv" "$folder/restored-counts.partial" || refuse 'restored table counts differ; automation remains stopped'
rm "$folder/restored-counts.partial"
restore_files() {
 [ ! -f "$folder/$3" ] || docker cp -a - "$1:$2/" < "$folder/$3"
}
[ -z "$worker" ] || restore_files "$worker" /private private.tar
if [ -f "$folder/inference.tar" ]; then
 image="$(docker inspect -f '{{.Image}}' "$worker")"
 user="$(docker inspect -f '{{.Config.User}}' "$worker")"
 docker run --rm --network none --read-only --volumes-from "$worker" --user "${user:-0:0}" --entrypoint sh "$image" -c 'mkdir -p "$1"' sh "/state/$environment/inference"
 restore_files "$worker" "/state/$environment/inference" inference.tar
fi
[ -z "$waha" ] || restore_files "$waha" /app/.sessions waha.tar
[ -z "$ollama" ] || restore_files "$ollama" /root/.ollama ollama.tar
printf 'restore-verified-paused-v1\n' > "$folder/restore-$environment"
echo 'Database row counts verified with admission paused; automation remains stopped. Reconcile uncertain sends before adoption or rollback.'

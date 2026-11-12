#!/usr/bin/env bash
set -euo pipefail

command -v codex >/dev/null 2>&1 || { echo '[setup] Codex CLI não encontrado.' >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo '[setup] Node.js não encontrado.' >&2; exit 1; }
marketplace_state="$(codex plugin marketplace list --json | node --input-type=module -e '
let input = "";
for await (const chunk of process.stdin) input += chunk;
const entry = JSON.parse(input).marketplaces.find((item) => item.name === "fullcycle-claude-marketplace");
if (!entry) console.log("missing");
else if (entry.marketplaceSource?.sourceType === "git" &&
  entry.marketplaceSource.source.replace(/\.git$/, "") === "https://github.com/devfullcycle/claude-mkt-place") console.log("existing");
else console.log("conflict");
')"
case "$marketplace_state" in
    missing) codex plugin marketplace add devfullcycle/claude-mkt-place --ref 4a5aa4dd6f926a9346fddc450550896d44c94cad --json ;;
    existing) echo '[setup] Marketplace Full Cycle existente; origem e revisão preservadas.' ;;
    *) echo '[setup] O nome do marketplace já está associado a outra origem; instalação interrompida.' >&2; exit 1 ;;
esac
for plugin in adrs-management diagrams-generator project-analizer development-guidelines; do
    codex plugin add "${plugin}@fullcycle-claude-marketplace" --json
done
codex plugin list --marketplace fullcycle-claude-marketplace --json

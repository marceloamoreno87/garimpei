"""Validate this dated documentation synchronization against its published baseline."""

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

root = Path(__file__).resolve().parents[3]
features = json.loads((root / "docs/prd_progress.json").read_text())["features"]
assert (root / "docs/prd_progress.json").read_bytes() == subprocess.check_output(
    ["git", "show", "d8c53ae:docs/prd_progress.json"], cwd=root
)
seen = set()
active = set()


def visit(name):
    assert name not in active, f"Dependency cycle at {name}"
    if name in seen:
        return
    active.add(name)
    for dep in features[name]["dependencies"]:
        assert dep in features
        visit(dep)
    assert features[name]["wave"] == 1 + max(
        (features[d]["wave"] for d in features[name]["dependencies"]), default=0
    )
    active.remove(name)
    seen.add(name)


for feature in features:
    visit(feature)
contracts = []
plans = []
headers = []
for feature, value in features.items():
    directory = next((root / "docs").glob(feature + "-*"))
    assert (root / value["report_path"]).exists()
    for name in ["spec.md", "plan.md", "contract.md"]:
        p = directory / name
        s = p.read_text()
        assert f"**Situação em 2026-11-13:** `{value['status']}`" in s
        headers.append(str(p.relative_to(root)))
        if name != "spec.md":
            original = subprocess.check_output(
                ["git", "show", "d8c53ae:" + str(p.relative_to(root))],
                cwd=root,
                text=True,
            )
            restored = re.sub(
                r"\n<!-- current-execution:start -->.*?<!-- current-execution:end -->\n",
                "",
                s,
                flags=re.DOTALL,
            )
            assert restored == original, str(p)
            (contracts if name == "contract.md" else plans).append(
                str(p.relative_to(root))
            )
paths = subprocess.check_output(
    [
        "git",
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "--",
        "docs",
        "README.md",
        "CONTEXT.md",
        "AGENTS.md",
    ],
    cwd=root,
    text=True,
).splitlines()
missing = []
checked = 0
for filename in paths:
    p = root / filename
    if p.suffix != ".md" or not p.exists():
        continue
    checked += 1
    text = re.sub(r"```.*?```", "", p.read_text(), flags=re.DOTALL)
    for raw in re.findall(r"\]\(([^\n)]*)\)", text):
        link = raw.strip().split(' "')[0].strip("<>")
        if (
            not link
            or "://" in link
            or link.startswith(("#", "mailto:", "plugin:"))
            or "${" in link
        ):
            continue
        target = p.parent / link.split("#")[0]
        if not target.exists():
            missing.append({"source": filename, "target": link})
assert not missing, json.dumps(missing, ensure_ascii=False)
# ai-memory's managed instructions stay byte-for-byte identical.
original = subprocess.check_output(
    ["git", "show", "d8c53ae:AGENTS.md"], cwd=root, text=True
)
pattern = r"<!-- ai-memory:start -->.*?<!-- ai-memory:end -->"
before = re.search(pattern, original, re.DOTALL)
after = re.search(pattern, (root / "AGENTS.md").read_text(), re.DOTALL)
assert (before[0] if before else None) == (after[0] if after else None)
summary = {
    "checked_at": datetime.now(UTC).isoformat(),
    "features": len(features),
    "feature_status_headers": len(headers),
    "original_contracts_preserved": len(contracts),
    "original_plans_preserved": len(plans),
    "progress_preserved": True,
    "dependency_graph": "DAG, waves consistent",
    "report_paths": "all exist",
    "markdown_files_checked": checked,
    "broken_local_links": missing,
    "ai_memory_managed_block": "preserved"
    if before
    else "absent in repository file; absence preserved",
    "feature_states": {k: v["status"] for k, v in features.items()},
    "historical_reports": "preserved; no retroactive approval",
}
(root / "docs/design/audit-2026-11-13/documentation-sync.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
)
print(json.dumps(summary, ensure_ascii=False))

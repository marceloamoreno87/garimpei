"""Run the audit's browser checks against two explicitly selected disposable instances."""

import argparse
import json
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--app-origin", required=True)
parser.add_argument("--setup-origin", required=True)
parser.add_argument("--session", default="garimpei-ux")
parser.add_argument(
    "--check", choices=["matrix", "interactions", "adaptive"], required=True
)
args = parser.parse_args()
for value in [args.app_origin, args.setup_origin]:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or not parsed.port
        or parsed.path
    ):
        parser.error("Use an explicit http://127.0.0.1:PORT origin without a path")
files = {
    "matrix": ("verify.cjs", "browser-results.json"),
    "interactions": ("interactions.cjs", "interaction-results.json"),
    "adaptive": ("adaptive.cjs", "adaptive-results.json"),
}
directory = Path(__file__).resolve().parent
source, result_file = files[args.check]
code = (
    (directory / source)
    .read_text()
    .replace("__APP_ORIGIN__", args.app_origin)
    .replace("__SETUP_ORIGIN__", args.setup_origin)
)
result = subprocess.run(
    ["playwright-cli", f"-s={args.session}", "run-code", code],
    capture_output=True,
    text=True,
    check=False,
)
if (
    result.returncode
    or "### Error" in result.stdout
    or "### Result\n" not in result.stdout
):
    raise SystemExit(result.stdout + result.stderr)
data = json.loads(result.stdout.split("### Result\n", 1)[1].split("\n###", 1)[0])
(directory / result_file).write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n"
)
if args.check == "matrix":
    failures = [
        case
        for case in data
        if case["violations"]
        or case["overflow"]
        or case["headings"] != 1
        or case["selectedDestinations"] != 1
    ]
    if failures:
        raise SystemExit(json.dumps(failures, ensure_ascii=False, indent=2))
print(f"{args.check}: {len(data)} checks passed; {result_file}")

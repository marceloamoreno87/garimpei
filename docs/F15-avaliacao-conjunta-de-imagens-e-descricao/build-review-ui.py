#!/usr/bin/env python3
"""Build the private, offline review page without copying source photos into Git.

Usage: python3 build-review-ui.py /path/to/private/package [--output /path/index.html]
The package contains manifest.json, review-template.json and relative photo paths.
Only the generated page contains private text; keep that page outside the repository.
"""

import argparse
import base64
import hashlib
import json
from pathlib import Path


def build(package: Path, output: Path) -> None:
    manifest_bytes = (package / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    review = json.loads((package / "review-template.json").read_text())
    sources = manifest["cases"] + manifest.get("controls", [])
    source_ids = [item["case_id"] for item in sources]
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("Manifest has duplicate case IDs")
    if source_ids != [item["case_id"] for item in review["cases"]]:
        raise ValueError("Manifest and review template must have the same ordered case IDs")
    if (manifest["schema_version"], manifest["rubric"]) != (review["schema_version"], review["rubric"]):
        raise ValueError("Manifest and review template schema/rubric differ")
    for item in sources:
        for photo in item.get("photos", []):
            relative = Path(photo["path"])
            if relative.is_absolute() or ".." in relative.parts or ":" in photo["path"]:
                raise ValueError("Only package-relative photo paths are permitted")
            photo_path = package / relative
            if hashlib.sha256(photo_path.read_bytes()).hexdigest() != photo["sha256"]:
                raise ValueError(f"Photo integrity check failed: {item['case_id']}")
    payload = json.dumps({"manifest": manifest, "template": review,
                          "manifestHash": hashlib.sha256(manifest_bytes).hexdigest()},
                         ensure_ascii=False, separators=(",", ":"))
    # A JSON script block is raw text in HTML: '<' must never close that block.
    payload = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    template = Path(__file__).with_name("review-offline-template.html").read_text()
    font_path = Path(__file__).resolve().parents[1] / "design/prototypes/assets/manrope.woff2"
    font = base64.b64encode(font_path.read_bytes()).decode("ascii")
    output.write_text(template.replace("__REVIEW_PAYLOAD__", payload).replace("__LOCAL_FONT__", font))
    print(f"Built offline review: {len(sources)} cases; manifest SHA-256 {hashlib.sha256(manifest_bytes).hexdigest()}")
    print(f"Private output: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    output = args.output.resolve() if args.output else package / "index.html"
    repo = Path(__file__).resolve().parents[2]
    if output.is_relative_to(repo):
        parser.error("Private generated output must remain outside the repository")
    if output.parent != package:
        parser.error("Output must be in the package directory to preserve relative photo paths")
    build(package, output)


if __name__ == "__main__":
    main()

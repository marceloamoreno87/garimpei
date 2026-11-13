"""Validate a frozen human review before any model or runtime access."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from garimpei.domain.listing.assessment_policy import CATEGORIES, POLICY_VERSION


class ReviewPending(ValueError):
    pass


def read_plan(manifest_path: Path, review_path: Path, package: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text())
    review = json.loads(review_path.read_text())
    if review.get("schema_version") != 1 or review.get("rubric") != POLICY_VERSION:
        raise ReviewPending("Expected review schema1 and the approved rubric")
    if manifest.get("rubric") != POLICY_VERSION:
        raise ReviewPending("Manifest rubric differs from the approved policy")
    expected_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if review.get("manifest_sha256") != expected_hash:
        raise ReviewPending("Human export must match the frozen manifest hash")
    cases = manifest.get("cases", []) + manifest.get("controls", [])
    ids = [row["case_id"] for row in cases]
    reviewed = review.get("cases", [])
    review_ids = [row.get("case_id") for row in reviewed]
    if not ids or len(set(ids)) != len(ids) or sorted(ids) != sorted(review_ids):
        raise ReviewPending("Review must contain every frozen case exactly once")
    rows = {row["case_id"]: row for row in reviewed}
    plan = []
    for case in cases:
        row = rows[case["case_id"]]
        if case.get("kind") not in {
            "real_source_unreviewed",
            "synthetic_control",
            "text_regression",
        }:
            raise ReviewPending("Unknown corpus provenance kind")
        if case["kind"] == "real_source_unreviewed" and not case.get("authorization"):
            raise ReviewPending("Real photograph authorization is missing")
        _human(row)
        if case.get("split") in {"adjustment", "reserved"} and row["split"] != case["split"]:
            raise ReviewPending("Frozen control splits cannot be changed by the human export")
        category = row.get("category")
        if category not in CATEGORIES and category not in {None, "unsupported"}:
            raise ReviewPending("Unknown category for case " + case["case_id"])
        if case.get("category") in CATEGORIES and category != case["category"]:
            raise ReviewPending("Category correction requires a new frozen manifest")
        if row.get("text_corrections") is not None:
            raise ReviewPending("Text correction requires a new frozen manifest with source")
        photos = [_photo(photo, package) for photo in case["photos"]]
        _findings(row, case)
        plan.append(dict(case, review=row, category=category, photos=photos, split=row["split"]))
    split_by_photo: dict[str, str] = {}
    for case in plan:
        for photo in case["photos"]:
            previous = split_by_photo.setdefault(photo["sha256"], case["split"])
            if previous != case["split"]:
                raise ReviewPending("A photo cannot occur in both adjustment and reserved splits")
    if not any(row["split"] == "reserved" for row in plan):
        raise ReviewPending("Close a nonempty reserved split before inference")
    if not any(row["split"] == "adjustment" for row in plan):
        raise ReviewPending("Keep an adjustment split separate from reserved evaluation")
    if not any(
        row["kind"] == "real_source_unreviewed"
        and row["split"] == "reserved"
        and bool(row["photos"])
        for row in plan
    ):
        raise ReviewPending("Reserved evaluation requires an authorized real-photo case")
    covered = {row["category"] for row in plan}
    if not CATEGORIES <= covered:
        raise ReviewPending("The frozen corpus must cover the six rubric categories")
    return dict(
        cases=plan,
        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        review_sha256=hashlib.sha256(review_path.read_bytes()).hexdigest(),
        rubric=POLICY_VERSION,
    )


def _human(row: dict[str, Any]) -> None:
    identity = str(row["case_id"])
    if not isinstance(row.get("reviewer"), str) or not row["reviewer"].strip():
        raise ReviewPending("Human reviewer missing: " + identity)
    try:
        stamp = datetime.fromisoformat(str(row.get("reviewed_at")).replace("Z", "+00:00"))
        if stamp.utcoffset() is None:
            raise ValueError
    except ValueError:
        raise ReviewPending("Timezone-aware human review date missing: " + identity) from None
    if row.get("label") not in {"good", "defect", "uncertain"}:
        raise ReviewPending("Human condition missing: " + identity)
    if row.get("split") not in {"adjustment", "reserved"}:
        raise ReviewPending("Adjustment/reserved split missing: " + identity)
    if not isinstance(row.get("limitations"), list) or any(
        not isinstance(v, str) or not v.strip() for v in row["limitations"]
    ):
        raise ReviewPending("Human limitations must be a text list: " + identity)


def _photo(photo: dict[str, Any], package: Path) -> dict[str, Any]:
    path = (package / photo["path"]).resolve()
    if not path.is_relative_to(package.resolve()) or not path.is_file():
        raise ReviewPending("Photo missing or outside frozen package")
    if hashlib.sha256(path.read_bytes()).hexdigest() != photo["sha256"]:
        raise ReviewPending("Frozen photo hash differs")
    return dict(photo, file=str(path), photo_id=photo.get("photo_id", photo.get("id")))


def _findings(row: dict[str, Any], case: dict[str, Any]) -> None:
    findings = row.get("findings")
    if not isinstance(findings, list):
        raise ReviewPending("Human findings must be a list")
    if row["label"] != "uncertain" and not findings:
        raise ReviewPending("A conclusive human label requires cited evidence")
    if row["label"] == "uncertain" and not findings and not row["limitations"]:
        raise ReviewPending("Human abstention requires evidence or a limitation")
    photos = {p.get("photo_id", p.get("id")) for p in case["photos"]}
    for finding in findings:
        if finding.get("severity") not in {"light_wear", "clear_defect", "suspected", "unknown"}:
            raise ReviewPending("Human finding severity is missing")
        if finding.get("component") not in {"main", "accessory", "unknown"}:
            raise ReviewPending("Human finding component is missing")
        if finding.get("dimension") not in {
            "appearance",
            "function_claim",
            "completeness",
            "identity",
            "consistency",
        }:
            raise ReviewPending("Human finding dimension is missing")
        if not isinstance(finding.get("description"), str) or not finding["description"].strip():
            raise ReviewPending("Human finding description is missing")
        evidence = finding.get("evidence") or {}
        photo_ok = evidence.get("photo_id") in photos
        field, quote = evidence.get("text_field"), evidence.get("quote")
        text = case["text"].get(field) if isinstance(field, str) else None
        text_ok = isinstance(quote, str) and bool(quote) and isinstance(text, str) and quote in text
        if not photo_ok and not text_ok:
            raise ReviewPending("Human finding must cite a frozen photo or literal text")

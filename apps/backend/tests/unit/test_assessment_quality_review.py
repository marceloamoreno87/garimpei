"""Synthetic review exports exercise validation; they never label the human corpus."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from tests.factories.assessment_quality import evaluate_corpus
from tests.factories.assessment_quality_review import read_plan


@pytest.fixture
def frozen(tmp_path: Path) -> dict[str, str]:
    categories = ["electronics", "camera", "computer", "console", "headphone", "television"]
    cases = []
    reviews = []
    for index, category in enumerate(categories + ["console"]):
        identity = "test-case-" + str(index)
        file = tmp_path / (identity + ".png")
        file.write_bytes(b"controlled-unit-fixture-" + str(index).encode())
        photo = dict(
            photo_id=identity,
            path=file.name,
            sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
            width=1,
            height=1,
        )
        cases.append(
            dict(
                case_id=identity,
                category=category,
                kind="synthetic_control" if index < 6 else "real_source_unreviewed",
                authorization="CONTROLLED UNIT FIXTURE ONLY",
                text=dict(title="Controlled test", description=None, condition=None),
                photos=[photo],
            )
        )
        reviews.append(
            dict(
                case_id=identity,
                category=category,
                reviewer="CONTROLLED UNIT FIXTURE",
                reviewed_at="2026-11-13T13:00:00Z",
                label="uncertain",
                findings=[],
                limitations=["Not a human corpus review"],
                text_corrections=None,
                split="adjustment" if index == 0 else "reserved",
            )
        )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(dict(rubric="condition-policy-v1", cases=cases)))
    review = tmp_path / "review.json"
    review.write_text(
        json.dumps(
            dict(
                schema_version=1,
                reference_method="human",
                rubric="condition-policy-v1",
                manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                cases=reviews,
            )
        )
    )
    return dict(manifest=str(manifest), review=str(review), package=str(tmp_path), mode="real")


def test_complete_synthetic_export_validates_without_accessing_runtime(
    frozen: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object) -> None:
        raise AssertionError("Validation touched runtime")

    monkeypatch.setattr("tests.factories.assessment_quality._execute", forbidden)
    result = evaluate_corpus(dict(frozen, mode="validate"))
    assert result["state"] == "validated" and result["cases"] == 7
    assert result["model_executed"] is False


@pytest.mark.parametrize(
    "fault",
    [
        "label",
        "reviewer",
        "date",
        "split",
        "duplicate",
        "hash",
        "provenance",
        "quote",
        "manifest_hash",
        "split_leak",
        "text_correction",
        "empty_limitation",
        "real_without_photo",
    ],
)
def test_invalid_export_is_rejected_before_any_model_or_runtime(
    frozen: dict[str, str], monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    path = Path(frozen["review"])
    data = json.loads(path.read_text())
    row = data["cases"][0]
    if fault == "label":
        row["label"] = None
    elif fault == "reviewer":
        row["reviewer"] = ""
    elif fault == "date":
        row["reviewed_at"] = "2026-11-13"
    elif fault == "split":
        row["split"] = None
    elif fault == "duplicate":
        data["cases"][-1] = row
    elif fault == "hash":
        (Path(frozen["package"]) / "test-case-0.png").write_bytes(b"tampered")
    elif fault == "manifest_hash":
        data["manifest_sha256"] = "0" * 64
    elif fault == "provenance":
        manifest = Path(frozen["manifest"])
        content = json.loads(manifest.read_text())
        content["cases"][-1]["kind"] = "synthetic_control"
        manifest.write_text(json.dumps(content))
        data["manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    elif fault == "quote":
        row["findings"] = [
            dict(
                dimension="function_claim",
                severity="unknown",
                component="main",
                description="Invented reference",
                evidence=dict(text_field="description", quote="Never supplied"),
            )
        ]
    elif fault == "split_leak":
        manifest = Path(frozen["manifest"])
        content = json.loads(manifest.read_text())
        content["cases"][1]["photos"] = content["cases"][0]["photos"]
        manifest.write_text(json.dumps(content))
        data["manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    elif fault == "real_without_photo":
        manifest = Path(frozen["manifest"])
        content = json.loads(manifest.read_text())
        content["cases"][-1]["photos"] = []
        manifest.write_text(json.dumps(content))
        data["manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    elif fault == "empty_limitation":
        row["limitations"] = [" "]
    elif fault == "text_correction":
        row["text_corrections"] = {"description": "Changed"}
    path.write_text(json.dumps(data))

    def forbidden(*args: object) -> None:
        raise AssertionError("Incomplete review touched runtime")

    monkeypatch.setattr("tests.factories.assessment_quality._execute", forbidden)
    result = evaluate_corpus(frozen)
    assert result["state"] == "blocked" and result["model_executed"] is False
    assert result["reason"] == "reference_or_frozen_input_incomplete"


def test_conclusive_label_requires_a_real_frozen_reference(frozen: dict[str, str]) -> None:
    path = Path(frozen["review"])
    data = json.loads(path.read_text())
    row = data["cases"][0]
    row.update(
        label="defect",
        findings=[
            dict(
                dimension="appearance",
                severity="clear_defect",
                component="main",
                description="Controlled damaged frame",
                evidence=dict(photo_id="test-case-0"),
            )
        ],
    )
    path.write_text(json.dumps(data))
    assert (
        read_plan(Path(frozen["manifest"]), path, Path(frozen["package"]))["cases"][0]["review"][
            "label"
        ]
        == "defect"
    )


def test_pending_canonical_human_export_does_not_run_model(monkeypatch: pytest.MonkeyPatch) -> None:
    root = Path(__file__).resolve().parents[4]
    folder = root / "docs/F15-avaliacao-conjunta-de-imagens-e-descricao"

    def forbidden(*args: object) -> None:
        raise AssertionError("Pending human corpus was executed")

    monkeypatch.setattr("tests.factories.assessment_quality._execute", forbidden)
    result = evaluate_corpus(
        dict(
            manifest=str(folder / "human-review-manifest.json"),
            review=str(folder / "human-review-template.json"),
            package=str(folder),
            mode="real",
        )
    )
    assert result["state"] == "blocked" and result["model_executed"] is False


def test_lab_real_action_reaches_validator_instead_of_unconditional_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.factories.assessment_lab_actions import AssessmentLab

    observed: list[dict[str, object]] = []

    def validate(payload: dict[str, object]) -> dict[str, object]:
        observed.append(payload)
        return dict(state="blocked", reason="human_review_missing", model_executed=False)

    monkeypatch.setattr("tests.factories.assessment_quality.evaluate_corpus", validate)
    lab = object.__new__(AssessmentLab)
    payload: dict[str, object] = dict(
        action="evaluate_corpus",
        mode="real",
        manifest="test-manifest",
        review="pending-review",
        package="test-package",
    )
    assert lab.action(payload)["reason"] == "human_review_missing"
    assert observed == [payload]


def test_quality_report_counts_abstentions_errors_and_keeps_kind_separate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.factories import assessment_quality_runtime as runtime
    from tests.factories.inference import inference_settings

    settings = inference_settings(tmp_path, "http://127.0.0.1:1")
    monkeypatch.setattr(runtime, "load_inference_settings", lambda: settings)
    results: list[dict[str, Any]] = [
        dict(
            case_id="control-a",
            reference="defect",
            automatic="good",
            kind="synthetic_control",
            category="computer",
        ),
        dict(
            case_id="real-a",
            reference="good",
            automatic="defect",
            kind="real_source_unreviewed",
            category="console",
        ),
        dict(
            case_id="real-b",
            reference="uncertain",
            automatic="uncertain",
            kind="real_source_unreviewed",
            category=None,
        ),
    ]
    output = tmp_path / "controlled-report.json"
    runtime._write(
        output,
        dict(manifest_sha256="a" * 64, review_sha256="b" * 64, reference_method="human"),
        results,
        complete=True,
    )
    report = json.loads(output.read_text())
    assert report["false_good"] == 1 and report["false_defect"] == 1 and report["abstentions"] == 1
    assert report["matrix"]["defect"]["good"] == 1
    assert report["matrix"]["good"]["defect"] == 1
    assert report["by_category"]["None"] == 1
    assert [row["kind"] for row in report["results"]] == [row["kind"] for row in results]


def test_real_report_cannot_complete_when_all_photos_fail_before_dispatch(
    frozen: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    from tests.factories import assessment_quality_runtime as runtime

    plan = read_plan(Path(frozen["manifest"]), Path(frozen["review"]), Path(frozen["package"]))
    plan_file = tmp_path / "controlled-plan.json"
    plan_file.write_text(json.dumps(plan))
    monkeypatch.setattr(runtime, "require_disposable", lambda: None)
    from dataclasses import replace

    from tests.factories.inference import inference_settings

    settings = replace(inference_settings(tmp_path, "http://127.0.0.1:1"), service_enabled=True)
    monkeypatch.setattr(runtime, "load_inference_settings", lambda: settings)
    monkeypatch.setattr(runtime, "load_alert_settings", lambda: SimpleNamespace(enabled=False))
    empty = SimpleNamespace(
        objects=SimpleNamespace(filter=lambda **kwargs: SimpleNamespace(exists=lambda: False))
    )
    monkeypatch.setattr(runtime, "InferenceRequest", empty)
    monkeypatch.setattr(runtime, "InferenceControl", empty)
    gateway = SimpleNamespace(
        diagnose=lambda: {
            "reason": "ready",
            "service": True,
            "artifact": "sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04",
        },
        unload=lambda: True,
    )
    monkeypatch.setattr(runtime, "build_inference_gateway", lambda: gateway)
    monkeypatch.setattr(
        runtime,
        "run_case",
        lambda case, origin: dict(case_id=case["case_id"], kind=case["kind"], analyses=[]),
    )
    completed: list[bool] = []

    def capture(
        output: Path, plan: dict[str, Any], results: list[dict[str, Any]], *, complete: bool
    ) -> None:
        completed.append(complete)

    monkeypatch.setattr(runtime, "_write", capture)
    with pytest.raises(RuntimeError, match="No real-photo inference"):
        runtime.execute(plan_file, tmp_path / "must-not-complete.json")
    assert completed and not any(completed)


@pytest.mark.parametrize("method", ["human", "ai_assisted"])
def test_reference_method_is_explicit_and_retained_without_inference(
    frozen: dict[str, str], monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    path = Path(frozen["review"])
    data = json.loads(path.read_text())
    data["reference_method"] = method
    if method == "ai_assisted":
        for row in data["cases"]:
            row["reviewer"] = "Codex (IA)"
    path.write_text(json.dumps(data))
    plan = read_plan(Path(frozen["manifest"]), path, Path(frozen["package"]))
    assert plan["reference_method"] == method
    assert plan["independent_human_review"] is (method == "human")
    result = evaluate_corpus(dict(frozen, mode="validate"))
    assert result["state"] == "validated" and result["model_executed"] is False
    assert result["reference_method"] == method
    assert result["independent_human_review"] is (method == "human")


@pytest.mark.parametrize(
    "fault",
    ["absent", "null", "invalid", "top_extra", "case_extra", "finding_extra", "evidence_extra"],
)
def test_unattributed_or_extra_export_fields_fail_before_photo_or_runtime_io(
    frozen: dict[str, str], monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    path = Path(frozen["review"])
    data = json.loads(path.read_text())
    for row in data["cases"]:
        row["reviewer"] = "Codex (IA)"
    if fault == "absent":
        data.pop("reference_method")
    elif fault == "null":
        data["reference_method"] = None
    elif fault == "invalid":
        data["reference_method"] = "as_if_human"
    elif fault == "top_extra":
        data["independent_human_review"] = True
    elif fault == "case_extra":
        data["cases"][0]["model_prediction"] = "good"
    else:
        finding: dict[str, Any] = dict(
            dimension="appearance",
            severity="unknown",
            component="main",
            description="Synthetic controlled review",
            evidence=dict(photo_id="test-case-0"),
        )
        data["cases"][0]["findings"] = [finding]
        if fault == "finding_extra":
            finding["confidence"] = 1
        else:
            finding["evidence"]["tool"] = "send"
    path.write_text(json.dumps(data))

    def forbidden(*args: object) -> None:
        raise AssertionError("Invalid reference touched photos/runtime")

    monkeypatch.setattr("tests.factories.assessment_quality_review._photo", forbidden)
    monkeypatch.setattr("tests.factories.assessment_quality._execute", forbidden)
    result = evaluate_corpus(frozen)
    assert result["state"] == "blocked" and result["model_executed"] is False


@pytest.mark.parametrize("method", ["human", "ai_assisted"])
def test_report_names_the_reference_method_and_never_calls_ai_a_human(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    from tests.factories import assessment_quality_runtime as runtime
    from tests.factories.inference import inference_settings

    settings = inference_settings(tmp_path, "http://127.0.0.1:1")
    monkeypatch.setattr(runtime, "load_inference_settings", lambda: settings)
    results = [
        dict(
            case_id="controlled-reference",
            reference="defect",
            automatic="good",
            kind="synthetic_control",
            category="computer",
        )
    ]
    output = tmp_path / "report.json"
    runtime._write(
        output,
        dict(manifest_sha256="a" * 64, review_sha256="b" * 64, reference_method=method),
        results,
        complete=True,
    )
    report = json.loads(output.read_text())
    assert report["reference_method"] == method
    assert report["independent_human_review"] is (method == "human")
    assert report["matrix_axes"] == ["reference", "automatic"]
    assert report["matrix"]["defect"]["good"] == 1
    assert all("human" not in row for row in report["results"])
    if method == "ai_assisted":
        assert report["comparison_kind"] == "ai_agreement"
        assert "false_good" not in report and "false_defect" not in report
        assert report["automatic_good_reference_other"] == 1
        assert report["legacy_human_acceptance_satisfied"] is False
    else:
        assert report["comparison_kind"] == "human_reference_comparison"
        assert report["false_good"] == 1


@pytest.mark.parametrize(
    "change", [{"reference_method": "human"}, {"mode": None}, {"mode": "invented"}]
)
def test_invalid_action_metadata_is_rejected_before_reading_export(
    frozen: dict[str, str], monkeypatch: pytest.MonkeyPatch, change: dict[str, object]
) -> None:
    def forbidden(*args: object) -> None:
        raise AssertionError("Invalid action read reference or runtime")

    monkeypatch.setattr("tests.factories.assessment_quality.read_plan", forbidden)
    result = evaluate_corpus(dict(frozen, **change))
    assert result["state"] == "blocked" and result["model_executed"] is False


def test_null_method_blocks_before_reading_manifest_or_photos(frozen: dict[str, str]) -> None:
    path = Path(frozen["review"])
    data = json.loads(path.read_text())
    data["reference_method"] = None
    path.write_text(json.dumps(data))
    Path(frozen["manifest"]).unlink()
    result = evaluate_corpus(frozen)
    assert result["state"] == "blocked" and result["model_executed"] is False
    assert "reference_method" in result["detail"]

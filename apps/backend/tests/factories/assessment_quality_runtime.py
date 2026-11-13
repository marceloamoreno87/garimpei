"""Real F14/F15/F19 corpus driver. Imported only after human review validation."""

import hashlib
import json
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Thread
from typing import Any, cast
from uuid import uuid4

import psutil
from django.utils.timezone import now

from garimpei.config.env import load_alert_settings, load_inference_settings
from garimpei.domain.inference.condition_evidence import VERSION
from garimpei.domain.listing.assessment_policy import POLICY_VERSION
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.media.media import Manifest, Photo, Variant
from garimpei.infra.gateway.inference.input_preparer import read_lock
from garimpei.infra.gateway.listing.assessment_inference import LocalAssessmentInference
from garimpei.infra.gateway.listing.assessment_inputs import LocalAssessmentInputs
from garimpei.infra.persistence.assessment_models import ConditionAssessment
from garimpei.infra.persistence.inference_models import InferenceControl, InferenceRequest
from garimpei.infra.persistence.listing_models import (
    CollectionCycle,
    CollectionState,
    Listing,
    ListingObservation,
)
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
from garimpei.infra.queries.media.postgres_queries import PostgresMediaQueries
from garimpei.infra.repository.listing.assessment_mapper import decode_assessment
from garimpei.infra.repository.listing.assessment_repository import PostgresAssessmentRepository
from garimpei.infra.repository.listing.mapper import encode_evidence
from garimpei.infra.repository.media.captures import create_capture
from garimpei.main import (
    build_inference_gateway,
    build_media_repository,
    build_media_runner,
    build_media_store,
    build_request_analysis,
    build_run_analysis,
)
from garimpei.usecase.listing.complete_assessment_usecase import CompleteAssessmentUseCase
from garimpei.usecase.listing.prepare_assessment_usecase import PrepareAssessmentUseCase
from tests.factories.assessment_origin import serve_assessment_images
from tests.factories.monitoring import require_disposable


def execute(plan_path: Path, output: Path) -> None:
    require_disposable()
    if not load_inference_settings().service_enabled or load_alert_settings().enabled:
        raise RuntimeError("Real IA enabled and alerts disabled are required")
    if InferenceRequest.objects.filter(
        state__in=["pending", "running", "awaiting_resource", "paused"]
    ).exists():
        raise RuntimeError("Exclusive idle inference queue required")
    if InferenceControl.objects.filter(paused=True).exists():
        raise RuntimeError("The selected runtime is manually paused")
    gateway = build_inference_gateway()
    diagnostic = gateway.diagnose()
    if diagnostic.get("reason") != "ready" or not gateway.unload():
        raise RuntimeError("Verified pinned real runtime and owned model unload required")
    plan = json.loads(plan_path.read_text())
    selected = [case for case in plan["cases"] if case["split"] == "reserved"]
    files = {photo["sha256"]: Path(photo["file"]) for case in selected for photo in case["photos"]}
    for digest, file in files.items():
        if hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            raise RuntimeError("Frozen photo changed after validation")
    results: list[dict[str, Any]] = []
    with serve_assessment_images(files) as (origin, _):
        os.environ["GARIMPEI_MEDIA_EVAL_ORIGIN"] = origin
        os.environ["GARIMPEI_ASSESSMENT_ENABLED"] = "true"
        for case in selected:
            result = run_case(case, origin)
            sent = any(
                part["metrics"].get("sent")
                for analysis in result["analyses"]
                for part in analysis["parts"]
            )
            prior_sent = any(row.get("inference_sent") for row in results)
            result["inference_sent"] = sent
            result["thermal_position"] = (
                "no_inference"
                if not sent
                else "after_verified_unload"
                if not prior_sent
                else "subsequent_case"
            )
            results.append(result)
            _write(output, plan, results, complete=False)
    if not any(
        row["kind"] == "real_source_unreviewed" and row["inference_sent"] for row in results
    ):
        raise RuntimeError(
            "No real-photo inference was actually sent; partial report remains incomplete"
        )
    _write(output, plan, results, complete=True)


def run_case(case: dict[str, Any], origin: str) -> dict[str, Any]:
    from garimpei.config.env import load_media_settings

    stamp = now()
    state = CollectionState.objects.create(
        configuration_id=uuid4(), source="assessment_quality_fixture"
    )
    cycle = CollectionCycle.objects.create(state=state, scope_key="quality", revision=1)
    listing = Listing.objects.create(
        source="assessment_quality_fixture",
        external_id=uuid4().hex,
        canonical_url="https://example.invalid/quality/",
        first_seen_at=stamp,
        origin="initial_load",
    )
    evidence = Evidence(**case["text"])
    obs = ListingObservation.objects.create(
        listing=listing,
        cycle=cycle,
        ordinal=1,
        observed_at=stamp,
        evidence=encode_evidence(evidence),
        coverage={},
    )
    listing.latest = obs
    listing.ordinal = 1
    listing.save()
    photos = tuple(
        Photo(
            "quality-" + str(index),
            (Variant(origin + "/" + photo["sha256"], photo["width"], photo["height"]),),
            index == 0,
        )
        for index, photo in enumerate(case["photos"])
    )
    create_capture(
        obs,
        Manifest("present" if photos else "none", photos, True, ""),
        load_media_settings().policy,
        stamp,
    )
    media = build_media_repository()
    media_runner = build_media_runner()
    for _ in range(max(4, len(photos) * 3)):
        jobs = media.due(now())
        if not jobs:
            break
        for job in jobs:
            media_runner.execute(job)
    repository = PostgresAssessmentRepository()
    inference = LocalAssessmentInference(
        build_request_analysis(), media, build_media_store(), PostgresMediaQueries()
    )
    prepare = PrepareAssessmentUseCase(LocalAssessmentInputs(), repository, inference, now)
    complete = CompleteAssessmentUseCase(repository, inference, now)
    runner = build_run_analysis()
    started = time.monotonic()
    with _memory_samples() as memory:
        work = prepare.execute(listing.id)
        deadline = time.monotonic() + max(600, len(photos) * 600)
        while not complete.execute(work.id):
            if time.monotonic() >= deadline:
                raise RuntimeError("Corpus case deadline exceeded; partial report preserved")
            runner.execute()
            time.sleep(0.05)
    row = ConditionAssessment.objects.get(id=work.id)
    assert isinstance(row.result, dict)
    assessment = decode_assessment(row.result)
    queries = PostgresInferenceQueries()
    analyses = [queries.analysis(identity) for identity in work.requests]
    parts = [
        part for analysis in analyses for part in cast(list[dict[str, Any]], analysis["parts"])
    ]
    if any(part["metrics"].get("controlled_fake") for part in parts):
        raise RuntimeError("Controlled fake results cannot enter real quality report")
    return dict(
        case_id=case["case_id"],
        kind=case["kind"],
        category=case["category"],
        human=case["review"]["label"],
        automatic=assessment.condition,
        status=assessment.status,
        reason=assessment.reason,
        sufficient=assessment.sufficient,
        assessment_id=str(work.id),
        observation_id=str(obs.id),
        fingerprint=work.value.fingerprint,
        photos=[dict(photo_id=p["photo_id"], sha256=p["sha256"]) for p in case["photos"]],
        elapsed_seconds=time.monotonic() - started,
        analyses=analyses,
        memory_scope="host RAM and evaluator RSS sampled at100ms; model VRAM in per-call F19 metrics",
        ram_samples=memory,
        evidence_errors=[part["reason"] for part in parts if part["state"] != "succeeded"],
        limitations=list(assessment.limitations),
    )


@contextmanager
def _memory_samples() -> Iterator[list[dict[str, float | int]]]:
    stop = Event()
    samples: list[dict[str, float | int]] = []

    def sample() -> None:
        while not stop.is_set():
            samples.append(
                dict(
                    monotonic=time.monotonic(),
                    host_used_bytes=psutil.virtual_memory().used,
                    evaluator_rss_bytes=psutil.Process().memory_info().rss,
                )
            )
            stop.wait(0.1)

    thread = Thread(target=sample, daemon=True)
    thread.start()
    try:
        yield samples
    finally:
        stop.set()
        thread.join(timeout=1)


def _write(
    output: Path, plan: dict[str, Any], results: list[dict[str, Any]], *, complete: bool
) -> None:
    labels = ("good", "defect", "uncertain")
    matrix = {human: {automatic: 0 for automatic in labels} for human in labels}
    for result in results:
        matrix[result["human"]][result["automatic"]] += 1
    lock = read_lock(load_inference_settings().model_lock)
    report = dict(
        complete=complete,
        runtime="real_local_F19",
        manifest_sha256=plan["manifest_sha256"],
        review_sha256=plan["review_sha256"],
        policy_version=POLICY_VERSION,
        prompt_version=VERSION,
        schema_version=VERSION,
        model=lock["model"],
        model_digest=lock["model_digest"],
        split="reserved",
        results=results,
        matrix=matrix,
        false_good=sum(matrix[h]["good"] for h in labels if h != "good"),
        false_defect=sum(matrix[h]["defect"] for h in labels if h != "defect"),
        abstentions=sum(matrix[h]["uncertain"] for h in labels),
        by_category={
            category: sum(str(r["category"]) == category for r in results)
            for category in sorted({str(r["category"]) for r in results})
        },
        note="No numerical accuracy target approved. Synthetic controls and real photographs remain distinct in every result; host RAM is not model-only RAM. Thermal order is not proof of continued residency; inspect per-call load_duration.",
    )
    temporary = output.with_suffix(".writing.json")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n")
    temporary.chmod(0o600)
    temporary.replace(output)

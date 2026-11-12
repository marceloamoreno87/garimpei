"""Read confirmed native boundaries; probes and repeated attempts never become progress."""

from datetime import datetime
from uuid import UUID

from django.db.models import F, Max, Min

from garimpei.infra.persistence.exploration_models import ExplorationRevision
from garimpei.infra.persistence.inference_models import InferenceControl, InferenceRequest
from garimpei.infra.persistence.media_models import MediaAsset, MediaCapture, MediaJob


def native_stages(identities: tuple[UUID, ...], now: datetime) -> list[dict[str, object]]:
    return [_media(identities, now), _inference(identities, now), _publication(now)]


def _media(identities: tuple[UUID, ...], now: datetime) -> dict[str, object]:
    jobs = MediaJob.objects.filter(
        entry__capture__observation__listing_id__in=identities,
        entry__capture__observation_id=F("entry__capture__observation__listing__latest_id"),
    )
    pending = jobs.filter(state__in=["pending", "running", "failed"])
    capture = MediaCapture.objects.filter(
        observation__listing_id__in=identities,
        observation_id=F("observation__listing__latest_id"),
    ).exclude(state="ready")
    blocked = capture.filter(state="configuration_required").exists()
    failed = (
        jobs.filter(state="failed").exists()
        and not jobs.filter(state__in=["pending", "running"]).exists()
    )
    timing = pending.aggregate(oldest=Min("entry__capture__observed_at"), due=Min("next_at"))
    last = MediaAsset.objects.filter(listing_id__in=identities, state="available").aggregate(
        at=Max("obtained_at")
    )["at"]
    return _view(
        "media",
        max(pending.count(), capture.count()),
        timing["oldest"] or capture.aggregate(at=Min("observed_at"))["at"],
        last,
        timing["due"],
        blocked or failed,
        "media_configuration_required"
        if blocked
        else "media_attention_required"
        if failed
        else "media_pending",
        now,
    )


def _inference(identities: tuple[UUID, ...], now: datetime) -> dict[str, object]:
    rows = InferenceRequest.objects.filter(
        observation__listing_id__in=identities,
        observation_id=F("observation__listing__latest_id"),
    )
    pending = rows.filter(state__in=["pending", "running", "awaiting_resource", "paused"])
    timing = pending.aggregate(oldest=Min("created_at"), due=Min("next_attempt_at"))
    last = rows.filter(state="succeeded").aggregate(at=Max("completed_at"))["at"]
    control = InferenceControl.objects.filter(pk=1).first()
    blocked = bool(control and (control.paused or not control.service))
    return _view(
        "inference",
        pending.count(),
        timing["oldest"],
        last,
        timing["due"],
        blocked,
        "analysis_service_unavailable" if blocked else "analysis_pending",
        now,
    )


def _publication(now: datetime) -> dict[str, object]:
    latest = ExplorationRevision.objects.order_by("-sequence").first()
    return _view(
        "exploration",
        0,
        None,
        latest.published_at if latest else None,
        None,
        False,
        "progress_confirmed" if latest else "historical_not_measured",
        now,
    )


def _view(
    stage: str,
    pending: int,
    oldest: datetime | None,
    last: datetime | None,
    deadline: datetime | None,
    blocked: bool,
    reason: str,
    now: datetime,
) -> dict[str, object]:
    state = "idle"
    if pending:
        state = _pending_state(blocked, deadline, last or oldest, now)
    return {
        "stage": stage,
        "state": state,
        "reason": reason
        if pending
        else "progress_confirmed"
        if last
        else "historical_not_measured",
        "last_progress_at": last,
        "pending": pending,
        "oldest_pending_at": oldest,
        "pending_age_seconds": max(0, (now - oldest).total_seconds()) if oldest and pending else 0,
        "next_attempt_at": deadline,
        "action": None,
    }


def _pending_state(
    blocked: bool, deadline: datetime | None, baseline: datetime | None, now: datetime
) -> str:
    if blocked:
        return "suspended"
    if deadline and deadline > now:
        return "waiting"
    return "stalled" if baseline and (now - baseline).total_seconds() >= 180 else "running"

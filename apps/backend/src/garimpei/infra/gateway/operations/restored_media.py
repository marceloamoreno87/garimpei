"""Remove imported execution ownership without granting another F14 retry budget."""

from django.db.models import F

from garimpei.domain.media.policy import MediaPolicy
from garimpei.infra.persistence.media_models import MediaCapture, MediaEntry, MediaJob


def restore_media_work() -> None:
    MediaJob.objects.update(lease_until=None, reserved_bytes=0)
    for job in MediaJob.objects.filter(state__in=["pending", "running"]).select_related(
        "entry__capture"
    ):
        _restore_job(job)


def _restore_job(job: MediaJob) -> None:
    if MediaPolicy().retry_delay(job.attempts) is not None:
        if job.state == "running":
            job.state = "pending"
            job.save(update_fields=["state"])
        return
    job.state, job.reason = "failed", "media_retry_exhausted"
    job.save(update_fields=["state", "reason"])
    MediaEntry.objects.filter(id=job.entry_id).update(reason="media_retry_exhausted")
    capture = job.entry.capture
    has_bytes = MediaEntry.objects.filter(capture=capture, asset__state="available").exists()
    # Retain verified bytes/history and timestamps; restore is not a network attempt or progress.
    MediaCapture.objects.filter(id=capture.id).update(
        state="partial" if has_bytes else "failed",
        complete=False,
        reason="media_retry_exhausted",
        revision=F("revision") + 1,
    )

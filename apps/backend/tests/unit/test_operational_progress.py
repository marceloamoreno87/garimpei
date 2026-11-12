from datetime import UTC, datetime, timedelta

import pytest

from garimpei.domain.operations.progress import OperationalProgress, ProgressConflict

NOW = datetime(2026, 11, 12, 18, tzinfo=UTC)


def test_heartbeat_and_same_checkpoint_never_renew_useful_progress() -> None:
    progress = OperationalProgress.create("listing", "interest-A", revision=2, now=NOW)
    progress.confirm("page-A", generation=0, revision=2, now=NOW)
    later = NOW + timedelta(seconds=181)
    progress.attempt(later)
    progress.confirm("page-A", generation=0, revision=2, now=later)
    assert progress.last_progress_at == NOW
    assert progress.last_attempt_at == later
    assert progress.state_at(later) == "stalled"


def test_idle_and_valid_source_deadline_do_not_stall() -> None:
    progress = OperationalProgress.create("listing", "interest-A", revision=2, now=NOW)
    progress.wait_until(NOW + timedelta(seconds=900), "source_rate_limit")
    assert progress.state_at(NOW + timedelta(seconds=400)) == "waiting"
    progress.complete()
    assert progress.state_at(NOW + timedelta(seconds=1000)) == "idle"


def test_third_failure_persists_checkpoint_and_requires_explicit_resume() -> None:
    progress = OperationalProgress.create("valuation", "offer-A", revision=2, now=NOW)
    progress.confirm("observation-A", generation=0, revision=2, now=NOW)
    for _ in range(3):
        progress.fail("temporary_unavailable", NOW)
    assert progress.state_at(NOW) == "suspended"
    assert not progress.admits(NOW + timedelta(seconds=1000))
    assert progress.failures == 3
    progress.resume(expected_revision=2, now=NOW)
    assert progress.failures == 0 and progress.checkpoint == "observation-A"
    with pytest.raises(ProgressConflict):
        progress.confirm("old", generation=0, revision=2, now=NOW)


def test_stale_revision_and_access_suspension_cannot_be_resumed() -> None:
    progress = OperationalProgress.create("listing", "interest-A", revision=2, now=NOW)
    with pytest.raises(ProgressConflict):
        progress.confirm("old", generation=0, revision=1, now=NOW)
    progress.fail("access_denied", NOW)
    with pytest.raises(ProgressConflict):
        progress.resume(expected_revision=2, now=NOW)
    assert progress.checkpoint == ""


def test_earlier_confirmed_boundary_arriving_late_does_not_replace_checkpoint() -> None:
    progress = OperationalProgress.create("listing", "interest-A", revision=2, now=NOW)
    progress.confirm("page-A", generation=0, revision=2, now=NOW)
    later = NOW + timedelta(seconds=10)
    progress.confirm("page-B", generation=0, revision=2, now=later)
    progress.confirm("page-A", generation=0, revision=2, now=later + timedelta(seconds=180))
    assert progress.last_progress_at == later and progress.checkpoint == "page-B"
    assert progress.state_at(later + timedelta(seconds=180)) == "stalled"

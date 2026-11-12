"""First authorization policy. The clock is supplied at the authorization boundary."""

from datetime import datetime, timedelta

POLICY = "first-eligibility-v1"
PUBLICATION_SOURCES = frozenset({"facebook.creation_time", "fixture.published_at"})


def publication_status(published: datetime | None, source: str | None, now: datetime) -> str:
    if published is None:
        return "untrusted" if source else "missing"
    if source not in PUBLICATION_SOURCES or published.tzinfo is None:
        return "untrusted"
    return "future" if published > now else "trusted"


def first_eligibility(
    published: datetime | None,
    source: str | None,
    now: datetime,
    reasons: tuple[str, ...],
    manual_consumed: bool,
) -> str:
    status = publication_status(published, source, now)
    if status != "trusted":
        return "publication_" + status
    assert published is not None
    if now > published + timedelta(hours=48):
        return "publication_expired"
    if reasons:
        return reasons[0]
    return "manual_change_only" if manual_consumed else "eligible"

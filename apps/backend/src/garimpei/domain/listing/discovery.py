from datetime import datetime

from garimpei.domain.listing.listing import Evidence


def publication_is_new(evidence: Evidence, started_at: datetime | None, now: datetime) -> bool:
    """Only a dated, available detail can establish a new publication."""
    stamp = evidence.published_at
    return (
        started_at is not None
        and stamp is not None
        and started_at < stamp <= now
        and evidence.source_available is True
        and evidence.price is not None
        and bool(evidence.title)
    )

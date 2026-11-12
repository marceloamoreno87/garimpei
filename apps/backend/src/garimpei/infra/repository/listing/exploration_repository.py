import hashlib
import json
from datetime import datetime, timedelta
from uuid import UUID

from django.db import connection, transaction
from django.db.models import Max

from garimpei.infra.persistence.exploration_models import ExplorationOffer, ExplorationRevision
from garimpei.infra.queries.listing.exploration_mapper import encode
from garimpei.infra.queries.listing.exploration_source import ExplorationSource

# Session lock acquired before starting the snapshot: a waiting publisher cannot publish stale data.
PUBLICATION_LOCK = 80808008


class PostgresExplorationRepository:
    def __init__(self, source: ExplorationSource, retention_seconds: int) -> None:
        self._source = source
        self._retention = retention_seconds

    def publish(self, now: datetime) -> UUID | None:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_lock(%s)", [PUBLICATION_LOCK])
        try:
            return self._publish(now)
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [PUBLICATION_LOCK])

    def _publish(self, now: datetime) -> UUID | None:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            return self._snapshot(now)

    def _snapshot(self, now: datetime) -> UUID | None:
        offers = self._source.snapshot(now)
        previous = ExplorationRevision.objects.order_by("-sequence").first()
        payloads = [encode(offer) for offer in offers]
        signature = hashlib.sha256(
            json.dumps(semantic(payloads), sort_keys=True).encode()
        ).hexdigest()
        self._expire(now)
        if previous and previous.signature == signature:
            return previous.id
        if previous is None and not offers:
            return None
        revision = ExplorationRevision.objects.create(published_at=now, signature=signature)
        ExplorationOffer.objects.bulk_create(
            [
                ExplorationOffer(
                    revision=revision,
                    listing_id=o.id,
                    first_seen_at=o.first_seen_at,
                    search=self._source.search_text(o),
                    categories=list(o.categories),
                    automatic_tab=o.condition.tab,
                    pickup=o.pickup,
                    shipping=o.shipping,
                    visible=o.visible,
                    profit=o.composition.profit.value,
                    payload=payload,
                )
                for o, payload in zip(offers, payloads, strict=True)
            ]
        )
        if previous:
            previous.superseded_at = now
            previous.save(update_fields=["superseded_at"])
        return revision.id

    def _expire(self, now: datetime) -> None:
        newest = ExplorationRevision.objects.aggregate(value=Max("sequence"))["value"]
        ExplorationRevision.objects.filter(
            superseded_at__lt=now - timedelta(seconds=self._retention)
        ).exclude(sequence=newest).delete()


def semantic(value: object) -> object:
    # Reobserving identical business data is progress, not an invitation to reorder the UI.
    technical = {
        "id",
        "observation_id",
        "evaluation_id",
        "evaluation_revision",
        "configuration_revision",
        "revision",
        "input_revision",
        "observed_at",
        "last_valid_at",
        "evaluated_at",
        "valid_until",
        "origin_diagnostic",
        "diagnostic",
        "failures",
    }
    if isinstance(value, dict):
        return {key: semantic(item) for key, item in value.items() if key not in technical}
    if isinstance(value, list):
        return [semantic(item) for item in value]
    return value

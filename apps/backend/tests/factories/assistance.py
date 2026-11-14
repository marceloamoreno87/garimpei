"""Synthetic engineering inputs; never represent independent human labels."""

import json
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from garimpei.domain.assistance.review import ReviewCommand, ReviewTicket


def identity_snapshot() -> dict[str, object]:
    return dict(
        facts=[
            dict(
                id="title-model",
                field="model",
                value="ps5",
                source="text",
                text_field="title",
                start=0,
                end=13,
                quote="PlayStation 5",
            )
        ],
        texts=dict(title="PlayStation 5 Slim Digital 825GB"),
        allowed_values=dict(model=["ps5"]),
        required_fields=["model"],
        conflict=False,
    )


def supported_response() -> dict[str, object]:
    return dict(
        outcome="supported",
        findings=[
            dict(
                field="model",
                value="ps5",
                evidence_refs=["title-model"],
                reason_code="explicit_evidence",
            )
        ],
        limitations=[],
    )


@dataclass
class NamedAssistanceRepository:
    commands: list[ReviewCommand] = field(default_factory=list)
    identity: UUID = field(default_factory=uuid4)

    def admit(self, command: ReviewCommand) -> ReviewTicket:
        self.commands.append(command)
        return ReviewTicket(self.identity, command.purpose, "pending", False)

    def reconcile(self) -> None:
        return None


def serialized_snapshot() -> str:
    return json.dumps(identity_snapshot())


def seed_observation(namespace: str, fixture: str) -> tuple[UUID, str]:
    """Namespace both public identity and UUID so shared PostgreSQL fixtures cannot collide."""
    from hashlib import sha256
    from uuid import NAMESPACE_URL, uuid5

    from django.utils.timezone import now

    from garimpei.domain.listing.listing import Evidence
    from garimpei.infra.persistence.listing_models import (
        CollectionCycle,
        CollectionState,
        Listing,
        ListingObservation,
    )
    from garimpei.infra.repository.listing.mapper import encode_evidence

    identity = uuid5(NAMESPACE_URL, "f23-assistance:" + namespace + ":" + fixture)
    external = sha256((namespace + ":" + fixture).encode()).hexdigest()[:24]
    listing, _ = Listing.objects.get_or_create(
        source="assistance-fixture",
        external_id=external,
        defaults=dict(
            id=identity,
            canonical_url="https://example.invalid/assistance/" + external,
            first_seen_at=now(),
            origin="synthetic",
        ),
    )
    state, _ = CollectionState.objects.get_or_create(
        configuration_id=identity, source="assistance-fixture"
    )
    cycle, _ = CollectionCycle.objects.get_or_create(
        id=identity, defaults=dict(state=state, scope_key="assistance-fixture", revision=1)
    )
    text = "Synthetic assistance observation " + fixture
    observation, _ = ListingObservation.objects.get_or_create(
        id=identity,
        defaults=dict(
            listing=listing,
            cycle=cycle,
            ordinal=1,
            observed_at=now(),
            evidence=encode_evidence(Evidence(title=text, description=text)),
            coverage={},
        ),
    )
    listing.latest = observation
    listing.save(update_fields=["latest"])
    return observation.id, text

"""Optional browser setup for the media lab; refuses every non-disposable database."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.utils.timezone import now

from garimpei.config.env import load_media_settings
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.listing.scope import Scope
from garimpei.domain.media.media import Manifest, Photo, Variant
from garimpei.infra.persistence.listing_models import (
    CollectionCycle,
    CollectionState,
    Listing,
    ListingInterestMatch,
    ListingObservation,
)
from garimpei.infra.persistence.media_models import MediaCapture, MediaJob
from garimpei.infra.repository.listing.mapper import decode_evidence, encode_evidence
from garimpei.infra.repository.media.captures import create_capture
from garimpei.main import (
    build_media_repository,
    build_media_runner,
    build_publish_exploration,
)
from tests.factories.monitoring import prepare_state, require_disposable


def configure_media_lab(*, page_two: bool = True) -> None:
    require_disposable()
    configuration = prepare_state("ATIVA")
    assert configuration.configuration_id is not None
    scope = Scope.from_snapshot(configuration)
    assert scope is not None
    state = CollectionState.objects.get(source="media_fixture")
    state.configuration_id = configuration.configuration_id
    state.initial_completed_at = now()
    state.save()
    CollectionCycle.objects.filter(state=state).update(
        scope_key=scope.key, revision=configuration.revision
    )
    if page_two:
        cycle = CollectionCycle.objects.filter(state=state).first()
        assert cycle is not None
        for index in range(25):
            row = Listing.objects.create(
                id=uuid4(),
                source="media_fixture",
                external_id=str(15000 + index),
                canonical_url=f"https://www.facebook.com/marketplace/item/{15000 + index}/",
                first_seen_at=now() + timedelta(seconds=1),
                origin="initial_load",
            )
            obs = ListingObservation.objects.create(
                listing=row,
                cycle=cycle,
                ordinal=1,
                observed_at=now(),
                price=Decimal("1000"),
                evidence=encode_evidence(
                    Evidence(
                        title=f"Oferta de controle {index}",
                        description="Funciona bem.",
                        condition="Funciona bem.",
                        price=Decimal("1000"),
                    )
                ),
                coverage={},
            )
            row.latest = obs
            row.ordinal = 1
            row.save()
    for observation in ListingObservation.objects.filter(cycle__state=state):
        evidence = decode_evidence(observation.evidence)
        observation.evidence = encode_evidence(replace(evidence, condition="Funciona bem"))
        observation.coverage = dict(
            pickup="confirmed",
            shipping="unknown",
            distance_km=None,
            pickup_reason="within_radius",
            shipping_reason="not_offered",
        )
        observation.save()
        ListingInterestMatch.objects.get_or_create(
            observation=observation,
            kind=scope.searches[0].interest.kind,
            key=scope.searches[0].interest.key,
        )
    # Explicit lab-only waiting state; its next action is beyond this short browser exercise.
    pending = prepare_pending_wait()
    MediaJob.objects.filter(entry__capture=pending).update(next_at=now() + timedelta(days=1))
    for _ in range(4):
        for job in build_media_repository().due(now()):
            build_media_runner().execute(job)
    build_publish_exploration().execute()


def prepare_pending_wait() -> MediaCapture:
    require_disposable()
    listing = Listing.objects.get(source="media_fixture", external_id="5")
    old = listing.latest
    assert old is not None
    capture = MediaCapture.objects.get(observation=old)
    if not capture.entries.filter(asset__isnull=False).exists():
        return capture
    # The lab may have been running before setup. Preserve that completed history
    # and prepare a genuinely new photo, rather than relabeling available bytes.
    cycle = CollectionCycle.objects.create(
        state=old.cycle.state, scope_key=old.cycle.scope_key, revision=old.cycle.revision
    )
    observation = ListingObservation.objects.create(
        listing=listing,
        cycle=cycle,
        ordinal=old.ordinal + 1,
        observed_at=now(),
        price=old.price,
        evidence=old.evidence,
        coverage=old.coverage,
    )
    for match in old.matches.all():
        ListingInterestMatch.objects.create(observation=observation, kind=match.kind, key=match.key)
    listing.latest = observation
    listing.ordinal = observation.ordinal
    listing.save()
    settings = load_media_settings()
    return create_capture(
        observation,
        Manifest(
            "present",
            (
                Photo(
                    "pending-" + str(uuid4()),
                    (Variant(str(settings.eval_origin) + "/other.png"),),
                    True,
                ),
            ),
            True,
            "",
        ),
        settings.policy,
        now(),
    )

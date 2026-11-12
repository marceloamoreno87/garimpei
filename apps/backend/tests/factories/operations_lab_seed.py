"""Controlled F17 corpus. Business policies calculate values; no real service is contacted."""

from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from garimpei.domain.alert.alert import AlertPolicy, Binding
from garimpei.domain.listing.coverage import Coverage
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.listing.scope import Scope
from garimpei.domain.media.media import Manifest
from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.policy import estimate
from garimpei.domain.valuation.values import Comparable, NewReference, Valuation
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.infra.persistence.alert_models import AlertFeedCursor, FirstAlertIdentity
from garimpei.infra.persistence.listing_models import (
    CollectionCycle,
    CollectionState,
    Listing,
    ListingInterestMatch,
    ListingObservation,
)
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
from garimpei.infra.persistence.valuation_models import (
    ValuationEvaluation,
    ValuationProgress,
    ValuationWork,
)
from garimpei.infra.repository.listing.mapper import encode_evidence
from garimpei.infra.repository.media.captures import create_capture
from garimpei.infra.repository.valuation.mapper import encode_valuation
from garimpei.main import (
    _effective_listing_settings,
    _listing_clock,
    build_alert_store,
    build_first_alert_store,
    build_navigation_catalog,
    build_operational_status,
    build_publish_exploration,
    build_read_monitoring_configuration,
    build_read_profit,
)
from tests.factories.monitoring import prepare_state, require_disposable

TITLE = "PlayStation 5 Slim disco 1TB"
COVERAGE = Coverage("confirmed", "unknown", 1.0, "within_radius", "destination_unverified")


def seed_counts(channel_url: str) -> dict[str, object]:
    require_disposable()
    if Listing.objects.exists():
        raise ValueError("Counts seed requires an empty owned business database")
    prepare_state("ATIVA")
    MonitoringConfiguration.objects.filter(slot="active").update(resale_fee_percent=Decimal("10"))
    configuration = build_read_monitoring_configuration().execute()
    scope = Scope.from_snapshot(configuration)
    assert scope is not None
    scope = build_navigation_catalog().decorate_scope(scope)
    stamp = _listing_clock(_effective_listing_settings())()
    state = CollectionState.objects.create(
        configuration_id=scope.configuration_id,
        source=scope.source,
        monitoring_started_at=stamp - timedelta(hours=2),
        initial_completed_at=stamp,
        last_success_at=stamp,
        initial_scope=scope.key,
        next_attempt_at=stamp + timedelta(days=1),
    )
    historical = _cycle(state, scope, stamp - timedelta(minutes=1), "0" * 64)
    current = _cycle(state, scope, stamp, scope.key)
    state.current = current
    state.save(update_fields=["current"])
    listings: dict[str, Listing] = {}
    comparables: list[Comparable] = []
    for index, letter in enumerate("ABCDEFGHIJKL", 1):
        row = Listing.objects.create(
            source=scope.source,
            external_id=str(170000 + index),
            canonical_url=f"https://www.facebook.com/marketplace/item/{170000 + index}/",
            first_seen_at=stamp - timedelta(minutes=1),
            origin="initial",
        )
        evidence = _evidence(TITLE if index <= 6 else "Item sem modelo", Decimal("1500"), stamp)
        old = _observation(row, historical, evidence, stamp - timedelta(minutes=1), scope)
        if index <= 6:
            comparables.append(_comparable(row, old, evidence))
        listings[letter] = row
    for index, letter in enumerate("ABCDEFGHIJ"):
        row = listings[letter]
        price: Decimal | None = (
            Decimal(["1000", "1100", "1200", "1400", "0", "1500"][index])
            if index < 6
            else Decimal("1500")
        )
        price = None if letter == "E" else price
        title = (
            TITLE
            if index < 5
            else "PlayStation 5 Slim Digital 825GB"
            if letter == "F"
            else "Item sem modelo"
        )
        evidence = _evidence(title, price, stamp)
        if letter == "D":
            evidence = Evidence(
                **(asdict(evidence) | {"published_at": stamp - timedelta(hours=49)})
            )
        if letter in "IJ":
            evidence = Evidence(title=title, price=price)
        latest = _observation(row, current, evidence, stamp, scope)
        if index < 8:
            from garimpei.config.env import load_media_settings

            create_capture(
                latest,
                Manifest(presence="none", complete=True, reason="", known_count=0),
                load_media_settings().policy,
                stamp,
            )
        if index < 6:
            _valuation(row, latest, evidence, tuple(comparables), stamp)
    build_publish_exploration().execute()
    first = build_first_alert_store()
    first.adopt(stamp)
    for row in listings.values():
        first.publish(row.id, first.prepare(row.id), build_read_profit().execute(row.id), stamp)
    _confirm_two(listings, channel_url, stamp)
    value = build_operational_status().execute()
    expected = dict(
        stored=12,
        revalidated=10,
        with_detail=8,
        recognized=6,
        with_sample=5,
        estimated=4,
        eligible=3,
        confirmed=2,
    )
    counts = value["counts"]
    assert isinstance(counts, dict)
    observed = {name: counts[name]["value"] for name in expected}
    assert observed == expected, {"expected": expected, "observed": observed}
    return {
        "scenario": "counts",
        "clock": stamp.isoformat(),
        "controlled": True,
        "ids": {letter: str(row.id) for letter, row in listings.items()},
        "sets": {name: list("ABCDEFGHIJKL"[:count]) for name, count in expected.items()},
        "counts": observed,
        "snapshot_id": value["snapshot_id"],
        "explanation": "Historical comparable observations precede the current input; D is publication-expired, E lacks purchase, F has a different recognized model. Two loopback HTTP receipts, never delivery/read proof.",
    }


def _cycle(state: CollectionState, scope: Scope, stamp: datetime, key: str) -> CollectionCycle:
    return CollectionCycle.objects.create(
        state=state,
        scope_key=key,
        revision=scope.revision,
        phase="complete",
        started_at=stamp,
        finished_at=stamp,
        scanned=True,
    )


def _evidence(title: str, price: Decimal | None, stamp: datetime) -> Evidence:
    return Evidence(
        title=title,
        description="Usado. Funcionando perfeitamente.",
        condition="Usado — seminovo",
        published_at=stamp - timedelta(hours=1),
        published_at_source="fixture.published_at",
        price=price,
        source_available=True,
    )


def _observation(
    listing: Listing, cycle: CollectionCycle, evidence: Evidence, stamp: datetime, scope: Scope
) -> ListingObservation:
    row = ListingObservation.objects.create(
        listing=listing,
        cycle=cycle,
        ordinal=listing.ordinal + 1,
        observed_at=stamp,
        price=evidence.price,
        evidence=encode_evidence(evidence),
        coverage=asdict(COVERAGE),
        provenance={"price": "fixture.detail.price", "published_at": "fixture.published_at"},
    )
    for search in scope.searches:
        ListingInterestMatch.objects.get_or_create(
            observation=row, kind=search.interest.kind, key=search.interest.key
        )
    listing.latest, listing.ordinal = row, row.ordinal
    if evidence.price is not None:
        listing.known_price = row
    listing.save()
    return row


def _comparable(listing: Listing, row: ListingObservation, evidence: Evidence) -> Comparable:
    return Comparable(
        listing.id,
        listing.source,
        listing.external_id,
        evidence.title or "",
        listing.canonical_url,
        evidence.price,
        row.observed_at,
        row.ordinal,
        evidence,
    )


def _valuation(
    listing: Listing,
    row: ListingObservation,
    evidence: Evidence,
    candidates: tuple[Comparable, ...],
    stamp: datetime,
) -> None:
    resale = estimate(_comparable(listing, row, evidence), candidates, stamp)
    work = ValuationWork.objects.create(
        listing=listing,
        revision=1,
        snapshot={"fixture": "F17 counts", "observation": str(row.id)},
        requested_at=stamp,
        next_attempt_at=stamp,
        completed=True,
    )
    identity = uuid4()
    value = Valuation(
        identity,
        listing.id,
        1,
        row.ordinal,
        identify(evidence),
        stamp,
        resale,
        NewReference("sem_referencia"),
    )
    evaluation = ValuationEvaluation.objects.create(
        id=identity, work=work, result=encode_valuation(value)
    )
    ValuationProgress.objects.create(
        listing=listing, requested=1, signature="fixture", current=evaluation
    )


def _confirm_two(listings: dict[str, Listing], url: str, stamp: datetime) -> None:
    AlertFeedCursor.objects.update_or_create(installation="local", defaults={"history_ready": True})
    store = build_alert_store()
    binding = Binding("synthetic", "100@g.us", "200@c.us")
    gateway = WahaGateway(url, "synthetic-key", AlertPolicy())
    assert gateway.check(binding)
    for letter in "AB":
        identity = FirstAlertIdentity.objects.get(listing=listings[letter])
        assert identity.intent_id is not None
        delivery = store.claim(identity.intent_id, binding, stamp, reconcile=False)
        assert delivery is not None
        outcome = gateway.send(delivery)
        assert outcome.state == "confirmed"
        store.finish(delivery, outcome, stamp)


def seed_recovery() -> None:
    from garimpei.config.env import load_config
    from garimpei.infra.repository.operations.progress_repository import (
        PostgresOperationalRepository,
    )

    require_disposable()
    stamp = _listing_clock(_effective_listing_settings())()
    progress = PostgresOperationalRepository(load_config().environment_id, lambda: stamp)
    progress.confirm("listing", "controlled-recovery", 1, "confirmed-A", stamp, pending=1)
    progress.failure("listing", "controlled-recovery", 1, "source_transport", stamp)
    progress.failure("listing", "controlled-recovery", 1, "source_transport", stamp)
    progress.confirm("valuation", "controlled-independent", 1, "confirmed-B", stamp, pending=1)


def seed_backup_choice() -> None:
    from garimpei.main import build_classify_condition

    require_disposable()
    row = Listing.objects.get(external_id="170009")
    assert build_classify_condition().execute(row.id, "good", 0) == 1


def seed_protected_photo(origin: str) -> dict[str, object]:
    from django.utils.timezone import now

    from garimpei.config.env import load_media_settings
    from garimpei.domain.media.media import Photo, Variant
    from garimpei.infra.persistence.media_models import MediaAsset
    from garimpei.main import build_media_repository, build_media_runner

    require_disposable()
    row = Listing.objects.select_related("latest").get(external_id="170011")
    assert row.latest is not None
    photo = Photo(
        "controlled-retained-photo", (Variant(origin + "/primary-large.jpg", 1280, 960),), True
    )
    manifest = Manifest("present", (photo,), True, "", 1)
    create_capture(row.latest, manifest, load_media_settings().policy, now())
    for _ in range(3):
        for identity in build_media_repository().due(now()):
            build_media_runner().execute(identity)
    asset = MediaAsset.objects.get(listing=row, state="available", thumbnail_state="ready")
    return {
        "corpus": "CONTROLLED F14 local HTTP",
        "listing_id": str(row.id),
        "version_id": str(asset.id),
        "sha256": asset.sha256,
        "thumbnail_sha256": asset.thumbnail_hash,
        "bytes": asset.byte_count,
    }

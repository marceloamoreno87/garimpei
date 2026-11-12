from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from garimpei.domain.listing.consolidation import consolidate
from garimpei.domain.listing.listing import Candidate, Evidence, Match
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.domain.navigation.catalog import Catalog, Family
from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository


def test_publication_store_accepts_scope_transform_and_alias_retains_identity() -> None:
    catalog = Catalog("1", (Family("ps5", "PlayStation 5 Slim", ("PS5 Slim",), ("pro",)),), ())
    scope = Scope(
        uuid4(),
        "facebook_marketplace",
        "01001000",
        4,
        "key",
        (Search(Match("product", "playstation 5 slim"), "PlayStation 5 Slim", "marketplace"),),
    )

    class Configuration:
        def execute(self) -> MonitoringSnapshot:
            raise AssertionError("Not called until transaction")

    store = PostgresCollectionRepository(
        Configuration(),
        lambda: datetime.now(UTC),
        lambda *_: 1,
        120,
        scope_transform=catalog.decorate_scope,
    )
    assert store is not None
    positive = Candidate(
        "101", Evidence(title="PS5 Slim funcionando", price=Decimal(2300)), "detail"
    )
    negative = Candidate(
        "102", Evidence(title="PS5 Pro funcionando", price=Decimal(3000)), "detail"
    )
    assert consolidate([positive], catalog.decorate_scope(scope)).matches == (
        scope.searches[0].interest,
    )
    assert consolidate([negative], catalog.decorate_scope(scope)).matches == ()
    assert consolidate([positive], scope).matches == ()

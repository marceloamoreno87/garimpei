from pathlib import Path

from tests.factories.listing import Source, prepare_listing_instance, serve
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import command, completed, configure, shell, sql


class UnicodeDetailSource(Source):
    def _detail(
        self, identity: str, cep: str, mode: str, price: str | None
    ) -> tuple[int, dict[str, object]]:
        status, row = super()._detail(identity, cep, mode, price)
        if identity == "101":
            row = row | {"description": "Descrição\x00sintética\ud800 com acentos e 📷\udfff"}
        return status, row


def test_invalid_detail_does_not_block_following_items_or_repeat_after_restart(
    tmp_path: Path,
) -> None:
    source = UnicodeDetailSource()
    root = Path(__file__).resolve().parents[4]
    with serve(source) as url:
        instance, clock = prepare_listing_instance(root, tmp_path, url)
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            configure(instance)
            completed(instance, 1)
            identity = sql(instance, "SELECT id FROM runtime_listing WHERE external_id='101'")
            assert len(identity) == 1
            assert sql(instance, "SELECT count(*) FROM runtime_listing") == [(4,)]
            shell(
                instance,
                """
from garimpei.infra.persistence.listing_models import Listing
listing = Listing.objects.get(external_id='101')
assert listing.latest.evidence['description'] == 'Descrição�sintética� com acentos e 📷�'
assert listing.canonical_url == 'https://www.facebook.com/marketplace/item/101/'
assert Listing.objects.get(external_id='103').latest_id is not None
""",
            )
            assert sum(path == "/detail/101" for path, _ in source.calls) == 1
            command(instance, "./scripts/stop.sh")
            clock.advance(61)
            command(instance, "./scripts/init.sh", "--disposable")
            completed(instance, 2)
            assert (
                sql(instance, "SELECT id FROM runtime_listing WHERE external_id='101'") == identity
            )
            assert sql(instance, "SELECT count(*) FROM runtime_listingobservation") == [(8,)]
            assert sum(path == "/detail/101" for path, _ in source.calls) == 2
            assert "DataError" not in (instance.config.directory / "worker.log").read_text()
        finally:
            command(instance, "./scripts/stop.sh", "--clean")


def test_live_gateway_detail_checkpoints_both_items_in_postgres(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    with serve(Source()) as url:
        instance, _ = prepare_listing_instance(root, tmp_path, url)
        command(instance, "./scripts/init.sh", "--disposable")
        group = pause_worker(instance)
        try:
            configure(instance)
            shell(instance, LIVE_DETAIL_CHECKPOINT)
        finally:
            resume_worker(group)
            command(instance, "./scripts/stop.sh", "--clean")


LIVE_DETAIL_CHECKPOINT = """
from dataclasses import replace
from datetime import UTC, datetime
from garimpei.domain.listing.ports import Attempt, CollectionPolicy
from garimpei.domain.monitoring.values import CategoryCatalog
from garimpei.infra.gateway.listing.facebook_marketplace import FacebookMarketplace
from garimpei.infra.persistence.listing_models import CollectionState, Listing
from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository
from garimpei.main import build_read_monitoring_configuration
from tests.unit.test_marketplace_source import FixedCep, RecordedNavigation

# Exercise the live gateway, Relay parser and actual PostgreSQL checkpoint together.
now = datetime(2026, 1, 1, 12, 2, 2, tzinfo=UTC)
store = PostgresCollectionRepository(build_read_monitoring_configuration(), lambda: now,
    lambda cycle_id, generation: 0, 120)
policy = CollectionPolicy(60, 120, 10, 5, 300)
store.reconcile(policy)
state = CollectionState.objects.get()
attempt = Attempt(state.current_id, state.generation)
work = store.begin(attempt)
navigation = RecordedNavigation((), [])
source = FacebookMarketplace(navigation, FixedCep(), CategoryCatalog('', '', ()))
for identity in ('601', '602'):
    navigation.detail_rows = ({
        'id': identity,
        'marketplace_listing_title': 'PlayStation 5 Slim',
        'listing_price': {'amount': '1000.00', 'currency': 'BRL'},
        'redacted_description': {'text': 'Lente sintética' + chr(0) + 'funcionando 📷'},
    },)
    candidate = replace(source.detail(work.scope, identity),
        matches=(work.scope.searches[0].interest,))
    key = 'detail:' + identity
    store.stage(attempt, key, (candidate,))
    store.record(attempt, key, None)
for query in work.scope.searches:
    store.record(attempt, query.key, None, 'source_exhausted')
store.mark_scanned(attempt, None)
while store.publish_batch(attempt):
    pass
store.finish(attempt, policy)
for identity in ('601', '602'):
    listing = Listing.objects.get(external_id=identity)
    assert listing.latest.evidence['description'] == 'Lente sintética�funcionando 📷'
    assert listing.canonical_url == 'https://www.facebook.com/marketplace/item/' + identity + '/'
assert len(navigation.calls) == 2
state.refresh_from_db()
assert state.current.finished_at is not None
assert state.current.results['detail:601'] is None
assert state.current.results['detail:602'] is None
"""

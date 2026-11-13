from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.factories.listing import ControlledClock, serve
from tests.factories.runtime import FoundationInstance
from tests.factories.valuation import (
    ValuationSource,
    prepare_valuation_instance,
    profit_rows,
    wait_valuation,
)
from tests.integration.test_collection import command, completed, configure, sql, wait_for

Scenario = tuple[FoundationInstance, ValuationSource, ControlledClock]


@pytest.fixture
def profit_scenario(tmp_path: Path) -> Iterator[Scenario]:
    source = ValuationSource(rows=profit_rows())
    with serve(source) as url:
        instance, clock = prepare_valuation_instance(
            Path(__file__).resolve().parents[4], tmp_path, url
        )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            status, _, body = instance.http("/health/ready")
            assert status == 200, body
            assert instance.manifest["disposable"] and instance.config.database.startswith(
                "garimpei_"
            )
            print(
                "F07 preflight",
                instance.config.environment_id,
                instance.config.database,
                "health_ready=200 disposable=true run=" + str(instance.manifest["run_id"]),
            )
            configure(instance)
            completed(instance, 1)
            wait_valuation(instance, price="2300.00")
            # Reconciliation creates progress in batches; a missing row is still pending.
            wait_for(
                lambda: (
                    sql(
                        instance,
                        "SELECT count(*) FROM runtime_listing l LEFT JOIN runtime_valuationprogress p ON p.listing_id=l.id WHERE p.current_id IS NULL",
                    )
                    == [(0,)]
                ),
                "all F07 valuations",
            )
            yield instance, source, clock
        finally:
            source.release.set()
            command(instance, "./scripts/stop.sh", "--clean")


IMPORTS = """
from decimal import Decimal
from garimpei.main import build_read_profit, build_read_valuation, build_read_listing, build_read_condition, build_read_monitoring_configuration, build_monitoring_handler
from garimpei.infra.persistence.listing_models import Listing,ListingEvent
from garimpei.usecase.monitoring.save_step_usecase import StepInput
read=build_read_profit()
def target(key='699'):
    return Listing.objects.get(external_id=key)
def current(key='699'):
    return read.execute(target(key).id)
"""


def check(instance: FoundationInstance, code: str) -> None:
    result = instance.shell(IMPORTS + code)
    assert result.returncode == 0, result.stdout + result.stderr
    print(result.stdout, end="")


def test_integrated_composition_matrix_and_cost_edits(profit_scenario: Scenario) -> None:
    i, source, clock = profit_scenario
    check(
        i,
        """
import json
from pathlib import Path
cases=json.loads(Path('apps/backend/tests/fixtures/valuation/cases.json').read_text())['profit']['offers']
for key,case in cases.items():
    v=current(key)
    expected=case['expected']
    assert v.profit.value==(Decimal(expected) if expected is not None else None),(key,v)
    assert v.listing_id==target(key).id and v.observation_id==target(key).latest_id
    assert v.evaluation_id==build_read_valuation().execute(v.listing_id).id
    assert v.evaluation_revision>=1 and v.configuration_revision==build_read_monitoring_configuration().execute().revision
    assert v.policy=='potential-before-freight-v2' and v.currency=='BRL'
    assert v.resale_scope=='functional_equivalent_without_repair_cost'
    assert 'repair' in v.excluded_costs
    assert v.event_id is None and v.calculated_at is not None
    print(case['item'],key,expected,'PASS')
v=current()
assert v.purchase.value==Decimal('1500') and v.purchase.state=='conhecido' and v.purchase.origin=='observation:detail'
assert v.resale.value==Decimal('2300') and v.resale.origin=='valuation' and v.resale.state=='estimado'
assert v.fee.value==Decimal('287.50') and v.fee_percent==Decimal('12.50') and v.fee.state=='estimado'
assert v.freight.value is None and v.freight.state=='nao_incluido'
assert current('709').fee.value==Decimal('12.63')
for key in ('700','701','702','703','704','705'):
    value=current(key)
    assert value.principal=='marketplace' and len(value.modalities)==1
    assert value.profit.value==Decimal('512.50') and value.freight.value is None
assert current('708').purchase.value is None and current('708').fee.value==Decimal('287.50')
for key in ('706','707'):
    before=build_read_condition().execute(target(key).id)
    assert before is not None
    assert build_read_listing().execute(target(key).id).id==current(key).listing_id
    assert build_read_condition().execute(target(key).id)==before
snap=build_read_monitoring_configuration().execute()
build_monitoring_handler()._update.execute(StepInput('editar',snap.revision,cep=snap.cep,shipping_estimate='0.00',resale_fee_percent='12.50',category_ids=snap.category_ids,product_names=snap.product_names))
v=current('702')
assert v.freight.value is None and v.freight.state=='nao_incluido' and v.profit.value==Decimal('512.50')
assert v.configuration_revision>snap.revision
print('SVC-FRETE-04 PASS')
snap=build_read_monitoring_configuration().execute()
build_monitoring_handler()._update.execute(StepInput('editar',snap.revision,cep=snap.cep,shipping_estimate='30.00',resale_fee_percent='10.00',category_ids=snap.category_ids,product_names=snap.product_names))
v=current('702')
assert v.fee.value==Decimal('230') and v.freight.value is None and v.profit.value==Decimal('570')
assert v.configuration_revision==snap.revision+1
print('SVC-RECALCULO-02 PASS')
""",
    )
    # Absence of freight scope is independently verified after normal F04 publication.
    source.rows["703"]["freight_cep"] = None
    clock.advance(61)
    completed(i, 2)
    check(
        i,
        "assert current('703').freight.value is None\nassert current('703').profit.value==Decimal('570')\n",
    )


def test_reduction_event_is_immutable_and_revalidates_cep_and_variant(
    profit_scenario: Scenario,
) -> None:
    i, source, clock = profit_scenario
    source.rows["699"]["freight"] = None
    source.rows["699"]["price"] = "R$ 1.550,00"
    clock.advance(61)
    completed(i, 2)
    source.rows["699"]["price"] = "R$ 1.500,00"
    clock.advance(61)
    completed(i, 3)
    source.rows["699"]["price"] = "R$ 1.450,00"
    clock.advance(61)
    completed(i, 4)
    check(
        i,
        """
from uuid import uuid4
from garimpei.domain.valuation.profit_queries import UnsupportedProfitEvent
row=ListingEvent.objects.get(listing=target(),kind='price_decreased',observation__price=Decimal('1500'))
v=read.execute(row.id,event=True)
assert v.purchase.value==Decimal('1500') and v.profit.value==Decimal('512.50')
assert v.event_id==row.id and v.observation_id==row.observation_id
assert current().purchase.value==Decimal('1450') and current().profit.value==Decimal('562.50')
assert current().observation_id!=v.observation_id
assert read.execute(uuid4()) is None and read.execute(uuid4(),event=True) is None
unsupported=ListingEvent.objects.filter(listing=target(),kind='price_increased').first()
try:
    read.execute(unsupported.id,event=True)
except UnsupportedProfitEvent as error:
    assert error.code=='UNSUPPORTED_PROFIT_EVENT'
else:
    raise AssertionError('unsupported event accepted')
print('SVC-RECALCULO-01/05 PASS',str(row.id),str(v.observation_id))
snap=build_read_monitoring_configuration().execute()
build_monitoring_handler()._update.execute(StepInput('editar',snap.revision,cep='02002000',shipping_estimate='25.50',resale_fee_percent='12.50',category_ids=snap.category_ids,product_names=snap.product_names))
v=read.execute(row.id,event=True)
assert v.purchase.value==Decimal('1500') and v.principal=='marketplace' and v.profit.value==Decimal('512.50')
print('SVC-FRETE-06 PASS')
""",
    )
    source.rows["699"]["title"] = "PlayStation 5 Slim disco 1TB"
    clock.advance(61)
    completed(i, 5)
    wait_valuation(i, price="101.00")
    check(
        i,
        """
row=ListingEvent.objects.get(listing=target(),kind='price_decreased',observation__price=Decimal('1500'))
assert build_read_valuation().execute(target().id).product=='sony:ps5:slim:disc:1tb'
v=read.execute(row.id,event=True)
assert v.purchase.value==Decimal('1500') and v.resale.value is None and v.profit.value is None
assert v.resale.reason=='produto_incompativel'
print('SVC-INDISPONIBILIDADE-05 PASS')
""",
    )


def test_unavailable_read_failure_draft_and_expired_resale(profit_scenario: Scenario) -> None:
    i, source, clock = profit_scenario
    check(
        i,
        """
from datetime import timedelta
from garimpei.infra.queries.valuation.profit_queries import PostgresProfitQueries
from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
from garimpei.infra.queries.valuation.postgres_queries import PostgresValuationQueries
from garimpei.usecase.valuation.read_profit_usecase import ReadProfitUseCase
from garimpei.domain.valuation.profit_queries import ProfitReadFailed
from tests.factories.valuation import FailingProfitConfiguration
from django.db import transaction
from garimpei.config.env import load_listing_settings
from garimpei.main import _listing_clock
clock=_listing_clock(load_listing_settings())
import json,logging
from io import StringIO
from garimpei.infra.runtime.logging import JsonFormatter
stream=StringIO()
handler=logging.StreamHandler(stream)
handler.setFormatter(JsonFormatter())
logger=logging.getLogger('garimpei.profit')
logger.addHandler(handler)
failed=ReadProfitUseCase(PostgresProfitQueries(FailingProfitConfiguration(),PostgresListingQueries(),PostgresValuationQueries()),clock)
try:
    failed.execute(target().id)
except ProfitReadFailed as error:
    assert error.code=='PROFIT_DEPENDENCY_UNAVAILABLE' and error.retryable
    assert error.__cause__ is None
else:
    raise AssertionError('technical failure returned a composition')
logger.removeHandler(handler)
diagnostic=json.loads(stream.getvalue())
assert diagnostic['event']=='profit_read_failed'
assert diagnostic['error_code']=='PROFIT_DEPENDENCY_UNAVAILABLE'
assert diagnostic['profit_identity']==str(target().id)
assert '01001000' not in stream.getvalue()
assert current().profit.value==Decimal('512.50')
# A consumer's READ COMMITTED transaction cannot silently weaken snapshot consistency.
try:
    with transaction.atomic():
        current()
except ProfitReadFailed:
    pass
else:
    raise AssertionError('unsafe outer transaction accepted')
print('SVC-INDISPONIBILIDADE-04 PASS')
# Used evidence expires while a separate, valid new quote exists (F06 historical proof).
v=build_read_valuation().execute(target().id)
edge=v.resale.valid_until
expired=ReadProfitUseCase(PostgresProfitQueries(build_read_monitoring_configuration(),PostgresListingQueries(),PostgresValuationQueries()),lambda:edge+timedelta(seconds=1)).execute(target().id)
assert expired.resale.value is None and expired.resale.reason=='evidencia_vencida'
assert expired.fee.value is None and expired.profit.value is None
assert expired.purchase.value==Decimal('1500') and expired.freight.value is None and expired.fee_percent==Decimal('12.50')
assert build_read_valuation().execute(v.id,historical=True).new.quote.price==Decimal('3800')
print('SVC-INDISPONIBILIDADE-01 expired PASS')
""",
    )
    source.rows["604"]["description"] = "Não funciona. Com defeito."
    clock.advance(61)
    completed(i, 2)
    wait_valuation(i, revision=2)
    # Revisions can advance while the collector is still publishing other candidates.
    # Wait for this changed input, not an unrelated intermediate evaluation revision.
    wait_for(
        lambda: (
            sql(
                i,
                "SELECT count(*) FROM runtime_valuationprogress p "
                "JOIN runtime_listing l ON p.listing_id=l.id "
                "JOIN runtime_valuationevaluation e ON p.current_id=e.id "
                "JOIN runtime_valuationwork w ON e.work_id=w.id "
                "JOIN runtime_listing c ON c.external_id='604' "
                "JOIN runtime_listingobservation o ON c.latest_id=o.id "
                "WHERE l.external_id='699' AND EXISTS ("
                "SELECT 1 FROM jsonb_array_elements(w.snapshot->'candidates') candidate "
                "WHERE candidate->>'external_id'='604' "
                "AND (candidate->>'revision')::bigint=o.ordinal)",
            )
            == [(1,)]
        ),
        "valuation published from the changed comparable 604",
    )
    check(
        i,
        """
v=build_read_valuation().execute(target().id)
assert v.resale.reason=='amostra_insuficiente' and v.new.quote.price==Decimal('3800')
p=current()
assert p.resale.value is None and p.fee.value is None and p.profit.value is None
assert p.purchase.value==Decimal('1500') and p.freight.value is None and p.fee_percent==Decimal('12.50')
print('SVC-INDISPONIBILIDADE-01 insufficient PASS')
""",
    )
    # Restore known resale before removing the active configuration via F03's draft factory.
    source.rows["604"]["description"] = "Funcionando perfeitamente."
    clock.advance(61)
    completed(i, 3)
    wait_valuation(i, price="2300.00")
    from datetime import timedelta

    source.collection_failed = True
    source.offers[0]["observed_at"] = (clock.value + timedelta(days=14)).isoformat()
    clock.advance(14 * 86400)
    wait_for(
        lambda: (
            sql(
                i,
                "SELECT (e.result->>'evaluated_at')::timestamptz "
                "FROM runtime_valuationprogress p "
                "JOIN runtime_listing l ON p.listing_id=l.id "
                "JOIN runtime_valuationevaluation e ON p.current_id=e.id "
                "WHERE l.external_id='699'",
            )
            == [(clock.value,)]
        ),
        "valuation recalculated at the expiry boundary",
    )
    boundary = wait_valuation(i, revision=4, price="2300.00")
    clock.advance(1)
    check(
        i,
        """
v=build_read_valuation().execute(target().id)
assert v.resale.price is None and v.resale.reason=='evidencia_vencida'
assert v.new.quote.price==Decimal('3800')
p=current()
assert p.profit.value is None and p.resale.value is None and p.fee.value is None
assert p.purchase.value==Decimal('1500') and p.freight.value is None and p.fee_percent==Decimal('12.50')
print('SVC-INDISPONIBILIDADE-01 expired with current new quote PASS')
""",
    )
    # F06's expiry publication can finish before F04's failing scan. Freeze time until
    # that scan commits its backoff; advancing first can move the retry past the frozen clock.
    wait_for(
        lambda: bool(
            sql(
                i,
                "SELECT c.id FROM runtime_collectionstate s JOIN runtime_collectioncycle c ON c.id=s.current_id WHERE c.finished_at IS NOT NULL AND c.phase IN ('partial','unavailable')",
            )
        ),
        "failed collection committed before recovery clock advance",
    )
    source.collection_failed = False
    clock.advance(61)
    wait_for(
        lambda: (
            sql(
                i,
                "SELECT o.observed_at FROM runtime_listing l JOIN runtime_listingobservation o ON l.latest_id=o.id WHERE l.external_id='699'",
            )
            == [(clock.value,)]
        ),
        "fresh target observation after expired evidence",
    )
    wait_valuation(i, revision=int(boundary["revision"]) + 1, price="2300.00")
    check(
        i,
        """
from tests.factories.monitoring import prepare_state
assert not prepare_state('RASCUNHO').configured
v=current()
assert v.configuration_id is None and v.configuration_revision is None and v.fee_percent is None
assert v.fee.value is None and v.profit.value is None
assert v.purchase.value==Decimal('1500') and v.resale.value==Decimal('2300')
assert v.purchase.origin=='observation:detail' and v.resale.origin=='valuation'
print('SVC-INDISPONIBILIDADE-03 PASS')
""",
    )


def test_consistent_snapshot_during_two_head_publication(profit_scenario: Scenario) -> None:
    i, source, clock = profit_scenario
    old_row = sql(
        i,
        "SELECT l.latest_id,p.current_id FROM runtime_listing l JOIN runtime_valuationprogress p ON p.listing_id=l.id WHERE l.external_id='699'",
    )[0]
    old = dict(observation=str(old_row[0]), evaluation=str(old_row[1]))
    source.rows["699"]["price"] = "R$ 1.400,00"
    source.rows["602"]["price"] = "R$ 2.350,00"
    clock.advance(61)
    completed(i, 2)
    wait_valuation(i, price="2350.00")
    check(
        i,
        "old="
        + repr(old)
        + "\n"
        + """
from uuid import UUID
import psycopg
from garimpei.config.env import load_config
from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
from garimpei.infra.queries.valuation.postgres_queries import PostgresValuationQueries
from garimpei.infra.queries.valuation.profit_queries import PostgresProfitQueries
from garimpei.usecase.valuation.read_profit_usecase import ReadProfitUseCase
class InterleavingListingReader:
    def listing(self,identity,scope):
        result=PostgresListingQueries().listing(identity,scope)
        with psycopg.connect(load_config().database_url) as c:
            c.execute('UPDATE runtime_listing SET latest_id=%s WHERE id=%s',(UUID(old['observation']),identity))
            c.execute('UPDATE runtime_valuationprogress SET current_id=%s WHERE listing_id=%s',(UUID(old['evaluation']),identity))
        return result
baseline=current()
assert baseline.purchase.value==Decimal('1400') and baseline.resale.value==Decimal('2350')
value=ReadProfitUseCase(PostgresProfitQueries(build_read_monitoring_configuration(),InterleavingListingReader(),PostgresValuationQueries()),lambda:baseline.calculated_at).execute(target().id)
assert value.purchase.value==Decimal('1400') and value.resale.value==Decimal('2350')
assert value.evaluation_id==baseline.evaluation_id and value.profit.value==Decimal('656.25')
assert current().purchase.value==Decimal('1500') and current().resale.value==Decimal('2300')
print('SNAPSHOT PASS: head switch committed after listing read; original evaluation retained in the same snapshot')
""",
    )

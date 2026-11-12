from pathlib import Path

from tests.factories.alert_scenario import (
    add_cases,
    alert_scenario,
    alert_shell,
    wait_alerts,
    wait_listing_alerts,
)
from tests.factories.valuation import listing
from tests.integration.test_collection import command, completed, sql, wait_for


def test_integrated_worker_matrix_reductions_classification_and_restart(tmp_path: Path) -> None:
    with alert_scenario(tmp_path) as (instance, source, clock, channel):
        assert not channel.messages
        add_cases(source, clock)
        clock.advance(61)
        completed(instance, 2)
        wait_alerts(instance, 3, clock)
        alert_shell(
            instance,
            """
for key,sign in [('901',1),('902',0),('903',-1)]:
    row=intent(key)
    assert row.state=='confirmed' and row.confirmed_ack>=1
    value=Decimal(row.financial['profit'])
    assert (value>0)-(value<0)==sign,(key,value)
    assert row.financial['observation_id']==str(row.first_decision.observation_id)
    assert 'R$' in row.body and target(key).canonical_url in row.body
for key in ['904','905','906']:
    assert first_state(key).state in {'excluded','waiting'}
    assert first_state(key).intent_id is None
assert not AlertIntent.objects.filter(decision__event__silent=True).exists()
# Public F05 manual correction cannot reopen an old excluded discovery.
view=build_read_condition().execute(target('905').id)
build_classify_condition().execute(target('905').id,'good',view.state.revision)
assert build_read_condition().execute(target('905').id).state.tab=='funcionam'
assert decision('905').state=='excluded'
print('WRK-ELEGIBILIDADE-01/02; E2E-CLASSIFICACAO-01 PASS')
""",
        )
        for count, price in enumerate(["2299,99", "2200,00", "2300,00", "2200,00"], 3):
            source.rows["903"]["price"] = "R$ " + price
            clock.advance(61)
            completed(instance, count)
            expected = 1 + {3: 1, 4: 2, 5: 2, 6: 3}[count]
            # The independent price/sample change may also alert manually classified905.
            # Count this listing, so another valid first alert cannot hide a missing reduction.
            wait_listing_alerts(instance, "903", expected, clock)
        alert_shell(
            instance,
            """
from django.db.models import Q
rows=list(AlertIntent.objects.filter(Q(first_decision__identity__listing=target())|Q(decision__event__listing=target())).order_by('created_at'))
assert len(rows)==4 and len({row.id for row in rows})==4
assert 'Preço anterior: R$ 2.300,00' in rows[1].body
assert 'Preço de compra: R$ 2.299,99' in rows[1].body
assert Decimal(rows[1].financial['profit'])-Decimal(rows[0].financial['profit'])==Decimal('.01')
assert len({row.financial['observation_id'] for row in rows})==4
print('WRK-ELEGIBILIDADE-04/05 PASS')
""",
        )
        before = len(channel.messages)
        clock.advance(61)
        completed(instance, 7)
        assert len(channel.messages) == before
        command(instance, "./scripts/stop.sh")
        clock.advance(1)
        source.rows["909"] = listing(
            "909",
            "1000,00",
            published_at=clock.value.isoformat(),
            delivery=True,
            delivery_cep="01001000",
            pickup=False,
        )
        clock.advance(61)
        command(instance, "./scripts/init.sh", "--disposable")
        completed(instance, 8)
        wait_alerts(instance, before + 1, clock)
        assert len(channel.messages) == before + 1
        wait_for(
            lambda: (
                sql(
                    instance,
                    "SELECT count(*) FROM runtime_alertintent WHERE decision_id IN (SELECT id FROM runtime_alerteventdecision WHERE event_id IN (SELECT id FROM runtime_listingevent WHERE silent))",
                )
                == [(0,)]
            ),
            "silent state retained",
        )
        print("WRK-RETOMADA-01 / WRK-ELEGIBILIDADE-07 PASS")


def test_manual_history_at_publication_and_revalidation(tmp_path: Path) -> None:
    from tests.factories.alert_scenario import pause_worker, resume_worker

    with alert_scenario(tmp_path, enabled=False) as (instance, source, clock, channel):
        add_cases(source, clock)
        clock.advance(61)
        completed(instance, 2)
        clock.advance(6)
        wait_for(
            lambda: sql(instance, "SELECT count(*) FROM runtime_alertintent") == [(3,)],
            "eligible intents waiting for configuration",
            seconds=35,
        )
        source.rows["903"]["description"] = "Com defeito. Não funciona."
        clock.advance(61)
        completed(instance, 3)
        group = pause_worker(instance)
        try:
            alert_shell(
                instance,
                """
from garimpei.domain.listing.read_models import ChangePage
from garimpei.main import build_read_listing_changes
# Remove only the unprocessed decision: reconstruct the delayed-consumer scenario.
AlertEventDecision.objects.filter(event__listing=target('905')).delete()
view=build_read_condition().execute(target('905').id)
build_classify_condition().execute(view.id,'defect',view.state.revision)
view=build_read_condition().execute(view.id)
assert view.state.tab=='defeitos'
build_classify_condition().execute(view.id,'good',view.state.revision)
view=build_read_condition().execute(view.id)
assert view.state.tab=='funcionam'
page=build_read_listing_changes().execute()
store.ingest(page,clock())
assert decision('905').state=='excluded' and decision('905').reason=='first_eligibility_managed'
assert not AlertIntent.objects.filter(decision=decision('905')).exists()
assert ManualConditionHistory.objects.filter(listing=view.id).count()==2
# A legacy event whose manual order cannot be established is explicitly excluded.
from garimpei.infra.queries.alert.event_source import event_condition
legacy=decision('905').event
legacy.publication_order=None
assert event_condition(legacy).reason=='condition_history_unavailable'
print('E2E-CLASSIFICACAO-02/03 PASS')
# The F04 observation published while the channel waited now contains a defect.
assert intent().state in ['queued','blocked']
AlertIntent.objects.filter(id=intent().id).update(next_action=clock())
assert store.claim(intent().id,binding,clock(),reconcile=False) is None
assert intent().state=='cancelled' and intent().reason=='condition_excluded'
assert not AlertAttempt.objects.filter(intent=intent()).exists()
print('WRK-ELEGIBILIDADE-06 condition PASS')
# Upgrade an actual dependency database with manual choices and preserve its history.
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
counts=(Listing.objects.count(),ListingEvent.objects.count())
assert not AlertAttempt.objects.exists()
FirstAlertIdentity.objects.update(intent=None)
AlertIntent.objects.all().delete()
FirstEligibilityDecision.objects.all().delete()
FirstAlertIdentity.objects.all().delete()
MigrationExecutor(connection).migrate([('runtime','0007_exploration')])
MigrationExecutor(connection).migrate([('runtime','0008_alert_delivery')])
executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
assert (Listing.objects.count(),ListingEvent.objects.count())==counts
view=build_read_condition().execute(target('905').id)
assert view.state.tab=='funcionam' and view.state.revision==2
assert ManualConditionHistory.objects.get(listing=view.id).publication_order==0
assert event_condition(ListingEvent.objects.get(id=legacy.id)).reason=='condition_history_unavailable'
executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
print('MIGRATION-UPGRADE with existing F04/F05/F06 history PASS')
""",
            )
        finally:
            resume_worker(group)
        assert not channel.messages


def test_interest_edit_republication_allows_unknown_logistics(tmp_path: Path) -> None:
    with alert_scenario(tmp_path) as (instance, source, clock, channel):
        # Put new cards in the source before changing scope; no collection is due
        # at the frozen clock. The real worker remains active during the edit.
        clock.advance(1)
        source.rows["921"] = listing(
            "921",
            "1000,00",
            published_at=clock.value.isoformat(),
            delivery=True,
            delivery_cep="01001000",
            pickup=False,
        )
        clock.advance(1)
        source.rows["922"] = listing(
            "922",
            "1000,00",
            published_at=clock.value.isoformat(),
            delivery=True,
            delivery_cep="01001000",
            pickup=False,
        )
        clock.advance(1)
        source.rows["923"] = listing("923", "1000,00", published_at=clock.value.isoformat())
        alert_shell(
            instance,
            """
from garimpei.main import build_read_monitoring_configuration,build_monitoring_handler
from garimpei.usecase.monitoring.save_step_usecase import StepInput
config=build_read_monitoring_configuration().execute()
build_monitoring_handler()._update.execute(StepInput('editar',config.revision,
    cep=config.cep,shipping_estimate=str(config.shipping_estimate),
    resale_fee_percent=str(config.resale_fee_percent),category_ids=config.category_ids,
    product_names=config.product_names+('PlayStation 5 Slim Digital 825GB',)))
""",
        )
        clock.advance(61)
        completed(instance, 2)
        wait_alerts(instance, 3, clock)
        alert_shell(
            instance,
            """
assert intent('921').id!=intent('922').id
assert intent('921').state==intent('922').state=='confirmed'
assert intent('923').state=='confirmed'
assert '*Lucro estimado:' in intent('923').body
assert 'frete/transporte' not in intent('923').body.lower()
assert ListingEvent.objects.filter(kind='discovered',listing__external_id='600').count()==0
assert not AlertIntent.objects.filter(decision__event__listing__external_id='600').exists()
print('WRK-ELEGIBILIDADE-07 new interest / republication / old identity PASS')
""",
        )
        assert len(channel.messages) == 3


def test_incremental_comparables_complete_the_same_waiting_discovery(tmp_path: Path) -> None:
    with alert_scenario(tmp_path) as (instance, source, clock, channel):
        source.rows["604"]["description"] = "Com defeito."
        clock.advance(1)
        source.rows["951"] = listing("951", "1000,00", published_at=clock.value.isoformat())
        clock.advance(61)
        completed(instance, 2)
        wait_for(
            lambda: (
                sql(
                    instance,
                    """
            SELECT d.state,d.reason FROM runtime_firstalertidentity d
            JOIN runtime_listing l ON l.id=d.listing_id
            WHERE l.external_id='951'
        """,
                )
                == [("waiting", "amostra_insuficiente")]
            ),
            "same discovery waiting for references",
            seconds=35,
        )
        assert not channel.messages
        source.rows["604"]["description"] = "Funcionando perfeitamente."
        clock.advance(61)
        completed(instance, 3)
        wait_alerts(instance, 1, clock)
        assert len(channel.messages) == 1
        assert sql(
            instance,
            "SELECT count(*) FROM runtime_listingevent e JOIN runtime_listing l ON l.id=e.listing_id WHERE l.external_id='951' AND kind='discovered'",
        ) == [(1,)]
        assert sql(instance, "SELECT count(*) FROM runtime_alertintent") == [(1,)]

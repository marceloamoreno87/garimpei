import re
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from tests.factories.condition_http import ConditionBrowser
from tests.factories.exploration import KEYS, ExplorationSource, prepare_exploration_instance
from tests.factories.listing import ControlledClock, serve
from tests.factories.runtime import FoundationInstance
from tests.integration.test_collection import command, completed, shell, sql, wait_for


@pytest.fixture
def exploration(
    tmp_path: Path,
) -> Iterator[tuple[FoundationInstance, ExplorationSource, ControlledClock]]:
    source = ExplorationSource()
    with serve(source) as origin:
        instance, clock = prepare_exploration_instance(
            Path(__file__).resolve().parents[4], tmp_path, origin
        )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            assert instance.http("/health/ready")[0] == 200
            assert "Prepare seu acompanhamento" in instance.http("/ofertas/")[2]
            shell(instance, "from tests.factories.exploration import configure; configure()")
            completed(instance, 1)
            wait_profit(instance, "530.00")
            yield instance, source, clock
        finally:
            command(instance, "./scripts/stop.sh", "--clean")


def latest(instance: FoundationInstance) -> str:
    return str(
        sql(instance, "SELECT id FROM runtime_explorationrevision ORDER BY sequence DESC LIMIT 1")[
            0
        ][0]
    )


def wait_profit(instance: FoundationInstance, price: str) -> None:
    wait_for(
        lambda: (
            sql(
                instance,
                "SELECT profit FROM runtime_explorationoffer WHERE listing_id='00000000-0000-0000-0000-000000000004' AND revision_id=(SELECT MAX(sequence) FROM runtime_explorationrevision)",
            )
            == [(__import__("decimal").Decimal(price),)]
        ),
        "published CAM04 " + price,
        seconds=45,
    )

    # Incremental pricing can publish the target before the rest of its input cohort.
    # These snapshot assertions begin only after every requested head is published.
    wait_for(
        lambda: (
            sql(
                instance,
                """
            SELECT count(*) FROM runtime_listing l
            LEFT JOIN runtime_valuationprogress p ON p.listing_id=l.id
            LEFT JOIN runtime_valuationevaluation e ON e.id=p.current_id
            LEFT JOIN runtime_valuationwork w ON w.id=e.work_id
            WHERE p.requested IS NULL OR w.revision IS DISTINCT FROM p.requested
        """,
            )
            == [(0,)]
        ),
        "all pricing heads settled before snapshot assertions",
        seconds=45,
    )
    shell(
        instance,
        "from garimpei.main import build_publish_exploration; build_publish_exploration().execute()",
    )


def offered(body: str) -> list[str]:
    return re.findall(r'data-key="([^"]+)"', body)


def test_order_snapshots_update_manual_and_history(
    exploration: tuple[FoundationInstance, ExplorationSource, ControlledClock],
) -> None:
    i, source, clock = exploration
    version = latest(i)
    query = f"?aba=funcionam&q=camera&categoria=cameras&modalidade=retirada&versao={version}"
    bodies = [i.http("/ofertas/" + query + f"&pagina={p}")[2] for p in (1, 2, 3)]
    ordered = [key for body in bodies for key in offered(body)]
    assert [len(offered(body)) for body in bodies] == [20, 20, 12]
    assert ordered[:4] == [KEYS[k] for k in ("CAM02", "CAM03", "CAM01", "CAM04")]
    assert len(set(ordered)) == 52
    assert ordered[39:41] == [KEYS["CAM40"], KEYS["CAM41"]]
    assert ordered[-1] == KEYS["CAM42"]
    assert (
        "R$ 0,00" in bodies[1]
        and "−R$ 50,00" in bodies[2]
        and "Estimativa indisponível" in bodies[2]
    )
    assert "41–52 de 52" in bodies[2] and "Página 3 de 3" in bodies[2]
    for query_error in ("?aba=wrong", "?pagina=-1", "?versao=bad", "?categoria=not-known"):
        assert i.http("/ofertas/" + query_error)[0] == 400
    assert i.http(f"/ofertas/?versao={uuid4()}")[0] == 410
    assert i.http(f"/ofertas/{uuid4()}/")[0] == 404
    detail = i.http(f"/ofertas/{UUID(int=4)}/" + query)[2]
    for value in (
        "R$ 1.000,00",
        "R$ 1.700,00",
        "R$ 170,00",
        "R$ 530,00",
        "R$ 2.400,00",
    ):
        assert value in detail, value
    assert detail.count("Abrir referência</a>") == 5
    assert "Lucro estimado" in detail
    assert "frete/transporte" not in detail.lower()
    assert "Frete ·" not in detail and "exploration-modality" not in bodies[0]
    assert "Referência de novo indisponível" in i.http(f"/ofertas/{UUID(int=5)}/")[2]
    assert "Imagem não disponível" in i.http(f"/ofertas/{UUID(int=42)}/")[2]
    assert "Há atualizações" not in i.http("/ofertas/atualizacoes/" + query)[2]
    # Technical reobservations with identical commercial fields do not publish a revision.
    clock.advance(61)
    completed(i, 2)
    shell(
        i,
        "from garimpei.main import build_publish_exploration; build_publish_exploration().execute()",
    )
    assert latest(i) == version
    source.change_a()
    clock.advance(61)
    completed(i, 3)
    wait_profit(i, "830.00")
    updated = latest(i)
    assert updated != version and "Há atualizações" in i.http("/ofertas/atualizacoes/" + query)[2]
    assert offered(i.http("/ofertas/" + query)[2]) == offered(bodies[0])
    assert "R$ 530,00" in i.http(f"/ofertas/{UUID(int=4)}/" + query)[2]
    fresh = i.http("/ofertas/" + query.replace("&versao=" + version, ""))[2]
    assert offered(fresh)[0] == KEYS["CAM04"] and "R$ 830,00" in fresh
    shell(
        i,
        """
from decimal import Decimal
from garimpei.main import build_read_profit,build_read_listing_changes
from garimpei.infra.persistence.listing_models import ListingEvent
row=ListingEvent.objects.filter(listing_id='00000000-0000-0000-0000-000000000004',kind='price_decreased').latest('sequence')
page=build_read_listing_changes().execute(None,100)
assert any(event.id==row.id for event in page.events)
value=build_read_profit().execute(row.id,event=True)
assert value.profit.value==Decimal('830') and value.observation_id==row.observation_id
print('independent event consumer',row.id,row.observation_id,value.profit.value)
""",
    )
    browser = ConditionBrowser(i)
    identity = str(UUID(int=49))
    assert browser.choose(identity, "good")[0] == 303
    assert identity in i.http("/ofertas/?aba=funcionam&q=incerta&versao=" + version)[2]
    assert identity not in i.http("/ofertas/" + query.replace("aba=funcionam", "aba=incerta"))[2]
    assert "R$ 530,00" in i.http(f"/ofertas/{UUID(int=4)}/" + query)[2]
    source.change_b()
    clock.advance(61)
    completed(i, 4)
    wait_for(lambda: latest(i) != updated, "coverage revision")
    fresh = i.http("/ofertas/" + query.replace("&versao=" + version, "") + "&pagina=3")[2]
    assert "41–53 de 53" in fresh and "Página 3 de 3" in fresh
    # Transaction failure cannot publish half a revision or replace the readable head.
    shell(
        i,
        """
from unittest.mock import patch
from django.db import DatabaseError
from garimpei.main import build_publish_exploration
from garimpei.infra.persistence.exploration_models import ExplorationRevision,ExplorationOffer
from garimpei.infra.queries.listing.exploration_source import ExplorationSource
before=list(ExplorationRevision.objects.values_list('id',flat=True))
with patch.object(ExplorationSource,'snapshot',side_effect=DatabaseError('controlled')):
    try: build_publish_exploration().execute()
    except DatabaseError: pass
    else: raise AssertionError('failure swallowed')
assert before==list(ExplorationRevision.objects.values_list('id',flat=True))
""",
    )
    source.rows[KEYS["CAM04"]]["source_available"] = False
    clock.advance(61)
    completed(i, 5)
    wait_for(
        lambda: KEYS["CAM04"] not in offered(i.http("/ofertas/?q=camera&modalidade=retirada")[2]),
        "confirmed removal",
    )
    assert "Anúncio indisponível na origem" in i.http(f"/ofertas/{UUID(int=4)}/")[2]
    assert "R$ 530,00" in i.http(f"/ofertas/{UUID(int=4)}/" + query)[2]


def test_costs_references_expiry_failures_and_concurrent_publishers(
    exploration: tuple[FoundationInstance, ExplorationSource, ControlledClock],
) -> None:
    i, source, clock = exploration
    original = latest(i)
    shell(
        i,
        """
from django.test import Client,RequestFactory
from unittest.mock import patch
from django.db import DatabaseError
from garimpei.infra.queries.listing.exploration_queries import PostgresExplorationQueries
from garimpei.main import build_condition_handler
with patch.object(PostgresExplorationQueries,'_page',side_effect=DatabaseError('controlled-private-error')):
    result=Client().get('/ofertas/?q=camera&pagina=2',HTTP_HOST='127.0.0.1',HTTP_HX_REQUEST='true')
    assert result.status_code==503
    assert b'controlled-private-error' not in result.content
    assert b'Nenhuma oferta neste recorte' not in result.content
# F05's original programmatic adapter remains compatible.
legacy=build_condition_handler().handle(RequestFactory().get('/ofertas/'))
assert legacy.status_code==200
print('controlled read failure HTTP=503; F05 compatibility=200')
""",
    )
    shell(
        i,
        """
from garimpei.main import build_read_monitoring_configuration,build_monitoring_handler,build_read_profit
from garimpei.usecase.monitoring.save_step_usecase import StepInput
from decimal import Decimal
from uuid import UUID
snap=build_read_monitoring_configuration().execute()
build_monitoring_handler()._update.execute(StepInput('editar',snap.revision,cep=snap.cep,shipping_estimate='34.00',resale_fee_percent='20.00',category_ids=snap.category_ids,product_names=snap.product_names))
assert build_read_profit().execute(UUID(int=4)).profit.value==Decimal('360.00')
""",
    )
    wait_profit(i, "360.00")
    assert "Há atualizações" in i.http("/ofertas/atualizacoes/?versao=" + original)[2]
    assert "R$ 530,00" in i.http(f"/ofertas/{UUID(int=4)}/?versao=" + original)[2]
    costs = latest(i)
    # Cost changes are isolated from marketplace events and from used-reference changes.
    event_count = sql(i, "SELECT count(*) FROM runtime_listingevent")[0][0]
    source.rows["20003"]["price"] = "R$ 1.720,00"
    clock.advance(61)
    completed(i, 2)
    wait_profit(i, "376.00")
    assert (
        latest(i) != costs
        and sql(i, "SELECT count(*) FROM runtime_listingevent")[0][0] != event_count
    )  # reference itself emits a price event; target emits none
    assert sql(
        i,
        "SELECT count(*) FROM runtime_listingevent WHERE listing_id='00000000-0000-0000-0000-000000000004' AND kind IN ('price_decreased','discovered')",
    ) == [(0,)]
    assert "Há atualizações" in i.http("/ofertas/atualizacoes/?versao=" + costs)[2]
    assert "R$ 1.720,00" not in i.http(f"/ofertas/{UUID(int=4)}/?versao=" + costs)[2]
    assert "R$ 360,00" in i.http(f"/ofertas/{UUID(int=4)}/?versao=" + costs)[2]
    assert "R$ 1.720,00" in i.http(f"/ofertas/{UUID(int=4)}/")[2]
    shell(
        i,
        """
from concurrent.futures import ThreadPoolExecutor
from django.db import connections
from django.test.utils import CaptureQueriesContext
from django.db import connection
from garimpei.main import build_publish_exploration
from garimpei.infra.queries.listing.exploration_queries import PostgresExplorationQueries
from garimpei.domain.listing.exploration import Criteria
from garimpei.infra.persistence.exploration_models import ExplorationRevision,ExplorationOffer
from django.utils import timezone
from datetime import timedelta
before=ExplorationRevision.objects.count()
def publish(_):
    try:return build_publish_exploration().execute()
    finally:connections.close_all()
with ThreadPoolExecutor(2) as pool:
    values=list(pool.map(publish,range(2)))
assert values[0]==values[1] and ExplorationRevision.objects.count()==before
with CaptureQueriesContext(connection) as queries:
    page=PostgresExplorationQueries().page(Criteria(category='cameras'))
assert len(queries)<=10,len(queries)
print('concurrent publishers same revision; page query count',len(queries))
head=ExplorationRevision.objects.latest('sequence')
ExplorationRevision.objects.exclude(sequence=head.sequence).update(superseded_at=timezone.now()-timedelta(days=365))
build_publish_exploration().execute()
assert ExplorationRevision.objects.filter(id=head.id).exists()
assert not ExplorationRevision.objects.exclude(id=head.id).exists()
""",
    )
    assert i.http("/ofertas/?q=camera&modalidade=retirada&versao=" + original)[0] == 410
    assert i.http(f"/ofertas/{UUID(int=4)}/?versao=" + original)[0] == 410

import re
from pathlib import Path
from uuid import uuid4

from tests.factories.alert import WahaServer, serve_waha
from tests.factories.exploration import prepare_exploration_instance
from tests.factories.financial_presentation_lab import FinancialSource, publish_and_check
from tests.factories.listing import serve
from tests.integration.test_collection import command, completed, shell, sql


def test_published_financial_html_preserves_components_pages_and_http_errors(
    tmp_path: Path,
) -> None:
    source, channel = FinancialSource(), WahaServer()
    with serve(source) as origin, serve_waha(channel):
        instance, _ = prepare_exploration_instance(
            Path(__file__).resolve().parents[4], tmp_path, origin
        )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            shell(
                instance,
                "from tests.factories.financial_presentation_lab import configure_financial; configure_financial()",
            )
            completed(instance, 1)
            publish_and_check(instance)
            pages = [instance.http("/ofertas/?q=Oferta&pagina=" + str(p)) for p in (1, 2, 3)]
            keys = [re.findall(r'data-key="([^"]+)"', b) for _, _, b in pages]
            assert [len(k) for k in keys] == [20, 20, 2]
            assert len(set(k for page in keys for k in page)) == 42
            assert "R$ 0,00" in pages[1][2] and "−R$ 50,00" in pages[2][2]
            assert "Estimativa indisponível" in pages[2][2]
            identity = sql(
                instance, "SELECT id::text FROM runtime_listing WHERE external_id='10001'"
            )[0][0]
            status, _, body = instance.http(f"/ofertas/{identity}/?q=Oferta")
            assert status == 200
            assert (
                body.index("Preço de compra")
                < body.index("Preço de venda estimado")
                < body.index("Lucro estimado")
            )
            for value in [
                "R$ 1.000,00",
                "R$ 1.500,00",
                "R$ 350,00",
                "R$ 150,00",
                "R$ 2.400,00",
                "10,00%",
            ]:
                assert value in body
            # Original seller text remains separate from generated financial copy.
            assert "frete conforme vendedor" in body
            assert "frete/transporte" not in body
            assert instance.http("/ofertas/?pagina=-1")[0] == 400
            assert instance.http(f"/ofertas/{uuid4()}/")[0] == 404
            assert instance.http(f"/ofertas/?versao={uuid4()}")[0] == 410
            shell(
                instance,
                """
from django.test import Client
from django.db import DatabaseError
from unittest.mock import patch
from garimpei.infra.queries.listing.exploration_queries import PostgresExplorationQueries
with patch.object(PostgresExplorationQueries,'_page',side_effect=DatabaseError('controlled read fault')):
 r=Client().get('/ofertas/?q=Oferta&pagina=2',HTTP_HX_REQUEST='true',HTTP_HOST='127.0.0.1')
 assert r.status_code==503 and 'controlled read fault' not in r.content.decode()
 assert 'q=Oferta' in r.content.decode() and 'pagina=2' in r.content.decode()
from garimpei.infra.persistence.exploration_models import ExplorationOffer
from uuid import uuid4
row=ExplorationOffer.objects.filter(listing__external_id='10001').latest('revision_id')
row.payload['composition']['observation_id']=str(uuid4());row.save(update_fields=['payload'])
""",
            )
            body = instance.http(f"/ofertas/{identity}/")[2]
            assert "Composição indisponível para esta revisão" in body and "R$ 1.000,00" in body
            assert "R$ 350,00" not in body
            assert not channel.messages
        finally:
            command(instance, "./scripts/stop.sh", "--clean")

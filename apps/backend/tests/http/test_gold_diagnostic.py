from tests.factories.gold_driver import GoldDriver
from tests.integration.test_gold_authorization import gold_driver as gold_driver


def test_gold_html_is_read_only_and_projection_failure_preserves_offer(
    gold_driver: GoldDriver,
) -> None:
    gold_driver.action("prepare", case="BASE")
    gold_driver.shell("""
from uuid import uuid4
from unittest.mock import patch
from django.test import RequestFactory
from garimpei.main import build_exploration_handler,build_read_alert_diagnostic
from garimpei.infra.queries.alert.gold_queries import PostgresGoldDiagnosticQueries
from garimpei.domain.alert.gold_diagnostic import GoldDiagnosticReadFailed
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.gold_models import GoldQualification
from garimpei.infra.persistence.alert_models import AlertIntent,AlertAttempt
listing=Listing.objects.get(external_id='21001');before=(GoldQualification.objects.count(),AlertIntent.objects.count(),AlertAttempt.objects.count())
path=f'/ofertas/{listing.id}/?aba=funcionam&q=PlayStation&pagina=1'
handler=build_exploration_handler();response=handler.handle(RequestFactory().get(path),listing.id)
assert response.status_code==200;body=response.content.decode()
assert 'Produto normalizado: PlayStation 5 Slim com leitor 1 TB' in body
assert 'gold-alert-v1' in body and 'mediana de preços pedidos' in body
assert 'Preço de compra' in body and '3.000,00' in body
assert (GoldQualification.objects.count(),AlertIntent.objects.count(),AlertAttempt.objects.count())==before
with patch.object(PostgresGoldDiagnosticQueries,'read',side_effect=GoldDiagnosticReadFailed()):
 response=handler.handle(RequestFactory().get(path),listing.id);body=response.content.decode()
 assert response.status_code==200 and 'Não foi possível consultar a qualificação do alerta' in body
 assert 'PlayStation 5' in body and 'pagina=1' in body
assert build_read_alert_diagnostic().execute(uuid4()) is None
""")

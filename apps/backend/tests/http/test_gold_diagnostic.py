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


def test_same_clock_new_profit_revision_replaces_current_gold_diagnostic(
    gold_driver: GoldDriver,
) -> None:
    gold_driver.action("prepare", case="BASE")
    gold_driver.action("prepare", case="PROFIT_ZERO")
    gold_driver.shell("""
from django.test import RequestFactory
from garimpei.main import build_read_alert_diagnostic,build_exploration_handler,build_qualify_gold_alert
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
from garimpei.infra.persistence.gold_models import GoldQualification
listing=Listing.objects.get(external_id='21001')
identity=FirstAlertIdentity.objects.get(listing=listing)
decisions=list(identity.decisions.order_by('generation'))
assert len(decisions)>=2 and decisions[0].evaluated_at==decisions[-1].evaluated_at
assert decisions[-1].financial['profit']=='0.00'
current=build_qualify_gold_alert().execute(listing.id)
assert current.state=='blocked' and current.reason=='gold_profit_non_positive'
diagnostic=build_read_alert_diagnostic().execute(listing.id,listing.latest_id)
assert diagnostic.gold and diagnostic.gold.current
assert diagnostic.gold.reason=='gold_profit_non_positive'
assert 'zero ou negativo' in diagnostic.label
assert 'Pronta para envio' not in diagnostic.label
assert diagnostic.current_reason=='gold_profit_non_positive'
path='/ofertas/?aba=funcionam&q=PlayStation&pagina=1'
response=build_exploration_handler().handle(RequestFactory().get(path))
assert response.status_code==200
body=response.content.decode()
assert 'Lucro estimado zero ou negativo impede alerta' in body
assert 'Pronta para envio; aguardando o canal' not in body
assert GoldQualification.objects.filter(listing=listing,state='qualified').exists()
""")


def test_gold_diagnostic_preserves_history_suspension_over_queued_intent(
    gold_driver: GoldDriver,
) -> None:
    gold_driver.action("prepare", case="BASE")
    gold_driver.action("prepare", case="PROFIT_ZERO")
    gold_driver.shell("""
from unittest.mock import patch
from garimpei.main import build_read_alert_diagnostic
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import AlertFeedCursor,FirstAlertInventory
from garimpei.infra.queries.alert.gold_queries import PostgresGoldDiagnosticQueries
from garimpei.domain.alert.gold_diagnostic import GoldDiagnosticReadFailed
listing=Listing.objects.get(external_id='21001')
for suspension in ('dispatch','inventory'):
 AlertFeedCursor.objects.update(dispatch_suspended=suspension=='dispatch')
 FirstAlertInventory.objects.update(completed=suspension!='inventory')
 diagnostic=build_read_alert_diagnostic().execute(listing.id,listing.latest_id)
 assert diagnostic.state=='suspended' and diagnostic.reason=='history_unavailable'
 assert diagnostic.gold and diagnostic.gold.reason=='gold_profit_non_positive'
 assert diagnostic.current_reason=='gold_profit_non_positive'
 with patch.object(PostgresGoldDiagnosticQueries,'read',side_effect=GoldDiagnosticReadFailed()):
  diagnostic=build_read_alert_diagnostic().execute(listing.id,listing.latest_id)
  assert diagnostic.state=='suspended' and diagnostic.reason=='history_unavailable'
  assert diagnostic.gold_failed
""")

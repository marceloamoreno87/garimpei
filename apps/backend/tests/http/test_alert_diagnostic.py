from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_alert_review_regressions import PREPARE


def test_public_diagnostic_fields_history_and_partial_http_failure(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, _, _):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                PREPARE
                + """
from uuid import uuid4
from unittest.mock import patch
from django.db import DatabaseError
from django.test import RequestFactory
from garimpei.domain.alert.diagnostic import AlertDiagnosticReadFailed
from garimpei.domain.alert.alert import Outcome,Receipt
from garimpei.main import build_read_alert_diagnostic,build_exploration_handler,build_publish_exploration
from garimpei.infra.queries.alert.diagnostic_queries import PostgresAlertDiagnosticQueries
from garimpei.usecase.alert.read_alert_diagnostic_usecase import ReadAlertDiagnosticUseCase
from garimpei.infra.persistence.alert_models import AlertAttempt
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l);intent=r.intent
reader=build_read_alert_diagnostic()
before=(AlertIntent.objects.count(),AlertAttempt.objects.count())
d=reader.execute(l.id,l.latest_id)
assert d.first_alert_state=='queued'
assert d.next_action_at==intent.next_action
assert d.valuation_revision==intent.first_decision.financial['evaluation_revision']
assert d.intent_reference==intent.id
assert d.observation_id==l.latest_id and d.matches_displayed_observation
assert d.condition_revision==intent.first_decision.condition_revision
from garimpei.main import build_read_condition
assert d.condition_revision==build_read_condition().execute(l.id).state.revision
assert d.evaluated_at is not None and d.first_alert_deadline==now+timedelta(hours=46)
assert reader.execute(l.id,uuid4()).matches_displayed_observation is False
assert reader.execute(uuid4()) is None
old_title=e['title'];e['title']='Console sem modelo identificado';l.latest.evidence=e;l.latest.save()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
u=reader.execute(l.id,l.latest_id)
assert u.current_reason=='produto_indeterminado' and 'produto_incompativel' not in u.reasons,u
# Restore the producer input before the original transmission assertions.
e['title']=old_title;l.latest.evidence=e;l.latest.save()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
assert (AlertIntent.objects.count(),AlertAttempt.objects.count())==before
with patch.object(PostgresAlertDiagnosticQueries,'_read',side_effect=DatabaseError('controlled')):
 try:reader.execute(l.id)
 except AlertDiagnosticReadFailed:pass
 else:raise AssertionError('technical failure was hidden as absence')
delivery=store.claim(intent.id,binding,now,reconcile=False)
store.finish(delivery,Outcome('uncertain','response_lost'),now)
d=reader.execute(l.id,l.latest_id);assert d.state=='uncertain' and 'incerto' in d.label
store.finish(delivery,Outcome('confirmed','ack',Receipt('svc-receipt',True,binding.recipient,delivery.body,1)),now)
e['description']='Com defeito. Não funciona.';l.latest.evidence=e;l.latest.save()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
d=reader.execute(l.id,l.latest_id)
assert d.first_alert_state=='confirmed' and d.confirmed_at==now
assert d.state=='confirmed' and d.current_reason=='condition_excluded'
assert 'condition_excluded' in d.reasons
# A later uncertain reduction remains primary while the first receipt stays confirmed.
event=ListingEvent.objects.create(listing=l,observation=l.latest,kind='price_decreased',silent=False,occurred_at=now,publication_order=l.publication_order)
decision=AlertEventDecision.objects.create(event=event,state='eligible',reason='eligible',next_action=now)
AlertIntent.objects.create(decision=decision,state='uncertain',reason='response_lost',body='synthetic reduction',created_at=now+timedelta(seconds=1),next_action=now)
d=reader.execute(l.id,l.latest_id);assert d.first_alert_state=='confirmed' and d.state=='uncertain' and d.confirmed_at==now
latest=r.decisions.latest('generation');latest.reason='analysis_pending';latest.save(update_fields=['reason'])
before_read=(AlertIntent.objects.count(),AlertAttempt.objects.count())
d=reader.execute(l.id,l.latest_id);assert d.current_reason=='analysis_pending' and d.current_label=='Aguardando análise das fotos'
assert (AlertIntent.objects.count(),AlertAttempt.objects.count())==before_read
build_publish_exploration().execute()
handler=build_exploration_handler()
path=f'/ofertas/{l.id}/?aba=defeitos&q=PlayStation&pagina=1'
request=RequestFactory().get(path)
class FailingDiagnostic:
 def read(self,listing_id,displayed_observation_id):raise AlertDiagnosticReadFailed()
handler._diagnostic=ReadAlertDiagnosticUseCase(FailingDiagnostic())
response=handler.handle(request,l.id)
assert response.status_code==200
body=response.content.decode()
assert 'PlayStation 5' in body and 'Não foi possível consultar o estado do alerta' in body
assert 'Tentar consultar novamente' in body and 'aba=defeitos' in body and 'pagina=1' in body
print('SVC01/02/03;DTO first_alert_state,next_action_at,valuation_revision,intent_reference;partial HTTP200 PASS')
""",
            )
        finally:
            resume_worker(group)

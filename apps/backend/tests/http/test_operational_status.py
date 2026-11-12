from tests.factories.runtime import FoundationInstance
from tests.integration.test_collection import shell
from tests.integration.test_operational_recovery import operational_instance as operational_instance


def test_status_versions_filters_resume_csrf_and_nonempty_catalog(
    operational_instance: FoundationInstance,
) -> None:
    shell(
        operational_instance,
        """
from uuid import uuid4
from django.test import Client
from django.utils.timezone import now
from garimpei.config.env import load_config
from garimpei.infra.repository.operations.progress_repository import PostgresOperationalRepository
from garimpei.infra.persistence.operations_models import OperationalUnit
from garimpei.main import build_backup_repository
client=Client(enforce_csrf_checks=True,HTTP_HOST='127.0.0.1')
response=client.get('/acompanhamento/');assert response.status_code==200
assert b'O caminho das oportunidades' in response.content
assert client.get('/configuracoes/').status_code==200
token=client.cookies['csrftoken'].value
status=client.get('/acompanhamento/estado/');assert status.status_code==200 and status['Cache-Control']=='no-store'
value=status.json(); assert value['counts']['with_photo']['available'] is True and value['counts']['stored']['value']>0
same=client.get('/acompanhamento/estado/',{'versao':value['snapshot_id']});assert same.status_code==200 and same.json()==value
assert client.get('/acompanhamento/estado/',{'interesse':'not-a-saved-interest'}).status_code==400
assert client.get('/acompanhamento/estado/',{'versao':str(uuid4())}).status_code==409
assert client.get('/acompanhamento/estado/',{'versao':'bad'}).status_code==400
store=PostgresOperationalRepository(load_config().environment_id,now)
for _ in range(3):store.failure('valuation','HTTP fixture',4,'valuation_publication_failed',now())
row=OperationalUnit.objects.get(scope='HTTP fixture')
route='/acompanhamento/etapas/valuation/retomar/'
assert client.post(route,{'unidade':str(row.id),'revisao':'4'}).status_code==403
row.refresh_from_db();assert row.failures==3
assert client.post(route,{'unidade':str(row.id),'revisao':'3','csrfmiddlewaretoken':token}).status_code==409
assert client.post(route,{'unidade':str(row.id),'revisao':'4','csrfmiddlewaretoken':token}).status_code==303
row.refresh_from_db();assert row.failures==0 and not row.suspended
assert client.post(route,{'unidade':'q'*36,'revisao':'4','csrfmiddlewaretoken':token}).status_code==400
r=build_backup_repository();identity=r.create();assert identity
request=str(uuid4());path=f'/acompanhamento/backups/{identity}/exportar/'
first=client.post(path,{'request_id':request,'csrfmiddlewaretoken':token});assert first.status_code==303
again=client.post(path,{'request_id':request,'csrfmiddlewaretoken':token});assert first['Location']==again['Location']
operation=first['Location'].split('operacao=')[1]
download=client.get(f'/acompanhamento/exportacoes/{operation}/arquivo/')
assert download.status_code==200 and 'attachment' in download['Content-Disposition'] and download['Cache-Control']=='no-store'
data=b''.join(download.streaming_content); assert data
assert client.get(f'/acompanhamento/exportacoes/{uuid4()}/arquivo/').status_code==404
catalog=client.get('/acompanhamento/backups/');assert catalog.status_code==200 and b'Exportar esta' in catalog.content
""",
    )


def test_configuration_read_failure_preserves_submitted_edit_and_active_state(
    operational_instance: FoundationInstance,
) -> None:
    shell(
        operational_instance,
        """
from unittest.mock import patch
from django.test import Client
from garimpei.domain.monitoring.errors import ConfigurationReadFailed
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
client=Client(enforce_csrf_checks=True,HTTP_HOST='127.0.0.1')
assert client.get('/configuracoes/').status_code==200
token=client.cookies['csrftoken'].value
before=list(MonitoringConfiguration.objects.values())
with patch('garimpei.infra.queries.monitoring.postgres_queries.PostgresMonitoringQueries.read_form',side_effect=ConfigurationReadFailed()):
 first=client.get('/acompanhamento/')
 assert first.status_code==503 and b'Prepare seu garimpo' not in first.content
 response=client.post('/configuracoes/',{'csrfmiddlewaretoken':token,'revision':'1','cep':'22222-222','shipping_estimate':'123,45','resale_fee_percent':'12,34','product_names[]':['Produto de entrada preservado']})
 assert response.status_code==503 and b'22222-222' in response.content and b'12,34' in response.content
 assert b'Produto de entrada preservado' in response.content and b'Gravado' not in response.content
assert list(MonitoringConfiguration.objects.values())==before
""",
    )

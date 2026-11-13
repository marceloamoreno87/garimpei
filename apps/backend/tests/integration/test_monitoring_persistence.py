from tests.factories.runtime import FoundationInstance


def run_case(instance: FoundationInstance, code: str) -> None:
    setup = """
from dataclasses import replace
from decimal import Decimal
from unittest.mock import patch
from django.db import DatabaseError, connection
from django.test import Client
from garimpei.main import build_monitoring_catalog, build_monitoring_handler, build_monitoring_queries, build_read_monitoring_configuration
from garimpei.domain.monitoring.errors import ConfigurationConflict, ConfigurationReadFailed, ConfigurationSaveFailed
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration as Row, MonitoringInterest
from garimpei.infra.gateway.monitoring.facebook_catalog import FacebookCategoryCatalog
from garimpei.infra.repository.monitoring.postgres_repository import PostgresMonitoringRepository
from garimpei.usecase.monitoring.save_step_usecase import StepInput
from tests.factories.monitoring import prepare_state, fail_after_save
client=Client(HTTP_HOST='127.0.0.1')
"""
    result = instance.shell(setup + code)
    assert result.returncode == 0, result.stdout + result.stderr


def test_real_database_draft_publication_idempotence_and_whole_edit(
    foundations: list[FoundationInstance],
) -> None:
    run_case(
        foundations[0],
        """
prepare_state('NOVO')
with connection.cursor() as cursor:
 cursor.execute('SELECT id FROM procrastinate_jobs')
 earlier_jobs=[row[0] for row in cursor.fetchall()]
assert not build_read_monitoring_configuration().execute().configured
assert client.get('/').headers['Location']=='/configuracao/regiao/'
assert client.get('/configuracao/interesses/').status_code==302
assert Row.objects.count()==0
r=client.post('/configuracao/regiao/',{'revision':'0','cep':'01001-000'})
assert r.status_code==303, r.content
draft=build_monitoring_queries().read_form()
assert draft.cep=='01001000' and draft.shipping_estimate is None
assert client.post('/configuracao/custos/',{'revision':'1','shipping_estimate':'25,50','resale_fee_percent':'12.50'}).status_code==303
assert not build_read_monitoring_configuration().execute().configured
assert client.get('/configuracoes/').status_code==302
category='479353692612078'
payload={'revision':'2','category_ids[]':[category,category],'product_names[]':['PlayStation 5',' playstation   5 ']}
r=client.post('/configuracao/concluir/',payload)
assert r.status_code==303,r.content
snapshot=build_read_monitoring_configuration().execute()
assert snapshot.configured and snapshot.category_ids==(category,) and snapshot.product_names==('PlayStation 5',)
assert snapshot.shipping_estimate==Decimal('25.50') and snapshot.resale_fee_percent==Decimal('12.50')
assert Row.objects.count()==1 and Row.objects.get().slot=='active' and MonitoringInterest.objects.count()==2
ids=list(MonitoringInterest.objects.values_list('id',flat=True))
assert client.post('/configuracao/concluir/',payload).status_code==303
assert build_read_monitoring_configuration().execute()==snapshot
assert list(MonitoringInterest.objects.values_list('id',flat=True))==ids
payload['product_names[]']=['Different']
assert client.post('/configuracao/concluir/',payload).status_code==409
edit={'revision':snapshot.revision,'cep':'02002000','shipping_estimate':'0','resale_fee_percent':'100','category_ids[]':[category],'product_names[]':['Notebook']}
assert client.post('/configuracoes/',edit).status_code==303
updated=build_read_monitoring_configuration().execute()
assert updated.revision==2 and updated.completed_at==snapshot.completed_at and updated.configuration_id==snapshot.configuration_id
assert updated.cep=='02002000' and updated.product_names==('Notebook',)
assert client.post('/configuracoes/',edit).status_code==303
assert build_read_monitoring_configuration().execute()==updated
edit['cep']='03003000'
conflict=client.post('/configuracoes/',edit)
assert conflict.status_code==409 and b'03003000' in conflict.content
assert build_read_monitoring_configuration().execute()==updated
assert client.get('/').headers['Location']=='/acompanhamento/'
assert client.get('/configuracao/regiao/').status_code==302
with connection.cursor() as cursor:
 cursor.execute("SELECT task_name FROM procrastinate_jobs WHERE NOT (id = ANY(%s)) AND task_name NOT IN ('garimpei.runtime_probe', 'garimpei.collect_listings')",(earlier_jobs,))
 assert cursor.fetchall()==[],'configuration publication enqueued an unrelated task'
""",
    )


def test_real_database_rollback_on_failure_and_read_error(
    foundations: list[FoundationInstance],
) -> None:
    run_case(
        foundations[0],
        """
prepare_state('RASCUNHO')
draft=build_monitoring_queries().read_form()
with patch.object(PostgresMonitoringRepository,'save',fail_after_save):
 r=client.post('/configuracao/concluir/',{'revision':draft.revision,'product_names[]':['Notebook']})
 assert r.status_code==503 and b'CONFIGURATION_SAVE_FAILED' in r.content and b'Notebook' in r.content
assert build_monitoring_queries().read_form()==draft
assert not build_read_monitoring_configuration().execute().configured
assert not Row.objects.filter(slot='active').exists()
with connection.cursor() as cursor:
 cursor.execute("SELECT count(*) FROM runtime_collectionstate WHERE configuration_id = %s", (draft.id,))
 assert cursor.fetchone()==(0,)
snapshot=prepare_state('ATIVA')
with patch.object(PostgresMonitoringRepository,'save',fail_after_save):
 r=client.post('/configuracoes/',{'revision':snapshot.revision,'cep':'02002000','shipping_estimate':'0','resale_fee_percent':'0','product_names[]':['Notebook']},HTTP_HX_REQUEST='true')
 assert r.status_code==503 and b'02002000' in r.content
assert build_read_monitoring_configuration().execute()==snapshot
with patch.object(PostgresMonitoringRepository,'find_current',side_effect=DatabaseError('controlled early failure')):
 r=client.post('/configuracoes/',{'revision':snapshot.revision,'cep':'02002000','shipping_estimate':'0','resale_fee_percent':'0','product_names[]':['Notebook']})
 assert r.status_code==503 and b'CONFIGURATION_SAVE_FAILED' in r.content and b'02002000' in r.content, 'early failure must preserve the submitted form'
with patch.object(PostgresMonitoringRepository,'find_by_slot',side_effect=DatabaseError('controlled')):
 try:
  build_read_monitoring_configuration().execute()
  raise AssertionError('read failure became absence')
 except ConfigurationReadFailed:
  pass
assert build_read_monitoring_configuration().execute()==snapshot
""",
    )


def test_real_http_validation_csrf_escaping_catalog_and_last_interest(
    foundations: list[FoundationInstance],
) -> None:
    run_case(
        foundations[0],
        """
prepare_state('NOVO')
for path in ['/configuracao/regiao/','/configuracao/custos/','/configuracoes/']:
 assert client.put(path).status_code==405
assert client.get('/configuracao/unknown/').status_code==404
assert client.get('/configuracao/concluir/').status_code==405
assert Client(enforce_csrf_checks=True,HTTP_HOST='127.0.0.1').post('/configuracao/concluir/',{}).status_code==403
assert not build_read_monitoring_configuration().execute().configured
for value in ['', '0100100','０１００１０００','01001 000']:
 r=client.post('/configuracao/regiao/',{'revision':'0','cep':value})
 assert r.status_code==422 and b'INVALID_CONFIGURATION' in r.content
assert Row.objects.count()==0
assert client.post('/configuracao/regiao/',{'revision':'0','cep':'01001000'}).status_code==303
for value in ['-1','1000000','NaN','Infinity','1e2','1,005','1.000,00']:
 r=client.post('/configuracao/custos/',{'revision':'1','shipping_estimate':value,'resale_fee_percent':'0'})
 assert r.status_code==422,r.content
 assert build_monitoring_queries().read_form().shipping_estimate is None
for value in ['-1','100.01','10%','']:
 assert client.post('/configuracao/custos/',{'revision':'1','shipping_estimate':'0','resale_fee_percent':value}).status_code==422
assert client.post('/configuracao/custos/',{'revision':'1','shipping_estimate':'999999.99','resale_fee_percent':'100'}).status_code==303
costs=build_monitoring_queries().read_form()
assert costs.shipping_estimate==Decimal('999999.99') and costs.resale_fee_percent==Decimal('100.00')
assert client.post('/configuracao/custos/',{'revision':costs.revision,'shipping_estimate':'0','resale_fee_percent':'0'}).status_code==303
costs=build_monitoring_queries().read_form()
assert costs.shipping_estimate==Decimal('0.00') and costs.resale_fee_percent==Decimal('0.00')
assert client.post('/configuracao/custos/',{'revision':costs.revision,'resale_fee_percent':'0'}).status_code==303
costs=build_monitoring_queries().read_form()
assert costs.shipping_estimate is None
for name in ['', '   ', 'a'*121]:
 assert client.post('/configuracao/interesses/',{'revision':costs.revision,'product_names[]':[name]}).status_code==422
r=client.post('/configuracao/interesses/',{'revision':costs.revision,'product_names[]':['<script>alert(1)</script>','PlayStation 5',' playstation   5 ']})
assert r.status_code==303
r=client.get('/configuracao/interesses/')
assert b'&lt;script&gt;' in r.content and b'<script>alert(1)</script>' not in r.content
assert len(build_monitoring_queries().read_form().interests)==2
draft=build_monitoring_queries().read_form()
csrf=Client(enforce_csrf_checks=True,HTTP_HOST='127.0.0.1')
assert csrf.get('/configuracao/interesses/').status_code==200
assert csrf.post('/configuracao/concluir/',{'revision':draft.revision,'product_names[]':['PlayStation 5']}).status_code==403
assert csrf.get('/acompanhamento/').headers['Location']=='/configuracao/interesses/'
assert build_monitoring_queries().read_form()==draft
for payload in [{},{'category_ids[]':['unknown']}]:
 r=client.post('/configuracao/concluir/',dict(payload,revision=draft.revision))
 assert r.status_code==422
 assert not build_read_monitoring_configuration().execute().configured
catalog=build_monitoring_catalog().load()
group=replace(catalog.entries[0],selectable=False)
with patch.object(FacebookCategoryCatalog,'load',return_value=replace(catalog,entries=(group,*catalog.entries[1:]))):
 r=client.post('/configuracao/concluir/',{'revision':draft.revision,'category_ids[]':[group.id]})
 assert r.status_code==422
assert not build_read_monitoring_configuration().execute().configured
snapshot=prepare_state('ATIVA')
r=client.post('/configuracoes/',{'revision':snapshot.revision,'cep':'02002000','shipping_estimate':'0','resale_fee_percent':'0'})
assert r.status_code==422
assert build_read_monitoring_configuration().execute()==snapshot
""",
    )


def test_category_only_product_only_and_both_are_independent(
    foundations: list[FoundationInstance],
) -> None:
    run_case(
        foundations[0],
        """
for categories, products in [(['479353692612078'],[]),([],['PlayStation 5']),(['479353692612078'],['PlayStation 5'])]:
 prepare_state('RASCUNHO')
 draft=build_monitoring_queries().read_form()
 response=client.post('/configuracao/concluir/',{'revision':draft.revision,'category_ids[]':categories,'product_names[]':products})
 assert response.status_code==303,response.content
 snapshot=build_read_monitoring_configuration().execute()
 assert snapshot.category_ids==tuple(categories) and snapshot.product_names==tuple(products)
""",
    )


def test_concurrent_creations_and_edits_cannot_overwrite_a_newer_version(
    foundations: list[FoundationInstance],
) -> None:
    run_case(
        foundations[0],
        """
from concurrent.futures import ThreadPoolExecutor
from django.db import connections
prepare_state('NOVO')
def region(cep):
 try:
  build_monitoring_handler()._save_step.execute(StepInput('regiao',0,cep=cep))
  return 'saved'
 except ConfigurationConflict:
  return 'conflict'
 finally:
  connections.close_all()
with ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(region,['01001000','02002000']))
assert sorted(results)==['conflict','saved'],results
assert Row.objects.count()==1 and Row.objects.get().revision==1
prepare_state('RASCUNHO')
draft=build_monitoring_queries().read_form()
assert client.post('/configuracao/custos/',{'revision':draft.revision,'shipping_estimate':'0','resale_fee_percent':'0'}).status_code==303
assert client.post('/configuracao/concluir/',{'revision':draft.revision,'product_names[]':['PlayStation 5']}).status_code==409
assert not build_read_monitoring_configuration().execute().configured
snapshot=prepare_state('ATIVA')
def update(cep):
 try:
  build_monitoring_handler()._update.execute(StepInput('editar',snapshot.revision,cep=cep,shipping_estimate='0',resale_fee_percent='0',product_names=('Notebook',)))
  return 'saved'
 except ConfigurationConflict:
  return 'conflict'
 finally:
  connections.close_all()
with ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(update,['02002000','03003000']))
assert sorted(results)==['conflict','saved'],results
assert build_read_monitoring_configuration().execute().revision==2
""",
    )


def test_confirmed_reader_never_observes_partial_publication(
    foundations: list[FoundationInstance],
) -> None:
    run_case(
        foundations[0],
        """
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import Event
from django.db import connections
old=prepare_state('ATIVA')
ready,release,reading=Event(),Event(),Event()
save=PostgresMonitoringRepository.save
def hold_commit(repository,state):
 save(repository,state)
 ready.set()
 assert release.wait(3)
def write():
 try:
  build_monitoring_handler()._update.execute(StepInput('editar',old.revision,cep='02002000',shipping_estimate='0',resale_fee_percent='100',product_names=('Notebook',)))
 finally:
  connections.close_all()
def read():
 reading.set()
 try:
  return build_read_monitoring_configuration().execute()
 finally:
  connections.close_all()
with patch.object(PostgresMonitoringRepository,'save',hold_commit), ThreadPoolExecutor(max_workers=2) as pool:
 writer=pool.submit(write)
 try:
  assert ready.wait(2)
  reader=pool.submit(read)
  assert reading.wait(1)
  try:
   assert reader.result(timeout=.15)==old
  except TimeoutError:
   pass  # Row lock can delay reading until the entire new version commits.
 finally:
  release.set()
 writer.result(timeout=3)
 during=reader.result(timeout=3)
new=build_read_monitoring_configuration().execute()
assert new.revision==2 and new.completed_at==old.completed_at
assert new.cep=='02002000' and new.shipping_estimate==0 and new.resale_fee_percent==100
assert new.category_ids==() and new.product_names==('Notebook',)
assert during in (old,new)
""",
    )

from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest

from tests.factories.runtime import (
    FoundationInstance,
    pause_worker,
    prepare_instance,
    resume_worker,
)
from tests.integration.test_collection import command, configure, shell


@pytest.fixture(scope="module")
def research_instance(tmp_path_factory: pytest.TempPathFactory) -> Iterator[FoundationInstance]:
    root = Path(__file__).resolve().parents[4]
    directory = tmp_path_factory.mktemp("f18-research")
    instance = prepare_instance(root, directory, "f18_research_" + uuid4().hex[:8])
    with instance.private_file.open("a") as file:
        file.write("GARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ALERTS_ENABLED=false\n")
    command(instance, "./scripts/init.sh", "--disposable")
    worker = pause_worker(instance)
    try:
        configure(instance, active=False)
        shell(
            instance,
            """
from garimpei.main import build_monitoring_handler,build_monitoring_queries
from garimpei.usecase.monitoring.save_step_usecase import StepInput
from tests.factories.listing import CATEGORIES
form=build_monitoring_queries().read_form()
build_monitoring_handler()._complete.execute(StepInput('interesses',form.revision,category_ids=CATEGORIES,product_names=()))
""",
        )
        yield instance
    finally:
        resume_worker(worker)
        command(instance, "./scripts/stop.sh", "--clean")


PREPARE = """
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4
from decimal import Decimal
from garimpei.main import build_identity_repository,build_read_monitoring_configuration,_collection_store
from garimpei.config.env import load_listing_settings
from garimpei.domain.valuation.identity_ports import IdentityEdit
from garimpei.domain.valuation.identity_errors import IdentityConflict
from garimpei.infra.persistence.identity_models import IdentityProgress,ProductIdentification,ManualIdentityRevision
from garimpei.infra.persistence.listing_models import Listing,ListingEvent,ListingInterestMatch,ListingObservation
from garimpei.infra.persistence.research_models import ComparableInvestigation,InvestigationTarget,ResearchCandidateDecision,ResearchQuery
from garimpei.infra.repository.valuation.research_repository import PostgresComparableResearchRepository
from garimpei.usecase.valuation.run_research_usecase import RunComparableResearchUseCase
from tests.factories.comparable_research import NOW,KEY,TITLE,ControlledResearchSource,controlled_limits,seed_case,candidate
clock=[NOW]
from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository
publication=PostgresCollectionRepository(build_read_monitoring_configuration(),lambda:clock[0],lambda *_:0,40)
repo=PostgresComparableResearchRepository(build_read_monitoring_configuration(),lambda:clock[0],controlled_limits(),publication)
manual_values=tuple(sorted(dict(family='playstation5',model='ps5',generation='slim',edition='digital',capacity='825gb').items()))
"""


def test_manual_identity_history_cas_and_new_contradiction(
    research_instance: FoundationInstance,
) -> None:
    shell(
        research_instance,
        PREPARE
        + """
listing=seed_case('18101',title='PlayStation 5 Slim Digital')
store=build_identity_repository()
v=store.read(listing.id);assert v.result.state=='missing_attribute' and 'capacity' in v.result.missing_attributes
before=ListingEvent.objects.count()
command=IdentityEdit(listing.id,1,0,'save',manual_values)
v=store.save(command);assert v.result.state=='identified' and v.result.product_key==KEY
assert all(a.origin=='manual' and a.quote is None and a.recorded_at for a in v.result.attributes)
try: store.save(command)
except IdentityConflict: pass
else: raise AssertionError('CAS accepted stale input')
seed_case('18101',title='PlayStation 5 Slim Digital')
v=store.read(listing.id);assert v.result.state=='identified' and v.result.manual_revision==1
seed_case('18101',title='PlayStation 5 Slim Digital 1TB')
v=store.read(listing.id);assert v.result.state=='conflicting_identity' and v.result.product_key is None
assert any(c.name=='capacity' and c.observed_value=='1tb' for c in v.result.conflicts)
v=store.save(IdentityEdit(listing.id,3,1,'resolve',(), 'keep_manual'))
assert v.result.state=='identified' and v.result.manual_revision==2
seed_case('18101',title='PlayStation 5 Slim Digital 2TB')
assert store.read(listing.id).result.state=='conflicting_identity'
assert ManualIdentityRevision.objects.filter(listing=listing).count()==2
assert ProductIdentification.objects.filter(listing=listing).count()==2
assert ListingEvent.objects.count()==before
""",
    )


def test_shared_research_completes_five_references_without_fake_matches(
    research_instance: FoundationInstance,
) -> None:
    shell(
        research_instance,
        PREPARE
        + """
a=seed_case('18201');b=seed_case('18202')
repo.reconcile()
row=ComparableInvestigation.objects.get(product_key=KEY)
assert row.targets.filter(active=True).count()==2
source=ControlledResearchSource()
runner=RunComparableResearchUseCase(repo,source,lambda:0.0)
runner.execute()
row.refresh_from_db();assert row.details==2 and row.state=='waiting_evidence' and row.pages==1
# A new repository instance resumes the preserved buffer and the exact shared investigation.
restarted=PostgresComparableResearchRepository(build_read_monitoring_configuration(),lambda:clock[0],controlled_limits(),publication)
RunComparableResearchUseCase(restarted,source,lambda:0.0).execute()
RunComparableResearchUseCase(restarted,source,lambda:0.0).execute()
row.refresh_from_db();assert row.state=='sufficient',(row.state,row.reason,row.details)
assert row.pages==1 and row.details==5 and row.attempts==3
assert [call for call in source.calls if call[0]=='search']==[('search',None)]
references=Listing.objects.filter(origin='reference')
assert references.count()==5 and not ListingInterestMatch.objects.filter(observation__listing__in=references).exists()
assert not ListingEvent.objects.filter(listing__in=references).exists()
assert ResearchCandidateDecision.objects.filter(query__investigation=row,decision='accepted').count()==10
from garimpei.domain.valuation.policy import estimate
from garimpei.infra.repository.valuation.postgres_repository import _listing
from garimpei.infra.repository.valuation.identity_mapper import identify_row
from garimpei.domain.valuation.profit import ProfitInput,compose_profit
from garimpei.main import build_read_listing
values=tuple(_listing(l,identify_row(l,getattr(l,'identity_progress',None))) for l in Listing.objects.select_related('latest','identity_progress__manual__observation').filter(latest__isnull=False))
resale=estimate(_listing(a),values,NOW)
assert resale.price==Decimal('2300') and resale.after>=5
assert len({(c.source,c.external_id) for c in resale.comparables})==len(resale.comparables)
""",
    )


def test_public_identity_endpoint_status_and_bound_error(
    research_instance: FoundationInstance,
) -> None:
    shell(
        research_instance,
        PREPARE
        + """
from django.test import Client
from django.db import DatabaseError
from unittest.mock import patch
listing=seed_case('18301',title='PlayStation 5 Slim Digital')
client=Client(enforce_csrf_checks=True,HTTP_HOST="127.0.0.1")
path=f'/ofertas/{listing.id}/identidade/'
values=dict(action='save',observed_revision='1',manual_revision='0',**dict(manual_values))
assert client.post(path,values).status_code==403
# Render an existing GET page to obtain the CSRF cookie; no source/network call.
response=client.get('/configuracoes/')
token=client.cookies['csrftoken'].value
values['csrfmiddlewaretoken']=token
assert client.post(path,values|{'unexpected':'x'}).status_code==400
assert client.post(path,values|{'observed_revision':'bad'}).status_code==400
assert client.post(path,values|{'capacity':'999gb'}).status_code==422
missing=f'/ofertas/{uuid4()}/identidade/'
assert client.post(missing,values).status_code==404
assert client.post(path,values).status_code==303
assert client.post(path,values).status_code==409
values['manual_revision']='1'
with patch('garimpei.infra.repository.valuation.identity_repository.PostgresIdentityRepository.save',side_effect=DatabaseError('controlled')):
 response=client.post(path,values)
 assert response.status_code==503
 assert b'825gb' in response.content
assert ManualIdentityRevision.objects.filter(listing=listing).count()==1
""",
    )


def test_retry_after_is_persisted_and_empty_is_a_distinct_exhaustion(
    research_instance: FoundationInstance,
) -> None:
    shell(
        research_instance,
        PREPARE
        + """
from garimpei.domain.listing.ports import SourceFailure
l=seed_case('18401',title='iPhone 12 128GB')
repo.reconcile()
row=ComparableInvestigation.objects.get(product_key='apple:iphone12:standard:128gb')
source=ControlledResearchSource(pages=[],failure=SourceFailure('source_rate_limit',120))
runner=RunComparableResearchUseCase(repo,source,lambda:0.0)
runner.execute();row.refresh_from_db()
assert row.state=='waiting_retry' and row.reason=='source_rate_limit' and row.attempts==1
assert row.next_attempt_at==NOW+timedelta(seconds=120)
runner.execute();assert len(source.calls)==1,'Retry-After was ignored'
clock[0]+=timedelta(seconds=120)
source.failure=None
runner.execute();row.refresh_from_db()
assert row.state=='exhausted' and row.reason=='no_results'
assert row.pages==1 and row.details==0
""",
    )


def test_unverified_geography_never_publishes_a_local_sample(
    research_instance: FoundationInstance,
) -> None:
    shell(
        research_instance,
        PREPARE
        + """
l=seed_case('18501',title='iPhone 13 128GB')
repo.reconcile();row=ComparableInvestigation.objects.get(product_key='apple:iphone13:standard:128gb')
source=ControlledResearchSource(pages=[(candidate('18502',title='iPhone 13 128GB'),)],verified=False)
count=ListingObservation.objects.count()
RunComparableResearchUseCase(repo,source,lambda:0.0).execute()
row.refresh_from_db();assert row.state=='limited' and row.reason=='search_geography_unverified'
assert ListingObservation.objects.count()==count and not Listing.objects.filter(external_id='18502').exists()
query=row.queries.get();assert query.state=='partial' and query.observed['verified'] is False
""",
    )


def test_late_response_cannot_publish_after_conflicting_manual_revision(
    research_instance: FoundationInstance,
) -> None:
    shell(
        research_instance,
        PREPARE
        + """
from garimpei.domain.listing.ports import SupersededAttempt
l=seed_case('18601',title='iPhone 14 128GB')
repo.reconcile();work=repo.claim();assert work is not None
assert work.product_key=='apple:iphone14:standard:128gb'
# Source I/O has begun and owns no publication transaction. A manual edit commits independently.
store=build_identity_repository()
store.save(IdentityEdit(l.id,1,0,'save',tuple(sorted(dict(family='iphone',model='14',edition='standard',capacity='256gb').items()))))
assert store.read(l.id).result.state=='conflicting_identity'
page=ControlledResearchSource(pages=[(candidate('18602',title='iPhone 14 128GB'),)]).search(work.scope,work.query,None)
try: repo.page(work,page)
except SupersededAttempt: pass
else: raise AssertionError('Stale source result published after identity conflict')
assert not Listing.objects.filter(external_id='18602').exists()
assert not ResearchQuery.objects.filter(investigation_id=work.id).exists()
""",
    )


def test_recovered_lease_does_not_reset_attempt_budget(
    research_instance: FoundationInstance,
) -> None:
    shell(
        research_instance,
        PREPARE
        + """
from garimpei.domain.listing.ports import SupersededAttempt
l=seed_case('18701',title='iPhone 15 128GB')
repo.reconcile()
# The stale previous target is retired before the next eligible investigation.
clock[0]=NOW+timedelta(seconds=41)
old=repo.claim()
if old is None: old=repo.claim()
assert old is not None and old.product_key=='apple:iphone15:standard:128gb'
clock[0]+=timedelta(seconds=41)
new=repo.claim();assert new is not None and new.id==old.id and new.generation>old.generation,(old,new,list(ComparableInvestigation.objects.values('product_key','state','reason','next_attempt_at','lease_until')))
page=ControlledResearchSource(pages=[]).search(new.scope,new.query,None)
try: repo.page(old,page)
except SupersededAttempt: pass
else: raise AssertionError('Old lease committed')
repo.page(new,page)
row=ComparableInvestigation.objects.get(id=new.id)
assert row.attempts==2 and row.state=='exhausted'
""",
    )

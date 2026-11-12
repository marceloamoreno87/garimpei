from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.factories.listing import serve
from tests.factories.navigation import NavigationSourceFake, prepare_navigation_instance
from tests.factories.runtime import FoundationInstance, pause_worker, resume_worker


@pytest.fixture(scope="module")
def navigation_source() -> NavigationSourceFake:
    return NavigationSourceFake()


@pytest.fixture(scope="module")
def navigation_instance(
    tmp_path_factory: pytest.TempPathFactory, navigation_source: NavigationSourceFake
) -> Iterator[FoundationInstance]:
    root = Path(__file__).resolve().parents[4]
    with serve(navigation_source) as url:
        instance = prepare_navigation_instance(root, tmp_path_factory.mktemp("navigation-db"), url)
        started = instance.command("./scripts/init.sh", "--disposable")
        assert started.returncode == 0, started.stdout + started.stderr
        group = pause_worker(instance)
        try:
            yield instance
        finally:
            with instance.database() as database:
                database.execute(
                    "DELETE FROM procrastinate_jobs WHERE status='todo' AND task_name IN ('garimpei.collect_listings','garimpei.navigation_suggestions')"
                )
            resume_worker(group)
            stopped = instance.command("./scripts/stop.sh", "--clean")
            assert stopped.returncode == 0, stopped.stdout + stopped.stderr


BOOTSTRAP = """
from datetime import timedelta
from dataclasses import replace
from uuid import uuid4
from django.db import connection, transaction
from django.utils.timezone import now
from garimpei.main import (build_monitoring_handler, build_monitoring_queries, build_read_monitoring_configuration,
    _navigation_collection, _effective_listing_settings, _listing_policy, build_navigation_repository,
    build_navigation_catalog, build_navigation_queries, reconcile_navigation)
from garimpei.config.env import load_navigation_policy
from garimpei.domain.listing.ports import Attempt, Page, SourceFailure, SupersededAttempt
from garimpei.domain.listing.scope import Scope
from garimpei.domain.listing.listing import Candidate, Evidence
from garimpei.domain.navigation.ports import StaleNavigation
from garimpei.infra.persistence.navigation_models import NavigationWork, NavigationCheckpoint, NavigationUnitReceipt, NicheSuggestion, SuggestionEvidence
from garimpei.infra.persistence.listing_models import CollectionCycle, CollectionState, CollectionCandidate, Listing, ListingObservation, ListingEvent
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
from garimpei.infra.gateway.listing.fixture_source import FixtureSource
from tests.factories.monitoring import prepare_state
from garimpei.usecase.monitoring.save_step_usecase import StepInput
from unittest.mock import patch
with connection.cursor() as cursor:
    cursor.execute('TRUNCATE runtime_navigationunitreceipt, runtime_navigationcheckpoint, runtime_navigationwork, runtime_suggestionevidence, runtime_nichesuggestion, runtime_listing, runtime_collectionstate, persistence_monitoringconfiguration CASCADE')
prepare_state('RASCUNHO')
handler = build_monitoring_handler()
handler._complete.execute(StepInput('interesses', build_monitoring_queries().read_form().revision, category_ids=(), product_names=('PlayStation 5 Slim', 'iPhone 13 128 GB')))
MonitoringConfiguration.objects.filter(slot="active").update(revision=2)
settings = _effective_listing_settings()
collection = _navigation_collection(settings)
collection.reconcile(_listing_policy(settings))
state = CollectionState.objects.get()
attempt = Attempt(state.current_id, state.generation)
work = collection.begin(attempt)
scope = build_navigation_catalog().decorate_scope(work.scope)
nav = build_navigation_repository(settings)
nav.prepare(attempt, scope)
source = FixtureSource(settings.fixture_url, settings.timeout)
"""


def shell(instance: FoundationInstance, code: str) -> str:
    result = instance.shell(code)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_checkpoint_survives_restart_and_atomic_rollback(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
unit = nav.claim(attempt, scope, pages=True, details=False)
page = source.search(scope, unit.search, unit.cursor)
with patch.object(NavigationUnitReceipt.objects, 'create', side_effect=RuntimeError('before_commit')):
    try: nav.page(attempt, unit, page)
    except RuntimeError: pass
    else: raise AssertionError('fault not exercised')
assert NavigationCheckpoint.objects.get(work_id=unit.turn.id).pages == 0
assert not CollectionCandidate.objects.exists()
unit = nav.claim(attempt, scope, pages=True, details=False)
nav.page(attempt, unit, source.search(scope, unit.search, unit.cursor))
assert NavigationCheckpoint.objects.get(work_id=unit.turn.id).pages == 1
assert NavigationUnitReceipt.objects.count() == 1
assert list(NavigationUnitReceipt.objects.values_list("turn_order","consumed_pages","consumed_details")) == [(unit.turn.last_turn,1,0)]
""",
    )
    # A new process rehydrates persisted context; no in-memory cursor survives.
    shell(
        navigation_instance,
        """
from garimpei.infra.persistence.navigation_models import NavigationCheckpoint, NavigationUnitReceipt
assert NavigationCheckpoint.objects.filter(pages=1).count() == 1
assert NavigationUnitReceipt.objects.count() == 1
print('restart_checkpoint_confirmed')
""",
    )


def test_incremental_publication_and_alias_identity(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
unit = nav.claim(attempt, scope, pages=True, details=False)
nav.page(attempt, unit, source.search(scope, unit.search, None))
detail = nav.claim(attempt, scope, pages=False, details=True)
assert detail and detail.target
candidate = source.detail(scope, detail.target.external_id)
with patch.object(NavigationUnitReceipt.objects, 'create', side_effect=RuntimeError('before_detail_commit')):
    try: nav.detail(attempt, detail, candidate)
    except RuntimeError: pass
    else: raise AssertionError('fault not exercised')
assert not Listing.objects.exists()
# One publication commits before discovery is exhausted.
nav.detail(attempt, detail, candidate)
assert ListingObservation.objects.count() == 1
receipt=NavigationUnitReceipt.objects.get(consumed_details=1)
assert list(receipt.observation_ids)==[str(ListingObservation.objects.get().id)]
assert NavigationWork.objects.filter(front='discovery', phase='complete').count() < 2
try: nav.detail(attempt, detail, candidate)
except SupersededAttempt: pass
assert ListingObservation.objects.count() == 1
assert not Listing.objects.filter(external_id='1306').exists()
assert Listing.objects.get().external_id in {'1301','1302'}
""",
    )


def test_fair_turns_and_stale_generation_rejected(navigation_instance: FoundationInstance) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
# Seed one pending target for each interest through the real source/public store.
for _ in range(2):
    unit = nav.claim(attempt, scope, pages=True, details=False)
    nav.page(attempt, unit, source.search(scope, unit.search, unit.cursor))
NavigationWork.objects.all().update(last_turn=0)
seen=[]
for _ in range(4):
    unit=nav.claim(attempt, scope, pages=True, details=True)
    assert unit
    seen.append((unit.turn.interest, unit.turn.front))
assert len(set(seen)) == 4, seen
old = unit
unit = nav.claim(attempt, scope, pages=True, details=True)
NavigationWork.objects.filter(id=old.turn.id).update(generation=old.generation+10)
try: nav.page(attempt, old, Page((),None))
except SupersededAttempt: pass
else: raise AssertionError('stale generation accepted')
assert NavigationUnitReceipt.objects.count()==2
""",
    )


def test_scope_revision_invalidates_old_results(navigation_instance: FoundationInstance) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
unit = nav.claim(attempt, scope, pages=True, details=False)
MonitoringConfiguration.objects.filter(slot='active').update(revision=scope.revision+1)
try: nav.page(attempt, unit, Page((), None))
except SupersededAttempt: pass
else: raise AssertionError('stale revision published')
assert not Listing.objects.exists()
# Same scope with a newer revision requires a new cycle (cost-only change).
collection.reconcile(_listing_policy(settings))
state.refresh_from_db()
assert state.current_id != attempt.cycle_id, 'cost-only revision kept stale cycle'
assert state.monitoring_started_at is not None
""",
    )


def test_cursor_repeat_wrong_context_and_limits_are_partial(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
unit=nav.claim(attempt, scope, pages=True, details=False)
nav.page(attempt,unit,Page((), 'same'))
unit=nav.claim(attempt, scope, pages=True, details=False)
# Whichever interest is due, explicitly fail verification rather than confirm emptiness.
nav.page(attempt,unit,Page((),None,diagnostic='wrong_search_query'))
assert NavigationWork.objects.get(id=unit.turn.id).phase=='partial'
assert NavigationCheckpoint.objects.get(work_id=unit.turn.id).pages==0
remaining = NavigationWork.objects.filter(front='discovery').exclude(id=unit.turn.id).get()
checkpoint=NavigationCheckpoint.objects.get(work=remaining)
checkpoint.pages=99;checkpoint.save()
unit=nav.claim(attempt,scope,pages=True,details=False)
nav.page(attempt,unit,Page((), 'next'))
assert NavigationWork.objects.get(id=unit.turn.id).reason=='window_limit'
""",
    )


def test_profile_challenge_cannot_be_resumed(navigation_instance: FoundationInstance) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
unit=nav.claim(attempt,scope,pages=True,details=False)
nav.failed(attempt,unit,SourceFailure('access_denied',access=True))
assert CollectionState.objects.get().access_suspended
try: nav.resume(unit.turn.id,scope.revision)
except StaleNavigation: pass
else: raise AssertionError('resume bypassed F11 access')
assert NavigationWork.objects.exclude(phase='suspended').count()==0
""",
    )


def test_research_boundary_idempotent_and_restrictive(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from garimpei.usecase.navigation.request_research_usecase import RequestResearchUseCase
research=RequestResearchUseCase(nav)
request=uuid4();interest=scope.searches[0]
identity=research.execute(request,scope.revision,interest.key,interest.term,scope.key,'attributes')
assert research.execute(request,scope.revision,interest.key,interest.term,scope.key,'attributes')==identity
for term,revision,constraints in [('free electronics',scope.revision,scope.key),(interest.term,scope.revision-1,scope.key),(interest.term,scope.revision,'arbitrary')]:
    try: research.execute(uuid4(),revision,interest.key,term,constraints,'attributes')
    except StaleNavigation: pass
    else: raise AssertionError('unjustified research accepted')
assert len(build_read_monitoring_configuration().execute().product_names)==2
""",
    )


def test_suggestions_isolated_persistent_budget_and_tick_backlog(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from garimpei.infra.repository.navigation.suggestion_repository import PostgresSuggestionRepository
from garimpei.usecase.navigation.run_suggestions_usecase import RunSuggestionsUseCase
from time import monotonic
policy=load_navigation_policy()
store=PostgresSuggestionRepository(build_read_monitoring_configuration(),build_navigation_catalog(),policy,now,settings.timeout,settings.cadence_ms/1000)
assert store.claim() is None # active work always wins
CollectionCycle.objects.filter(id=attempt.cycle_id).update(finished_at=now())
CollectionState.objects.update(next_attempt_at=now()+timedelta(seconds=60))
runner=RunSuggestionsUseCase(store,source,policy,monotonic,settings.timeout,settings.cadence_ms/1000)
runner.execute()
assert NicheSuggestion.objects.filter(state='supported').count()==1
assert SuggestionEvidence.objects.get().external_id=='1304'
assert not Listing.objects.exists() and not ListingEvent.objects.exists()
assert len(build_read_monitoring_configuration().execute().product_names)==2
# Restart constructing a fresh store cannot replenish the persistent 300s quota.
store=PostgresSuggestionRepository(build_read_monitoring_configuration(),build_navigation_catalog(),policy,now,settings.timeout,settings.cadence_ms/1000)
assert store.claim() is None
reconcile_navigation();reconcile_navigation()
with connection.cursor() as cursor:
    cursor.execute("SELECT count(*) FROM procrastinate_jobs WHERE task_name='garimpei.navigation_suggestions' AND status IN ('todo','doing')")
    assert cursor.fetchone()[0] <= 1
""",
    )


def test_suggestion_rate_limit_survives_collection_reconcile(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from garimpei.infra.repository.navigation.suggestion_repository import PostgresSuggestionRepository
CollectionCycle.objects.filter(id=attempt.cycle_id).update(finished_at=now(),published_count=1)
CollectionState.objects.update(next_attempt_at=now()+timedelta(seconds=60))
store=PostgresSuggestionRepository(build_read_monitoring_configuration(),build_navigation_catalog(),load_navigation_policy(),now,20,1.2)
unit=store.claim();assert unit
store.failed(unit,SourceFailure('source_rate_limit',300))
state.refresh_from_db();deadline=state.next_attempt_at
collection.reconcile(_listing_policy(settings))
state.refresh_from_db()
assert state.next_attempt_at >= deadline, 'reconcile shortened mandatory source wait'
""",
    )


def test_page_buffer_preserves_excess_without_exceeding_500(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from garimpei.domain.listing.listing import Match
query=next(q for q in scope.searches if q.term=='PlayStation 5 Slim')
old=tuple(Candidate(str(5000+i),Evidence(title='PS5 Slim'), 'card',(query.interest,)) for i in range(499))
collection.stage(attempt,query.key,old)
unit=nav.claim(attempt,scope,pages=True,details=False)
# Pick the PS5 discovery explicitly, keeping the other interest out of this cap test.
if unit.query.key!=query.key:
    NavigationWork.objects.filter(id=unit.turn.id).update(phase='complete')
    unit=nav.claim(attempt,scope,pages=True,details=False)
new=tuple(Candidate(str(6000+i),Evidence(title='PS5 Slim'),'card',(query.interest,)) for i in range(200))
nav.page(attempt,unit,Page(new,'next'))
assert len([t for t in collection.detail_targets(attempt) if query.interest in t.matches])<=500
checkpoint=NavigationCheckpoint.objects.get(work_id=unit.turn.id)
assert len(checkpoint.buffered_candidates)==199
# Free two slots through confirmed details; a new repository drains buffered data.
for _ in range(2):
    detail=nav.claim(attempt,scope,pages=False,details=True)
    nav.detail(attempt,detail,Candidate(detail.target.external_id,Evidence(title='PS5 Slim'),'detail'))
nav=build_navigation_repository(settings)
nav.claim(attempt,scope,pages=False,details=True)
checkpoint.refresh_from_db()
assert len(checkpoint.buffered_candidates)==197
assert checkpoint.pages==1
""",
    )


def test_three_detail_failures_pause_attempt_and_queued_task_cannot_bypass(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
unit=nav.claim(attempt,scope,pages=2,details=False)
nav.page(attempt,unit,source.search(scope,unit.search,None))
collection.stage(attempt,unit.query.key,tuple(Candidate(str(7100+i),Evidence(title=unit.query.term),'card',(unit.query.interest,)) for i in range(3)))
for failure in range(3):
    NavigationWork.objects.all().update(next_attempt_at=None)
    detail=nav.claim(attempt,scope,pages=0,details=True)
    assert detail
    nav.failed(attempt,detail,SourceFailure('source_http_503'))
state.refresh_from_db()
assert state.source_not_before is None
assert NavigationWork.objects.get(id=detail.turn.id).phase=='partial'
NavigationWork.objects.filter(front='discovery').update(phase='pending',next_attempt_at=None)
unit=nav.claim(attempt,scope,pages=2,details=False)
nav.failed(attempt,unit,SourceFailure('source_rate_limit',300))
state.refresh_from_db();assert state.source_not_before and state.source_not_before>now()
cycle=CollectionCycle.objects.get(id=attempt.cycle_id)
assert cycle.results['source_health']['reason']=='detail_failures_pause'
from garimpei.usecase.navigation.run_slice_usecase import RunSliceUseCase
from unittest.mock import Mock
fake=Mock()
runner=RunSliceUseCase(collection,nav,fake,fake,build_navigation_catalog(),load_navigation_policy(),lambda:0.0,20,1.2)
runner.execute(attempt)
assert fake.search.call_count==0 and fake.detail.call_count==0
""",
    )


def test_research_shares_fairness_budgets_and_rejects_cycle_old_revision(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from garimpei.usecase.navigation.request_research_usecase import RequestResearchUseCase
query=next(q for q in scope.searches if q.term=='PlayStation 5 Slim')
collection.stage(attempt,query.key,(Candidate('1301',Evidence(title='PS5 Slim'),'card',(query.interest,)),))
NavigationWork.objects.exclude(origin_interest=query.key).update(phase='complete')
research=RequestResearchUseCase(nav)
research.execute(uuid4(),scope.revision,query.key,'PS5 Slim',scope.key,'attributes')
research.execute(uuid4(),scope.revision,query.key,'PS5 Pro',scope.key,'comparables')
first=nav.claim(attempt,scope,pages=2,details=True)
second=nav.claim(attempt,scope,pages=2,details=True)
assert {first.turn.front,second.turn.front}=={'discovery','investigation'}
NavigationCheckpoint.objects.filter(work__cycle_id=attempt.cycle_id,work__origin_interest=query.key,work__front='discovery').update(pages=100)
assert nav.claim(attempt,scope,pages=2,details=False) is None
MonitoringConfiguration.objects.filter(slot='active').update(revision=scope.revision+1)
try: research.execute(uuid4(),scope.revision+1,query.key,'PS5 Slim',scope.key,'attributes')
except StaleNavigation: pass
else: raise AssertionError('research attached to stale cycle')
""",
    )


def test_navigation_http_csrf_resume_and_suggestion_preview(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from django.test import Client
from django.db import DatabaseError
unit=nav.claim(attempt,scope,pages=2,details=False)
nav.failed(attempt,unit,SourceFailure('source_transport'))
client=Client(enforce_csrf_checks=True,HTTP_HOST="127.0.0.1")
assert client.get('/acompanhamento/navegacao/').status_code==200
token=client.cookies['csrftoken'].value
body={'work_id':str(unit.turn.id),'revision':str(scope.revision),'csrfmiddlewaretoken':token}
assert client.post('/acompanhamento/navegacao/retomar/',body).status_code==303
assert client.post('/acompanhamento/navegacao/retomar/',{'work_id':str(unit.turn.id),'revision':scope.revision}).status_code==403
assert client.post('/acompanhamento/navegacao/retomar/',body|{'work_id':'invalid'}).status_code==400
assert client.post('/acompanhamento/navegacao/retomar/',body|{'revision':scope.revision-1}).status_code==409
assert client.post('/acompanhamento/navegacao/retomar/',body|{'work_id':str(uuid4())}).status_code==404
with patch('garimpei.infra.repository.navigation.postgres_repository.PostgresNavigationRepository.resume',side_effect=DatabaseError()):
    response=client.post('/acompanhamento/navegacao/retomar/',body)
    assert response.status_code==503
before=NavigationUnitReceipt.objects.count()
assert client.get('/acompanhamento/navegacao/').status_code==200
assert NavigationUnitReceipt.objects.count()==before
suggestion=NicheSuggestion.objects.create(configuration_id=scope.configuration_id,revision=scope.revision,origin_interest=unit.query.key,original_term='PlayStation 5 Slim',term='PS5 Pro',relation_key='ps5-slim-pro',catalog_version='1',relation_reason='Outro modelo da família; produto diferente.',state='supported',observed_at=now())
SuggestionEvidence.objects.create(suggestion=suggestion,source=scope.source,external_id='1304',canonical_url='https://www.facebook.com/marketplace/item/1304/',excerpt='PS5 Pro funcionando',observed_at=now(),context_hash=scope.key,catalog_version='1')
response=client.get('/configuracoes/?sugestao='+str(suggestion.id))
assert response.status_code==200 and b'PS5 Pro' in response.content
assert 'PS5 Pro' not in build_read_monitoring_configuration().execute().product_names
assert client.get('/sugestoes/?pagina=0').status_code==400
assert client.get('/sugestoes/').status_code==200
""",
    )


def test_native_rebuild_reserves_cycle_budget_before_io(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
query=scope.searches[0]
NavigationWork.objects.exclude(origin_interest=query.key).update(phase='complete')
row=NavigationWork.objects.get(origin_interest=query.key,front='discovery')
checkpoint=NavigationCheckpoint.objects.get(work=row)
checkpoint.pages=99;checkpoint.cursor='source:opaque-cursor';checkpoint.save()
with patch('garimpei.config.env.load_navigation_policy',return_value=replace(load_navigation_policy(),cycle_pages=1000)):
    nav=build_navigation_repository(settings)
assert nav.claim(attempt,scope,pages=2,details=False) is None, '99+2 page rebuild exceeded cycle cap'
row.refresh_from_db();assert row.phase=='partial' and row.reason=='window_limit'
""",
    )


def test_opaque_cursor_4096_characters_does_not_overflow_unit_identity(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
row=NavigationWork.objects.filter(front='discovery').order_by('origin_interest').first()
checkpoint=NavigationCheckpoint.objects.get(work=row)
opaque=' {\"offset\":\"'+'A'*4070+'\",\"page\":2} '
assert len(opaque)<=4096
checkpoint.cursor='source:'+opaque;checkpoint.save()
checkpoint.refresh_from_db()
assert checkpoint.cursor=='source:'+opaque
unit=nav.claim(attempt,scope,pages=2,details=False)
assert unit and len(unit.unit_key)<=450
nav.page(attempt,unit,Page((),None))
receipt=NavigationUnitReceipt.objects.get(work_id=unit.turn.id)
assert len(receipt.unit_key)<=450 and opaque not in receipt.unit_key
""",
    )


def test_partial_finish_and_carry_are_atomic_across_new_cycle(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
unit=nav.claim(attempt,scope,pages=2,details=False)
nav.page(attempt,unit,source.search(scope,unit.search,None))
detail=nav.claim(attempt,scope,pages=0,details=True)
nav.failed(attempt,detail,SourceFailure('source_http_503'))
NavigationWork.objects.filter(front='discovery').update(phase='complete')
from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository
with patch.object(PostgresCollectionRepository,'finish',side_effect=RuntimeError('before_partial_commit')):
    try: nav.yield_slice(attempt,scope)
    except RuntimeError: pass
    else: raise AssertionError('partial commit fault not activated')
assert ListingObservation.objects.count()==0
assert CollectionCandidate.objects.exists()
assert CollectionCycle.objects.get(id=attempt.cycle_id).finished_at is None
nav.yield_slice(attempt,scope)
old=CollectionCycle.objects.get(id=attempt.cycle_id)
assert old.finished_at and old.phase=='partial'
assert NavigationCheckpoint.objects.filter(work__cycle=old).exclude(buffered_candidates=[]).exists()
assert ListingObservation.objects.count()==1
CollectionState.objects.update(next_attempt_at=now()-timedelta(seconds=1))
collection.reconcile(_listing_policy(settings));state.refresh_from_db()
assert state.current_id!=old.id
new_attempt=Attempt(state.current_id,state.generation)
new_scope=build_navigation_catalog().decorate_scope(collection.begin(new_attempt).scope)
nav=build_navigation_repository(settings);nav.prepare(new_attempt,new_scope)
pending_count=CollectionCandidate.objects.count()
assert pending_count>0
nav.prepare(new_attempt,new_scope)
assert CollectionCandidate.objects.count()==pending_count
assert NavigationWork.objects.filter(cycle_id=new_attempt.cycle_id,front='discovery',reason='cursor_rebuilt').exists()
assert not NavigationCheckpoint.objects.filter(work__cycle_id=new_attempt.cycle_id).exclude(cursor=None).exists()
new_detail=nav.claim(new_attempt,new_scope,pages=0,details=True)
nav.detail(new_attempt,new_detail,source.detail(new_scope,new_detail.target.external_id))
assert ListingObservation.objects.count()==2
assert ListingEvent.objects.count()==1
assert NavigationUnitReceipt.objects.filter(work__cycle=old).count()==2
""",
    )


def test_research_history_remains_readable_by_uuid_after_rollover(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from garimpei.usecase.navigation.request_research_usecase import RequestResearchUseCase
from garimpei.domain.navigation.ports import MissingNavigation
from garimpei.usecase.navigation.read_research_usecase import ReadResearchUseCase
from garimpei.infra.queries.navigation.postgres_queries import PostgresNavigationQueries
query=scope.searches[0]
request_id=uuid4()
research=RequestResearchUseCase(nav)
identity=research.execute(request_id,scope.revision,query.key,query.term,scope.key,'attributes')
reader=build_navigation_queries()
initial=ReadResearchUseCase(reader).execute(identity)
assert initial.work_id==identity and initial.canonical_term==query.term
assert initial.origin_interest==query.key and initial.purpose=="attributes"
assert initial.scope_key==scope.key and initial.source==scope.source
assert initial.phase=="pending" and initial.reason==""
assert initial.window_start==scope.window.start and initial.pages==0 and initial.details==0
assert initial.limits.page_limit==100 and initial.limits.term_limit==3
assert initial.window_end==scope.window.end and initial.scope_revision==scope.revision
page_unit=nav.claim(attempt,scope,pages=2,details=False)
nav.page(attempt,page_unit,source.search(scope,page_unit.search,None))
detail_unit=nav.claim(attempt,scope,pages=0,details=True)
nav.detail(attempt,detail_unit,source.detail(scope,detail_unit.target.external_id))
NavigationWork.objects.filter(cycle_id=attempt.cycle_id).update(phase='waiting',next_attempt_at=now()+timedelta(seconds=15))
nav.yield_slice(attempt,scope)
confirmed=reader.research(identity)
assert confirmed.shared_pages==1 and len(confirmed.observations)==1
CollectionState.objects.update(next_attempt_at=now()-timedelta(seconds=1))
collection.reconcile(_listing_policy(settings));state.refresh_from_db()
assert state.current_id != attempt.cycle_id
assert research.execute(request_id,scope.revision,query.key,query.term,scope.key,'attributes')==identity
# A different live policy cannot rewrite the historical work budget or context.
reader=PostgresNavigationQueries(build_read_monitoring_configuration(),now,replace(load_navigation_policy(),cycle_pages=3),settings.timeout,settings.cadence_ms/1000)
counts=(NavigationWork.objects.count(),NavigationCheckpoint.objects.count(),NavigationUnitReceipt.objects.count(),ListingObservation.objects.count())
history=ReadResearchUseCase(reader).execute(identity)
assert history.historical and history.limits==confirmed.limits
assert history.context_hash==confirmed.context_hash and history.window_end==confirmed.window_end
assert history.shared_pages==confirmed.shared_pages and history.observations==confirmed.observations
assert counts==(NavigationWork.objects.count(),NavigationCheckpoint.objects.count(),NavigationUnitReceipt.objects.count(),ListingObservation.objects.count())
try: reader.research(uuid4())
except MissingNavigation: pass
else: raise AssertionError('missing research UUID was not typed')
""",
    )


def test_research_requested_before_window_binds_context_once(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from garimpei.usecase.navigation.request_research_usecase import RequestResearchUseCase
from garimpei.usecase.navigation.read_research_usecase import ReadResearchUseCase
CollectionCycle.objects.filter(id=attempt.cycle_id).update(window_start=None,window_end=None)
query=scope.searches[0]
request=uuid4();research=RequestResearchUseCase(nav)
identity=research.execute(request,scope.revision,query.key,query.term,scope.key,'comparables')
reader=ReadResearchUseCase(build_navigation_queries())
assert reader.execute(identity).window_end is None
bound_scope=build_navigation_catalog().decorate_scope(collection.begin(attempt).scope)
nav.prepare(attempt,bound_scope)
bound=reader.execute(identity)
assert bound.window_end==bound_scope.window.end and bound.purpose=='comparables'
nav.prepare(attempt,bound_scope)
assert reader.execute(identity).context_hash==bound.context_hash
assert research.execute(request,scope.revision,query.key,query.term,scope.key,'comparables')==identity
""",
    )


def test_suggestion_budget_wait_and_caps_are_public_read_only(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from garimpei.infra.queries.navigation.postgres_queries import PostgresNavigationQueries
reader=build_navigation_queries()
counts=(NavigationWork.objects.count(),NicheSuggestion.objects.count(),ListingObservation.objects.count())
active=reader.suggestions(1).budget
assert active.reason=='active_work' and active.page_limit==1 and active.detail_limit==1
assert active.seconds_limit==45 and active.interval_seconds==300 and active.evidence_limit==10
assert counts==(NavigationWork.objects.count(),NicheSuggestion.objects.count(),ListingObservation.objects.count())
CollectionCycle.objects.filter(id=attempt.cycle_id).update(finished_at=now())
CollectionState.objects.update(next_attempt_at=now()+timedelta(seconds=60))
query=next(q for q in scope.searches if q.term=='PlayStation 5 Slim')
row=NicheSuggestion.objects.create(configuration_id=scope.configuration_id,revision=scope.revision,origin_interest=query.key,original_term=query.term,term='PS5 Pro',relation_key='ps5-slim-pro',catalog_version='1',relation_reason='Outro modelo da família.',state='supported',observed_at=now(),last_slice_at=now(),pages=1,details=1)
SuggestionEvidence.objects.create(suggestion=row,source=scope.source,external_id='1304',canonical_url='https://www.facebook.com/marketplace/item/1304/',excerpt='PS5 Pro',observed_at=now(),context_hash=scope.key,catalog_version='1')
budget=reader.suggestions(1).budget
assert budget.reason=='cooldown' and budget.next_at>now()
assert budget.pages==1 and budget.details==1
CollectionState.objects.update(next_attempt_at=now()+timedelta(seconds=10))
assert reader.suggestions(1).budget.reason=='active_due_soon'
CollectionState.objects.update(source_not_before=now()+timedelta(seconds=90))
assert reader.suggestions(1).budget.reason=='source_wait'
CollectionState.objects.update(source_not_before=None,next_attempt_at=now()+timedelta(seconds=60))
NicheSuggestion.objects.update(last_slice_at=now()-timedelta(seconds=301))
limited=PostgresNavigationQueries(build_read_monitoring_configuration(),now,replace(load_navigation_policy(),suggestion_limit=1,evidence_limit=1),settings.timeout,settings.cadence_ms/1000)
page=limited.suggestions(1)
assert page.budget.suggestion_count==1 and page.budget.suggestion_limit==1
assert page.budget.capacity_reason=='suggestion_limit'
assert len(page.items[0].evidence)==1
assert not Listing.objects.exists() and not ListingEvent.objects.exists()
""",
    )


def test_suggestion_100_records_and_10_evidences_preserve_every_record(
    navigation_instance: FoundationInstance, navigation_source: NavigationSourceFake
) -> None:
    source = navigation_source
    source.related_ids = ("8500",)
    source.extra_cards = {
        str(8500 + i): {"title": "PS5 Pro funcionando", "price": "R$ 3.200,00"} for i in range(10)
    }
    try:
        shell(
            navigation_instance,
            BOOTSTRAP
            + """
from garimpei.infra.repository.navigation.suggestion_repository import PostgresSuggestionRepository
from garimpei.usecase.navigation.run_suggestions_usecase import RunSuggestionsUseCase
from tests.factories.navigation_timing import UtcClockFake
clock=UtcClockFake(now())
CollectionCycle.objects.filter(id=attempt.cycle_id).update(finished_at=clock.now())
CollectionState.objects.update(next_attempt_at=clock.now()+timedelta(seconds=60))
query=next(q for q in scope.searches if q.term=='PlayStation 5 Slim')
for index in range(100):
    NicheSuggestion.objects.create(configuration_id=scope.configuration_id,revision=scope.revision,origin_interest=query.key,original_term=query.term,term='ocupado'+str(index),relation_key='occupied'+str(index),catalog_version='1',relation_reason='fixture sem suporte')
store=PostgresSuggestionRepository(build_read_monitoring_configuration(),build_navigation_catalog(),load_navigation_policy(),clock.now,20,1.2)
assert store.claim() is None
assert NicheSuggestion.objects.count()==100 and not SuggestionEvidence.objects.exists()
# Only the fixture removes an empty placeholder to exercise 99 -> 100; the runtime never evicts evidence.
NicheSuggestion.objects.get(relation_key='occupied0').delete()
assert NicheSuggestion.objects.count()==99
RunSuggestionsUseCase(store,source,load_navigation_policy(),lambda:0.0,20,1.2).execute()
assert NicheSuggestion.objects.count()==100 and SuggestionEvidence.objects.count()==1
assert NicheSuggestion.objects.get(term='PS5 Pro').evidence.count()==1
""",
        )
        for index in range(1, 10):
            source.related_ids = (str(8500 + index),)
            shell(
                navigation_instance,
                """
from datetime import timedelta
from garimpei.main import build_navigation_catalog,build_read_monitoring_configuration,_effective_listing_settings
from garimpei.config.env import load_navigation_policy
from garimpei.infra.persistence.navigation_models import NicheSuggestion,SuggestionEvidence
from garimpei.infra.persistence.listing_models import CollectionState
from garimpei.infra.repository.navigation.suggestion_repository import PostgresSuggestionRepository
from garimpei.infra.gateway.listing.fixture_source import FixtureSource
from garimpei.usecase.navigation.run_suggestions_usecase import RunSuggestionsUseCase
from tests.factories.navigation_timing import UtcClockFake
last=NicheSuggestion.objects.get(term='PS5 Pro').last_slice_at
clock=UtcClockFake(last+timedelta(seconds=300))
CollectionState.objects.update(next_attempt_at=clock.now()+timedelta(seconds=60))
policy=load_navigation_policy();settings=_effective_listing_settings()
store=PostgresSuggestionRepository(build_read_monitoring_configuration(),build_navigation_catalog(),policy,clock.now,20,1.2)
RunSuggestionsUseCase(store,FixtureSource(settings.fixture_url,20),policy,lambda:0.0,20,1.2).execute()
""",
            )
        calls = len(source.calls)
        shell(
            navigation_instance,
            """
from datetime import timedelta
from garimpei.main import build_navigation_catalog,build_read_monitoring_configuration
from garimpei.config.env import load_navigation_policy
from garimpei.infra.persistence.navigation_models import NicheSuggestion,SuggestionEvidence
from garimpei.infra.persistence.listing_models import CollectionState,Listing,ListingEvent
from garimpei.infra.repository.navigation.suggestion_repository import PostgresSuggestionRepository
from garimpei.infra.queries.navigation.postgres_queries import PostgresNavigationQueries
from tests.factories.navigation_timing import UtcClockFake
row=NicheSuggestion.objects.get(term='PS5 Pro')
assert row.evidence.count()==10
before=set(SuggestionEvidence.objects.values_list('id',flat=True))
clock=UtcClockFake(row.last_slice_at+timedelta(seconds=300))
CollectionState.objects.update(next_attempt_at=clock.now()+timedelta(seconds=60))
policy=load_navigation_policy();store=PostgresSuggestionRepository(build_read_monitoring_configuration(),build_navigation_catalog(),policy,clock.now,20,1.2)
assert store.claim() is None
assert set(SuggestionEvidence.objects.values_list('id',flat=True))==before
assert NicheSuggestion.objects.count()==100
page=PostgresNavigationQueries(build_read_monitoring_configuration(),clock.now,policy,20,1.2).suggestions(1)
assert page.items[0].limit_reason=='evidence_limit' and len(page.items[0].evidence)==10
assert page.budget.capacity_reason=='suggestion_limit'
assert not Listing.objects.exists() and not ListingEvent.objects.exists()
""",
        )
        assert len(source.calls) == calls
    finally:
        source.related_ids = ("1304", "1305")
        source.extra_cards = {}


def test_exact_300_seconds_and_missing_support_stays_inconclusive(
    navigation_instance: FoundationInstance, navigation_source: NavigationSourceFake
) -> None:
    source = navigation_source
    source.related_ids = ("1305",)
    try:
        shell(
            navigation_instance,
            BOOTSTRAP
            + """
from garimpei.infra.repository.navigation.suggestion_repository import PostgresSuggestionRepository
from garimpei.usecase.navigation.run_suggestions_usecase import RunSuggestionsUseCase
from tests.factories.navigation_timing import UtcClockFake
clock=UtcClockFake(now())
CollectionCycle.objects.filter(id=attempt.cycle_id).update(finished_at=clock.now())
CollectionState.objects.update(next_attempt_at=clock.now()+timedelta(seconds=60))
query=next(q for q in scope.searches if q.term=='PlayStation 5 Slim')
row=NicheSuggestion.objects.create(configuration_id=scope.configuration_id,revision=scope.revision,origin_interest=query.key,original_term=query.term,term='PS5 Pro',relation_key='ps5-slim-pro',catalog_version='1',relation_reason='Outro modelo',last_slice_at=clock.now()-timedelta(seconds=299))
policy=load_navigation_policy()
store=PostgresSuggestionRepository(build_read_monitoring_configuration(),build_navigation_catalog(),policy,clock.now,20,1.2)
assert store.claim() is None
clock.advance(1)
RunSuggestionsUseCase(store,source,policy,lambda:0.0,20,1.2).execute()
row.refresh_from_db()
assert row.last_slice_at==clock.now() and row.state=='inconclusive' and row.reason=='evidence_pending'
assert row.pages==1 and row.details==0 and not row.evidence.exists()
assert not build_navigation_queries().suggestions(1).items
assert not Listing.objects.exists() and not ListingEvent.objects.exists()
""",
        )
    finally:
        source.related_ids = ("1304", "1305")


def test_justified_fourth_term_is_rejected_by_shared_effective_budget(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from garimpei.domain.navigation.catalog import Catalog,Relation
from garimpei.infra.repository.navigation.postgres_repository import PostgresNavigationRepository
from garimpei.usecase.navigation.request_research_usecase import RequestResearchUseCase
catalog=build_navigation_catalog()
catalog=Catalog('test-extra',catalog.families,(*catalog.relations,Relation('slim-fat','PlayStation 5 Slim','PS5 Fat','Outro modelo da mesma família, sem equivalência')))
nav=PostgresNavigationRepository(collection,build_read_monitoring_configuration(),catalog,load_navigation_policy(),_listing_policy(settings),now,lambda attempt,delay:None)
research=RequestResearchUseCase(nav);query=next(q for q in scope.searches if q.term=='PlayStation 5 Slim')
assert catalog.permits(query.term,'PS5 Fat')
research.execute(uuid4(),scope.revision,query.key,'PS5 Pro',scope.key,'comparables')
before=NavigationWork.objects.count()
try: research.execute(uuid4(),scope.revision,query.key,'PS5 Fat',scope.key,'comparables')
except StaleNavigation: pass
else: raise AssertionError('justified fourth term bypassed shared budget')
assert NavigationWork.objects.count()==before
""",
    )


def test_two_interest_fronts_receive_turns_despite_real_controlled_timeout(
    navigation_instance: FoundationInstance, navigation_source: NavigationSourceFake
) -> None:
    source = navigation_source
    source.mode = "slow_detail"
    source.release.clear()
    try:
        shell(
            navigation_instance,
            BOOTSTRAP
            + """
from garimpei.usecase.navigation.run_slice_usecase import RunSliceUseCase
from time import monotonic
# Both fronts start pending with actual source pages already confirmed.
for _ in range(2):
    unit=nav.claim(attempt,scope,pages=2,details=False)
    nav.page(attempt,unit,source.search(scope,unit.search,unit.cursor))
NavigationWork.objects.all().update(last_turn=5)
slow=NavigationWork.objects.get(original_term='PlayStation 5 Slim',front='investigation')
slow.last_turn=4;slow.save()
source=FixtureSource(settings.fixture_url,1)
runner=RunSliceUseCase(collection,nav,source,source,build_navigation_catalog(),load_navigation_policy(),monotonic,1,1.2)
runner.execute(attempt)
first=list(NavigationUnitReceipt.objects.filter(turn_order__gte=6).select_related('work').order_by('turn_order'))[:4]
assert len(first)==4
assert len({(receipt.work.origin_interest,receipt.work.front) for receipt in first})==4
assert first[0].reason=='source_transport' and first[0].consumed_details==1
assert first[2].work.original_term=='iPhone 13 128 GB' and first[2].consumed_details==1
assert ListingObservation.objects.filter(listing__external_id='1302').exists()
assert NavigationWork.objects.get(original_term='iPhone 13 128 GB',front='investigation').last_progress_at
assert not CollectionState.objects.get().access_suspended and CollectionState.objects.get().source_not_before is None
""",
        )
        assert source.held.is_set()
    finally:
        source.mode = "normal"
        source.release.set()


def test_resume_http_persists_intent_and_every_rejection_preserves_history(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
from django.test import Client
from django.db import DatabaseError
unit=nav.claim(attempt,scope,pages=2,details=False)
nav.failed(attempt,unit,SourceFailure('source_transport'))
client=Client(enforce_csrf_checks=True,HTTP_HOST='127.0.0.1')
client.get('/acompanhamento/navegacao/')
body={'work_id':str(unit.turn.id),'revision':str(scope.revision),'csrfmiddlewaretoken':client.cookies['csrftoken'].value}
def snapshot():
    return (list(NavigationWork.objects.order_by('id').values()),list(NavigationCheckpoint.objects.order_by('work_id').values()),list(NavigationUnitReceipt.objects.order_by('id').values()),list(CollectionState.objects.values()),list(ListingObservation.objects.values()))
with connection.cursor() as cursor:
    cursor.execute("SELECT count(*) FROM procrastinate_jobs WHERE task_name='garimpei.collect_listings'");before_jobs=cursor.fetchone()[0]
response=client.post('/acompanhamento/navegacao/retomar/',body)
assert response.status_code==303 and response['Location']=='/acompanhamento/'
row=NavigationWork.objects.get(id=unit.turn.id)
assert row.phase=='pending' and row.reason=='resume_requested' and row.next_attempt_at<=now()
with connection.cursor() as cursor:
    cursor.execute("SELECT count(*) FROM procrastinate_jobs WHERE task_name='garimpei.collect_listings'");assert cursor.fetchone()[0]==before_jobs
    cursor.execute("SELECT count(*) FROM procrastinate_jobs WHERE task_name='garimpei.collect_listings' AND status='todo' AND args->>'cycle_id'=%s AND args->>'generation'=%s",[str(attempt.cycle_id),str(attempt.generation)])
    assert cursor.fetchone()[0]==1, 'resume must retain exactly one accepted task for this generation'
for data,expected in [(body|{'work_id':'bad'},400),(body|{'revision':scope.revision-1},409),({'work_id':str(unit.turn.id),'revision':scope.revision},403)]:
    before=snapshot();assert client.post('/acompanhamento/navegacao/retomar/',data).status_code==expected;assert snapshot()==before
CollectionState.objects.update(access_suspended=True)
before=snapshot();assert client.post('/acompanhamento/navegacao/retomar/',body).status_code==409;assert snapshot()==before
CollectionState.objects.update(access_suspended=False)
before=snapshot()
with patch('garimpei.infra.repository.navigation.postgres_repository.PostgresNavigationRepository.resume',side_effect=DatabaseError()):
    response=client.post('/acompanhamento/navegacao/retomar/',body)
    assert response.status_code==503 and b'Tente novamente' in response.content
assert snapshot()==before
""",
    )


def test_legacy_numeric_cursor_rebuild_keeps_confirmed_history_and_budget(
    navigation_instance: FoundationInstance,
) -> None:
    shell(
        navigation_instance,
        BOOTSTRAP
        + """
row=NavigationWork.objects.filter(front='discovery').order_by('origin_interest').first()
NavigationWork.objects.exclude(id=row.id).update(phase='complete')
checkpoint=NavigationCheckpoint.objects.get(work=row)
checkpoint.cursor='2';checkpoint.pages=1;checkpoint.save()
unit=nav.claim(attempt,scope,pages=2,details=False)
assert unit is not None and unit.cursor=='2'
nav.failed(attempt,unit,SourceFailure('continuation_scope_mismatch'))
checkpoint.refresh_from_db();row.refresh_from_db()
assert checkpoint.cursor is None and checkpoint.pages==1
assert row.reason=='cursor_rebuilt' and row.last_progress_at is None
prior=list(NavigationUnitReceipt.objects.values_list('id','unit_key','reason'))
assert len(prior)==1 and prior[0][2]=='continuation_scope_mismatch'
NavigationWork.objects.filter(id=row.id).update(next_attempt_at=None)
unit=nav.claim(attempt,scope,pages=2,details=False)
assert unit is not None and unit.cursor is None
opaque=' {"offset":"'+'x'*1650+'","page":2} '
nav.page(attempt,unit,Page((), 'source:'+opaque))
checkpoint.refresh_from_db()
assert checkpoint.cursor=='source:'+opaque and checkpoint.pages==2
assert NavigationUnitReceipt.objects.filter(id=prior[0][0],unit_key=prior[0][1],reason=prior[0][2]).exists()
assert NavigationUnitReceipt.objects.count()==2
""",
    )

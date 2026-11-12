from pathlib import Path

import pytest

from tests.factories.listing import ControlledClock, serve
from tests.factories.navigation import NavigationSourceFake, prepare_navigation_instance
from tests.factories.runtime import pause_worker, resume_worker


def test_saved_profile_budget_matches_worker_admission_without_timeout_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GARIMPEI_LISTING_TIMEOUT", raising=False)
    monkeypatch.delenv("GARIMPEI_FACEBOOK_STATE_FILE", raising=False)
    root = Path(__file__).resolve().parents[4]
    source = NavigationSourceFake()
    with serve(source) as url:
        instance = prepare_navigation_instance(root, tmp_path, url)
        clock = ControlledClock(tmp_path / "clock")
        clock.advance(0)
        with instance.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_LISTING_FIXTURE_CLOCK={clock.path}\n"
                f"GARIMPEI_INTEGRATION_PRIVATE_DIR={tmp_path / 'integrations'}\n"
                "GARIMPEI_ALERTS_ENABLED=false\n"
            )
        assert "GARIMPEI_LISTING_TIMEOUT=" not in instance.private_file.read_text()
        started = instance.command("./scripts/init.sh", "--disposable")
        assert started.returncode == 0, started.stdout + started.stderr
        group = pause_worker(instance)
        try:
            result = instance.shell(
                """
import json,os
from datetime import timedelta
from garimpei.config.env import load_navigation_policy,load_integration_private_settings
from garimpei.main import (build_monitoring_handler,build_monitoring_queries,
    build_read_monitoring_configuration,build_navigation_catalog,build_navigation_queries,
    _effective_listing_settings,_navigation_collection,_listing_policy,_listing_clock)
from garimpei.infra.persistence.integration_models import IntegrationSettings
from garimpei.infra.persistence.listing_models import CollectionState,ListingObservation
from garimpei.infra.persistence.navigation_models import NicheSuggestion
from garimpei.infra.repository.navigation.suggestion_repository import PostgresSuggestionRepository
from garimpei.usecase.monitoring.save_step_usecase import StepInput
from tests.factories.monitoring import prepare_state
assert 'GARIMPEI_LISTING_TIMEOUT' not in os.environ
prepare_state('RASCUNHO')
build_monitoring_handler()._complete.execute(StepInput('interesses',build_monitoring_queries().read_form().revision,category_ids=(),product_names=('PlayStation 5 Slim',)))
settings=_effective_listing_settings()
now=_listing_clock(settings)
collection=_navigation_collection(settings)
collection.reconcile(_listing_policy(settings))
state=CollectionState.objects.select_related('current').get()
cycle=state.current
cycle.finished_at=now();cycle.phase='complete';cycle.save()
due=now()+timedelta(seconds=15)
CollectionState.objects.update(next_attempt_at=due)
cookie_budget=build_navigation_queries().suggestions(1).budget
assert cookie_budget.reason=='idle_available'
# A saved mode selects the real profile defaults without credentials or a browser.
IntegrationSettings.objects.update_or_create(id='local',defaults={'facebook_mode':'profile'})
settings=_effective_listing_settings()
store=PostgresSuggestionRepository(build_read_monitoring_configuration(),build_navigation_catalog(),load_navigation_policy(),_listing_clock(settings),settings.timeout,settings.cadence_ms/1000)
assert store.claim() is None
before=(list(IntegrationSettings.objects.values()),NicheSuggestion.objects.count(),ListingObservation.objects.count())
profile_budget=build_navigation_queries().suggestions(1).budget
assert before==(list(IntegrationSettings.objects.values()),NicheSuggestion.objects.count(),ListingObservation.objects.count())
CollectionState.objects.update(next_attempt_at=now()+timedelta(seconds=60))
available_budget=build_navigation_queries().suggestions(1).budget
assert available_budget.reason=='idle_available'
assert store.claim() is not None
assert not (load_integration_private_settings().directory/'facebook-browser').exists()
print(json.dumps({'cookie_due15':cookie_budget.reason,'profile_due15':profile_budget.reason,'worker_reserved_due15':False,'profile_due60':available_budget.reason,'worker_reserved_due60':True}))
assert profile_budget.reason=='active_due_soon'
assert profile_budget.next_at==due
"""
            )
            assert result.returncode == 0, result.stdout + result.stderr
            print(result.stdout, end="")
            assert source.calls == []
        finally:
            with instance.database() as database:
                database.execute(
                    "DELETE FROM procrastinate_jobs WHERE status='todo' AND task_name IN "
                    "('garimpei.collect_listings','garimpei.navigation_suggestions')"
                )
            resume_worker(group)
            stopped = instance.command("./scripts/stop.sh", "--clean")
            assert stopped.returncode == 0, stopped.stdout + stopped.stderr

from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from garimpei.config.env import AlertSettings
    from garimpei.domain.alert.alert import AlertPolicy
    from garimpei.domain.listing.ports import (
        Attempt,
        Clock,
        CollectionPolicy,
        Geocoding,
        ListingSource,
    )
    from garimpei.domain.navigation.catalog import Catalog
    from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
    from garimpei.infra.gateway.inference.input_preparer import LocalInputPreparer
    from garimpei.infra.gateway.inference.ollama_gateway import OllamaGateway
    from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser
    from garimpei.infra.gateway.monitoring.facebook_catalog import FacebookCategoryCatalog
    from garimpei.infra.http.inference.inference_handler import InferenceHandler
    from garimpei.infra.http.integration.integration_handler import IntegrationHandler
    from garimpei.infra.http.listing.condition_handler import ConditionHandler
    from garimpei.infra.http.listing.exploration_handler import ExplorationHandler
    from garimpei.infra.http.monitoring.monitoring_handler import MonitoringHandler
    from garimpei.infra.http.navigation.navigation_handler import NavigationHandler
    from garimpei.infra.http.operations.status_handler import OperationsHandler
    from garimpei.infra.queries.listing.condition_queries import PostgresConditionQueries
    from garimpei.infra.queries.monitoring.postgres_queries import PostgresMonitoringQueries
    from garimpei.infra.queries.navigation.postgres_queries import PostgresNavigationQueries
    from garimpei.infra.repository.alert.first_alert_repository import PostgresFirstAlertRepository
    from garimpei.infra.repository.alert.postgres_repository import PostgresAlertRepository
    from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
    from garimpei.infra.repository.integration.facebook_profile_repository import (
        PostgresFacebookProfileRepository,
    )
    from garimpei.infra.repository.integration.postgres_repository import (
        PostgresIntegrationRepository,
    )
    from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository
    from garimpei.infra.repository.navigation.postgres_repository import (
        PostgresNavigationRepository,
    )
    from garimpei.infra.repository.operations.backup_repository import PostgresBackupRepository
    from garimpei.infra.repository.operations.progress_repository import (
        PostgresOperationalRepository,
    )
    from garimpei.infra.repository.valuation.postgres_repository import PostgresValuationRepository
    from garimpei.infra.worker.alert_handler import AlertTaskHandler
    from garimpei.infra.worker.facebook_login_handler import FacebookLoginHandler
    from garimpei.infra.worker.listing_handler import ListingTaskHandler
    from garimpei.infra.worker.valuation_handler import ValuationTaskHandler
    from garimpei.usecase.alert.read_alert_diagnostic_usecase import ReadAlertDiagnosticUseCase
    from garimpei.usecase.inference.read_analysis_usecase import ReadAnalysisUseCase
    from garimpei.usecase.inference.request_analysis_usecase import RequestAnalysisUseCase
    from garimpei.usecase.inference.run_analysis_usecase import RunAnalysisUseCase
    from garimpei.usecase.listing.classify_condition_usecase import ClassifyConditionUseCase
    from garimpei.usecase.listing.publish_exploration_usecase import PublishExplorationUseCase
    from garimpei.usecase.listing.read_collection_status_usecase import ReadCollectionStatusUseCase
    from garimpei.usecase.listing.read_condition_usecase import ReadConditionUseCase
    from garimpei.usecase.listing.read_listing_changes_usecase import ReadListingChangesUseCase
    from garimpei.usecase.listing.read_listing_usecase import ReadListingUseCase
    from garimpei.usecase.monitoring.read_configuration_usecase import (
        ReadMonitoringConfigurationUseCase,
    )
    from garimpei.usecase.navigation.read_suggestions_usecase import ReadSuggestionUseCase
    from garimpei.usecase.operations.create_backup_usecase import CreateBackupUseCase
    from garimpei.usecase.operations.read_status_usecase import ReadOperationalStatusUseCase
    from garimpei.usecase.operations.restore_backup_usecase import RestoreBackupUseCase
    from garimpei.usecase.valuation.read_profit_usecase import ReadProfitUseCase
    from garimpei.usecase.valuation.read_valuation_usecase import ReadValuationUseCase

from procrastinate import App, SyncPsycopgConnector
from psycopg import Connection

from garimpei.config.env import ListingSettings, load_config, load_listing_settings
from garimpei.infra.runtime.logging import WorkerNoticeStream
from garimpei.infra.runtime.probes import DatabaseProbe, MigrationsProbe, WahaProbe, WorkerProbe
from garimpei.infra.worker.runtime_handler import RuntimeTaskHandler
from garimpei.usecase.runtime.check_readiness_usecase import CheckReadinessUseCase


def build_readiness() -> CheckReadinessUseCase:
    config = load_config()
    return CheckReadinessUseCase(
        {
            "database": DatabaseProbe(),
            "migrations": MigrationsProbe(),
            "worker": WorkerProbe(config),
            "waha": WahaProbe(config),
        }
    )


def build_database_probe() -> DatabaseProbe:
    return DatabaseProbe()


@lru_cache(maxsize=1)
def register_tasks() -> None:
    from procrastinate.contrib.django import app

    app.task(name="garimpei.media", queue="media")(_handle_media)
    app.task(name="garimpei.local_analysis", queue="inference")(_handle_inference)
    app.task(name="garimpei.operational_maintenance", queue="maintenance")(_handle_operations)
    app.task(name="garimpei.alert_tick", queue="alert")(_handle_alert)
    app.task(name="garimpei.runtime_probe", queue="runtime")(_handle_runtime_probe)
    app.task(name="garimpei.collect_listings", queue="listing")(_handle_listing)
    app.task(name="garimpei.navigation_suggestions", queue="listing")(
        _handle_navigation_suggestions
    )
    app.task(name="garimpei.evaluate_valuation", queue="valuation")(_handle_valuation)


def _handle_runtime_probe(probe_id: str) -> None:
    build_task_handler().execute(probe_id)


@lru_cache(maxsize=1)
def build_enqueue_app() -> App:
    return App(connector=SyncPsycopgConnector())


def _enqueue(name: str, queue: str, delay: int, **arguments: str | int) -> int:
    from django.db import connection

    register_tasks()
    connection.ensure_connection()
    if not isinstance(connection.connection, Connection):
        raise RuntimeError("Expected psycopg 3 connection for transactional enqueue")
    # A dedicated synchronous connector accepts the ORM's connection, including inside workers.
    return (
        build_enqueue_app()
        .configure_task(
            name=name,
            queue=queue,
            connection=connection.connection,
            schedule_in={"seconds": delay},
        )
        .defer(**arguments)
    )


def defer_runtime_probe(probe_id: str, delay: int = 0) -> int:
    return _enqueue("garimpei.runtime_probe", "runtime", delay, probe_id=probe_id)


def _defer_listing(cycle_id: UUID, generation: int) -> int:
    return _enqueue(
        "garimpei.collect_listings", "listing", 0, cycle_id=str(cycle_id), generation=generation
    )


def _handle_listing(cycle_id: str, generation: int) -> None:
    build_listing_task_handler().execute(cycle_id, generation)


def _listing_clock(settings: ListingSettings) -> "Clock":
    from datetime import UTC, datetime

    from django.utils.timezone import now

    path = settings.fixture_clock
    if path is None:
        return now

    def read_fixture_clock() -> datetime:
        value = datetime.fromisoformat(path.read_text().strip())
        if value.tzinfo is None:
            raise ValueError("Listing fixture clock requires a timezone")
        return value.astimezone(UTC)

    return read_fixture_clock


def _listing_policy(settings: ListingSettings) -> "CollectionPolicy":
    from garimpei.domain.listing.ports import CollectionPolicy

    return CollectionPolicy(
        settings.interval,
        settings.lease,
        settings.max_pages,
        settings.retry_base,
        settings.retry_max,
    )


def _collection_store(settings: ListingSettings) -> "PostgresCollectionRepository":
    from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository

    return PostgresCollectionRepository(
        build_read_monitoring_configuration(),
        _listing_clock(settings),
        _defer_listing,
        settings.lease,
        operations=build_operational_progress(),
    )


def reconcile_listings(*, recover_access: bool = False) -> None:
    from garimpei.usecase.listing.schedule_collection_usecase import ScheduleCollectionUseCase

    integration = build_integration_repository().read()
    if integration.facebook_mode == "profile" and integration.facebook_phase != "connected":
        return
    settings = _effective_listing_settings()
    store = _collection_store(settings)
    policy = _listing_policy(settings)
    if (
        recover_access
        and integration.facebook_mode != "profile"
        and (settings.fixture_url is not None or settings.facebook_state is not None)
    ):
        store.reconcile(policy, recover_access=True)
    else:
        ScheduleCollectionUseCase(store, policy).execute()


def build_listing_task_handler() -> "ListingTaskHandler":
    from garimpei.infra.gateway.listing.facebook_marketplace import UnavailableMarketplace
    from garimpei.infra.gateway.listing.fixture_source import FixtureSource

    settings = _effective_listing_settings()
    if settings.fixture_url is not None:
        fixture = FixtureSource(settings.fixture_url, settings.timeout)
        return _navigation_task(settings, fixture, fixture)
    if settings.facebook_state is not None or settings.facebook_profile is not None:
        return _build_live_listing_handler(settings)
    unavailable = UnavailableMarketplace()
    return _navigation_task(settings, unavailable, unavailable)


def _build_live_listing_handler(settings: ListingSettings) -> "ListingTaskHandler":
    from garimpei.infra.gateway.listing.cep_geocoding import BrasilApiGeocoding
    from garimpei.infra.gateway.listing.facebook_marketplace import FacebookMarketplace
    from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser

    path = settings.facebook_profile or settings.facebook_state
    assert path is not None
    browser = MarketplaceBrowser(
        path, settings.timeout, settings.cadence_ms, profile=settings.facebook_profile
    )
    geocoding = BrasilApiGeocoding(settings.timeout)
    source = FacebookMarketplace(browser, geocoding, build_monitoring_catalog().load())
    return _navigation_task(settings, source, geocoding, source.close)


def build_read_collection_status() -> "ReadCollectionStatusUseCase":
    from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
    from garimpei.usecase.listing.read_collection_status_usecase import ReadCollectionStatusUseCase

    return ReadCollectionStatusUseCase(
        PostgresListingQueries(), build_read_monitoring_configuration()
    )


def build_read_listing() -> "ReadListingUseCase":
    from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
    from garimpei.usecase.listing.read_listing_usecase import ReadListingUseCase

    return ReadListingUseCase(PostgresListingQueries(), build_read_monitoring_configuration())


def build_read_listing_changes() -> "ReadListingChangesUseCase":
    from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
    from garimpei.usecase.listing.read_listing_changes_usecase import ReadListingChangesUseCase

    return ReadListingChangesUseCase(PostgresListingQueries())


def build_task_handler() -> RuntimeTaskHandler:
    return RuntimeTaskHandler(defer_runtime_probe)


def build_worker_stderr() -> WorkerNoticeStream:
    return WorkerNoticeStream()


def build_monitoring_queries(*, repeatable_snapshot: bool = False) -> "PostgresMonitoringQueries":
    from garimpei.infra.queries.monitoring.postgres_queries import PostgresMonitoringQueries
    from garimpei.infra.repository.monitoring.postgres_repository import (
        PostgresMonitoringRepository,
    )

    return PostgresMonitoringQueries(
        PostgresMonitoringRepository(), repeatable_snapshot=repeatable_snapshot
    )


def build_monitoring_catalog() -> "FacebookCategoryCatalog":
    from garimpei.config.env import load_catalog_fixture
    from garimpei.infra.gateway.monitoring.facebook_catalog import FacebookCategoryCatalog

    return FacebookCategoryCatalog(
        load_catalog_fixture()
        or Path(__file__).parent / "infra/gateway/monitoring/facebook_categories.json"
    )


def build_read_monitoring_configuration(
    *, repeatable_snapshot: bool = False
) -> "ReadMonitoringConfigurationUseCase":
    from garimpei.usecase.monitoring.read_configuration_usecase import (
        ReadMonitoringConfigurationUseCase,
    )

    return ReadMonitoringConfigurationUseCase(
        build_monitoring_queries(repeatable_snapshot=repeatable_snapshot)
    )


def build_monitoring_handler() -> "MonitoringHandler":
    from garimpei.infra.http.monitoring.monitoring_handler import MonitoringHandler
    from garimpei.infra.persistence.monitoring_unit_of_work import PostgresMonitoringUnitOfWork
    from garimpei.infra.repository.monitoring.postgres_repository import (
        PostgresMonitoringRepository,
    )
    from garimpei.usecase.monitoring.complete_configuration_usecase import (
        CompleteMonitoringConfigurationUseCase,
    )
    from garimpei.usecase.monitoring.preview_products_usecase import PreviewProductsUseCase
    from garimpei.usecase.monitoring.read_catalog_usecase import ReadCategoryCatalogUseCase
    from garimpei.usecase.monitoring.read_form_usecase import ReadMonitoringFormUseCase
    from garimpei.usecase.monitoring.save_step_usecase import SaveMonitoringStepUseCase
    from garimpei.usecase.monitoring.update_configuration_usecase import (
        UpdateMonitoringConfigurationUseCase,
    )

    catalog = build_monitoring_catalog()
    unit = PostgresMonitoringUnitOfWork(PostgresMonitoringRepository())
    return MonitoringHandler(
        ReadMonitoringFormUseCase(build_monitoring_queries()),
        ReadCategoryCatalogUseCase(catalog),
        SaveMonitoringStepUseCase(unit.transaction, catalog),
        CompleteMonitoringConfigurationUseCase(unit.transaction, catalog),
        UpdateMonitoringConfigurationUseCase(unit.transaction, catalog),
        PreviewProductsUseCase(),
        build_read_collection_status(),
        build_operational_status(),
    )


def build_condition_queries() -> "PostgresConditionQueries":
    from garimpei.infra.queries.listing.condition_queries import PostgresConditionQueries

    return PostgresConditionQueries(build_read_monitoring_configuration())


def build_read_condition() -> "ReadConditionUseCase":
    from garimpei.usecase.listing.read_condition_usecase import ReadConditionUseCase

    return ReadConditionUseCase(build_condition_queries())


def build_classify_condition() -> "ClassifyConditionUseCase":
    from garimpei.infra.repository.listing.condition_repository import PostgresConditionRepository
    from garimpei.usecase.listing.classify_condition_usecase import ClassifyConditionUseCase

    return ClassifyConditionUseCase(PostgresConditionRepository())


def build_condition_handler() -> "ConditionHandler":
    from garimpei.infra.http.listing.condition_handler import ConditionHandler
    from garimpei.usecase.listing.list_conditions_usecase import ListConditionsUseCase

    return ConditionHandler(
        build_read_condition(),
        ListConditionsUseCase(build_condition_queries()),
        build_classify_condition(),
    )


def _defer_valuation(work_id: UUID) -> int:
    return _enqueue("garimpei.evaluate_valuation", "valuation", 0, work_id=str(work_id))


def _handle_valuation(work_id: str) -> None:
    build_valuation_handler().execute(UUID(work_id))


def build_valuation_store() -> "PostgresValuationRepository":
    from garimpei.infra.repository.valuation.postgres_repository import PostgresValuationRepository

    return PostgresValuationRepository(_defer_valuation, build_operational_progress())


def reconcile_valuations() -> None:
    build_valuation_store().reconcile(_listing_clock(load_listing_settings())())


def build_valuation_handler() -> "ValuationTaskHandler":
    from garimpei.config.env import load_valuation_fixture
    from garimpei.infra.gateway.valuation.new_source import RetailNewSource
    from garimpei.infra.worker.valuation_handler import ValuationTaskHandler
    from garimpei.usecase.valuation.evaluate_usecase import EvaluateValuationUseCase

    store = build_valuation_store()
    clock = _listing_clock(load_listing_settings())
    source = RetailNewSource(
        Path(__file__).parent / "infra/gateway/valuation/retail_catalog.json",
        load_valuation_fixture(),
    )
    return ValuationTaskHandler(EvaluateValuationUseCase(store, source, clock), store, clock)


def build_read_valuation() -> "ReadValuationUseCase":
    from garimpei.infra.queries.valuation.postgres_queries import PostgresValuationQueries
    from garimpei.usecase.valuation.read_valuation_usecase import ReadValuationUseCase

    return ReadValuationUseCase(PostgresValuationQueries(), _listing_clock(load_listing_settings()))


def build_read_profit() -> "ReadProfitUseCase":
    from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
    from garimpei.infra.queries.valuation.postgres_queries import PostgresValuationQueries
    from garimpei.infra.queries.valuation.profit_queries import PostgresProfitQueries
    from garimpei.usecase.valuation.read_profit_usecase import ReadProfitUseCase

    return ReadProfitUseCase(
        PostgresProfitQueries(
            build_read_monitoring_configuration(),
            PostgresListingQueries(),
            PostgresValuationQueries(),
        ),
        _listing_clock(load_listing_settings()),
    )


def build_publish_exploration() -> "PublishExplorationUseCase":
    from garimpei.config.env import load_exploration_settings
    from garimpei.infra.queries.listing.exploration_source import ExplorationSource
    from garimpei.infra.queries.valuation.postgres_queries import PostgresValuationQueries
    from garimpei.infra.repository.listing.exploration_repository import (
        PostgresExplorationRepository,
    )
    from garimpei.usecase.listing.publish_exploration_usecase import PublishExplorationUseCase

    labels = exploration_categories()
    return PublishExplorationUseCase(
        PostgresExplorationRepository(
            ExplorationSource(
                build_read_monitoring_configuration(repeatable_snapshot=True),
                PostgresValuationQueries(),
                labels,
            ),
            load_exploration_settings().retention,
        ),
        _listing_clock(load_listing_settings()),
    )


def exploration_categories() -> dict[str, str]:
    labels = {row.id: row.label for row in build_monitoring_catalog().load().entries}
    labels["cameras"] = "Câmeras"
    return labels


def build_exploration_handler() -> "ExplorationHandler":
    from garimpei.infra.http.listing.exploration_handler import ExplorationHandler
    from garimpei.infra.queries.listing.exploration_queries import PostgresExplorationQueries
    from garimpei.usecase.listing.read_exploration_updates_usecase import (
        ReadExplorationUpdatesUseCase,
    )
    from garimpei.usecase.listing.read_offer_detail_usecase import ReadOfferDetailUseCase
    from garimpei.usecase.listing.read_offers_usecase import ReadOffersUseCase

    reader = PostgresExplorationQueries()
    return ExplorationHandler(
        ReadOffersUseCase(reader),
        ReadOfferDetailUseCase(reader),
        ReadExplorationUpdatesUseCase(reader),
        build_read_condition(),
        build_classify_condition(),
        build_read_collection_status(),
        build_read_monitoring_configuration(),
        exploration_categories(),
        _exploration_worker_active,
        build_read_alert_diagnostic(),
    )


def _exploration_worker_active() -> bool:
    return WorkerProbe(load_config()).check()


def build_first_alert_store() -> "PostgresFirstAlertRepository":
    from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
    from garimpei.infra.repository.alert.first_alert_repository import PostgresFirstAlertRepository

    return PostgresFirstAlertRepository(
        build_read_monitoring_configuration(), PostgresListingQueries()
    )


def build_read_alert_diagnostic() -> "ReadAlertDiagnosticUseCase":
    from garimpei.infra.queries.alert.diagnostic_queries import PostgresAlertDiagnosticQueries
    from garimpei.usecase.alert.read_alert_diagnostic_usecase import ReadAlertDiagnosticUseCase

    return ReadAlertDiagnosticUseCase(PostgresAlertDiagnosticQueries())


def build_alert_store() -> "PostgresAlertRepository":
    from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
    from garimpei.infra.repository.alert.postgres_repository import PostgresAlertRepository

    return PostgresAlertRepository(
        build_read_monitoring_configuration(),
        PostgresListingQueries(),
        _alert_policy(),
        build_recovery_guard(),
        build_operational_progress(),
    )


def _alert_policy() -> "AlertPolicy":
    from garimpei.config.env import load_alert_settings
    from garimpei.domain.alert.alert import AlertPolicy

    value = load_alert_settings()
    return AlertPolicy(
        tick=value.tick,
        timeout=value.timeout,
        lease=value.lease,
        retry_base=value.retry_base,
        retry_max=value.retry_max,
        window=value.window,
        history_pages=value.history_pages,
    )


def build_alert_handler(stage: str) -> "AlertTaskHandler":
    from garimpei.domain.alert.alert import Binding
    from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
    from garimpei.infra.worker.alert_handler import AlertTaskHandler
    from garimpei.usecase.alert.adopt_first_alerts_usecase import AdoptFirstAlertsUseCase
    from garimpei.usecase.alert.consume_listing_events_usecase import ConsumeListingEventsUseCase
    from garimpei.usecase.alert.evaluate_alert_usecase import EvaluateAlertUseCase
    from garimpei.usecase.alert.reconcile_alert_usecase import ReconcileAlertUseCase
    from garimpei.usecase.alert.refresh_first_eligibility_usecase import (
        RefreshFirstEligibilityUseCase,
    )
    from garimpei.usecase.alert.send_alert_usecase import SendAlertUseCase

    settings, store, clock = (
        _effective_alert_settings(),
        build_alert_store(),
        _listing_clock(load_listing_settings()),
    )
    gateway = WahaGateway(settings.url, settings.key, _alert_policy())
    binding = (
        Binding(settings.session, settings.recipient, settings.account)
        if (
            settings.enabled
            and settings.session
            and settings.recipient
            and settings.account
            and settings.key
        )
        else None
    )
    actions = {
        "adopt": AdoptFirstAlertsUseCase(build_first_alert_store(), clock).execute,
        "refresh": RefreshFirstEligibilityUseCase(
            build_first_alert_store(), build_read_profit(), clock
        ).execute,
        "ingest": ConsumeListingEventsUseCase(store, build_read_listing_changes(), clock).execute,
        "evaluate": EvaluateAlertUseCase(store, build_read_profit(), clock).execute,
        "send": SendAlertUseCase(
            store, gateway, binding, build_read_listing_changes(), clock
        ).execute,
        "reconcile": ReconcileAlertUseCase(store, gateway, binding, clock).execute,
    }
    return AlertTaskHandler(stage, actions[stage])


def _handle_alert(stage: str) -> None:
    build_alert_handler(stage).execute()


def reconcile_alerts(*, recovery: bool = False) -> None:
    from datetime import timedelta

    from django.db import transaction
    from django.utils import timezone

    from garimpei.infra.persistence.alert_models import AlertFeedCursor, AlertIntent
    from garimpei.infra.persistence.listing_models import Listing, ListingEvent
    from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication

    now = timezone.now()
    with transaction.atomic():
        lock_monitoring_publication()
        if not Listing.objects.exists() and not ListingEvent.objects.exists():
            return
        cursor, _ = AlertFeedCursor.objects.select_for_update().get_or_create(installation="local")
        if recovery:
            AlertIntent.objects.filter(state="review").update(
                state="uncertain", next_action=_listing_clock(load_listing_settings())()
            )
        if cursor.next_tick and cursor.next_tick > now:
            return
        for stage in ("adopt", "ingest", "refresh", "evaluate", "reconcile", "send"):
            _enqueue("garimpei.alert_tick", "alert", 0, stage=stage)
        cursor.next_tick = now + timedelta(seconds=_alert_policy().tick)
        cursor.save(update_fields=["next_tick"])


def build_integration_repository() -> "PostgresIntegrationRepository":
    from garimpei.config.env import load_integration_private_settings
    from garimpei.infra.repository.integration.postgres_repository import (
        PostgresIntegrationRepository,
    )

    return PostgresIntegrationRepository(
        load_integration_private_settings().directory, _listing_clock(load_listing_settings())
    )


def _effective_listing_settings() -> ListingSettings:
    from garimpei.config.env import load_integration_private_settings

    store = build_integration_repository()
    if store.read().facebook_mode == "profile":
        return load_listing_settings(
            facebook_profile=load_integration_private_settings().directory / "facebook-browser"
        )
    return load_listing_settings(facebook_state=store.facebook_path())


def build_facebook_profile_repository() -> "PostgresFacebookProfileRepository":
    from garimpei.infra.repository.integration.facebook_profile_repository import (
        PostgresFacebookProfileRepository,
    )

    return PostgresFacebookProfileRepository(
        _listing_clock(load_listing_settings()),
        build_integration_repository().resume_collections,
    )


def _build_login_browser() -> "MarketplaceBrowser":
    from garimpei.config.env import load_facebook_browser_origin, load_integration_private_settings
    from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser

    path = load_integration_private_settings().directory / "facebook-browser"
    origin, headless = load_facebook_browser_origin()
    return MarketplaceBrowser(
        path, 20, 1200, profile=path, login_origin=origin, profile_headless=headless
    )


@lru_cache(maxsize=1)
def build_facebook_login_handler() -> "FacebookLoginHandler":
    from garimpei.infra.worker.facebook_login_handler import FacebookLoginHandler

    return FacebookLoginHandler(
        build_facebook_profile_repository(),
        _build_login_browser,
        _listing_clock(load_listing_settings()),
    )


def _effective_alert_settings() -> "AlertSettings":
    from dataclasses import replace

    from garimpei.config.env import load_alert_settings

    settings = load_alert_settings()
    value = build_integration_repository().read()
    if not value.whatsapp_configured:
        return settings
    return replace(
        settings,
        enabled=value.alerts_enabled,
        session=value.whatsapp_session,
        recipient=value.whatsapp_group,
        account=value.whatsapp_account,
    )


def build_integration_handler() -> "IntegrationHandler":
    from garimpei.config.env import load_alert_settings
    from garimpei.infra.gateway.integration.waha_session import WahaSessionGateway
    from garimpei.infra.http.integration.integration_handler import IntegrationHandler
    from garimpei.usecase.integration.configure_whatsapp_usecase import ConfigureWhatsAppUseCase
    from garimpei.usecase.integration.confirm_facebook_login_usecase import (
        ConfirmFacebookLoginUseCase,
    )
    from garimpei.usecase.integration.connect_whatsapp_usecase import ConnectWhatsAppUseCase
    from garimpei.usecase.integration.read_facebook_status_usecase import ReadFacebookStatusUseCase
    from garimpei.usecase.integration.read_integrations_usecase import ReadIntegrationsUseCase
    from garimpei.usecase.integration.read_qr_usecase import ReadWhatsAppQrUseCase
    from garimpei.usecase.integration.request_facebook_login_usecase import (
        RequestFacebookLoginUseCase,
    )
    from garimpei.usecase.integration.save_facebook_usecase import SaveFacebookSessionUseCase

    settings = load_alert_settings()
    store = build_integration_repository()
    config = store.read()
    session = config.whatsapp_session or settings.session or "default"
    gateway = WahaSessionGateway(settings.url, settings.key, min(settings.timeout, 5))
    return IntegrationHandler(
        ReadIntegrationsUseCase(store, gateway, session),
        SaveFacebookSessionUseCase(store, _listing_clock(load_listing_settings())),
        ConnectWhatsAppUseCase(gateway, session),
        ConfigureWhatsAppUseCase(store, gateway, session),
        ReadWhatsAppQrUseCase(gateway, session),
        store.disable_whatsapp,
        ReadFacebookStatusUseCase(store),
        RequestFacebookLoginUseCase(build_facebook_profile_repository()),
        ConfirmFacebookLoginUseCase(build_facebook_profile_repository()),
    )


def build_inference_preparer() -> "LocalInputPreparer":
    from garimpei.config.env import load_inference_settings
    from garimpei.infra.gateway.inference.input_preparer import LocalInputPreparer

    return LocalInputPreparer(load_inference_settings())


def build_inference_guard() -> "HostGpuGuard":
    from garimpei.config.env import load_inference_settings
    from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard

    settings = load_inference_settings()
    return HostGpuGuard(settings.gpu_lock, settings.owner)


@lru_cache(maxsize=1)
def build_inference_gateway() -> "OllamaGateway":
    from garimpei.config.env import load_inference_settings
    from garimpei.infra.gateway.inference.docker_transport import DockerOllamaTransport
    from garimpei.infra.gateway.inference.gpu_probe import NvidiaGpuProbe
    from garimpei.infra.gateway.inference.ollama_gateway import OllamaGateway
    from garimpei.infra.runtime.inference_runtime import recover_inference_service

    config, guard = load_config(require_secrets=False), build_inference_guard()
    return OllamaGateway(
        load_inference_settings(),
        guard,
        lambda: recover_inference_service(config, guard),
        DockerOllamaTransport(config).request,
        NvidiaGpuProbe().measure,
    )


def _defer_inference() -> int:
    return _enqueue("garimpei.local_analysis", "inference", 0)


def build_inference_repository() -> "PostgresInferenceRepository":
    from garimpei.config.env import load_inference_settings
    from garimpei.infra.gateway.inference.quota import LocalQuota
    from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository

    settings = load_inference_settings()
    return PostgresInferenceRepository(
        _defer_inference, settings.queue_limit, settings.lease_seconds, LocalQuota(settings).reserve
    )


def build_request_analysis() -> "RequestAnalysisUseCase":
    from garimpei.usecase.inference.request_analysis_usecase import RequestAnalysisUseCase

    return RequestAnalysisUseCase(build_inference_repository(), build_inference_preparer())


def build_read_analysis() -> "ReadAnalysisUseCase":
    from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
    from garimpei.usecase.inference.read_analysis_usecase import ReadAnalysisUseCase

    return ReadAnalysisUseCase(PostgresInferenceQueries())


def build_run_analysis() -> "RunAnalysisUseCase":
    from django.utils.timezone import now

    from garimpei.usecase.inference.run_analysis_usecase import RunAnalysisUseCase

    return RunAnalysisUseCase(build_inference_repository(), build_inference_gateway(), now)


def _handle_inference() -> None:
    build_run_analysis().execute()


def reconcile_inference() -> None:
    from django.utils.timezone import now

    from garimpei.config.env import load_inference_settings
    from garimpei.infra.persistence.inference_models import InferenceControl

    repository, gateway = build_inference_repository(), build_inference_gateway()
    control = InferenceControl.objects.filter(pk=1).first()
    if control and control.reason in {"execution_unknown", "unload_failed"}:
        repository.recovered(gateway.recover(), now())
        return
    repository.reconcile(now())
    control = InferenceControl.objects.get(pk=1)
    if control.active_request is not None:
        return
    idle = bool(
        control.last_used_at
        and (now() - control.last_used_at).total_seconds() >= load_inference_settings().idle_seconds
    )
    if control.resident and (control.paused or idle):
        repository.unloaded(_unload_local_model(gateway), now())
        return
    diagnostic = gateway.diagnose()
    if diagnostic.get("reason") == "ready" and not diagnostic.get("resident"):
        diagnostic["reason"] = "paused" if control.paused else "idle_unloaded" if idle else "ready"
    repository.record_diagnostic(diagnostic, now())


def _unload_local_model(gateway: "OllamaGateway") -> bool:
    from garimpei.domain.inference.errors import InferenceError

    try:
        return gateway.unload()
    except InferenceError:
        return False


def start_configured_inference() -> str | None:
    from garimpei.config.env import load_inference_settings
    from garimpei.infra.runtime.inference_runtime import start_inference_service

    settings = load_inference_settings()
    if settings.service_enabled:
        return start_inference_service(load_config(), settings, build_inference_guard())
    return None


def build_inference_handler() -> "InferenceHandler":
    from garimpei.infra.http.inference.inference_handler import InferenceHandler
    from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
    from garimpei.usecase.inference.pause_inference_usecase import PauseInferenceUseCase
    from garimpei.usecase.inference.read_status_usecase import ReadStatusUseCase
    from garimpei.usecase.inference.resume_inference_usecase import ResumeInferenceUseCase

    repository = build_inference_repository()
    return InferenceHandler(
        ReadStatusUseCase(PostgresInferenceQueries()),
        PauseInferenceUseCase(repository),
        ResumeInferenceUseCase(repository),
    )


def build_navigation_catalog() -> "Catalog":
    from garimpei.infra.gateway.navigation.catalog_loader import load_catalog

    return load_catalog(Path(__file__).parent / "infra/gateway/navigation/navigation_catalog.json")


def build_navigation_repository(
    settings: ListingSettings | None = None,
) -> "PostgresNavigationRepository":
    from garimpei.config.env import load_navigation_policy
    from garimpei.infra.repository.navigation.postgres_repository import (
        PostgresNavigationRepository,
    )

    settings = settings or _effective_listing_settings()
    return PostgresNavigationRepository(
        _navigation_collection(settings),
        build_read_monitoring_configuration(),
        build_navigation_catalog(),
        load_navigation_policy(),
        _listing_policy(settings),
        _listing_clock(settings),
        _defer_navigation,
    )


def _defer_navigation(attempt: "Attempt", delay: int) -> None:
    _enqueue(
        "garimpei.collect_listings",
        "listing",
        delay,
        cycle_id=str(attempt.cycle_id),
        generation=attempt.generation,
    )


def _navigation_collection(settings: ListingSettings) -> "PostgresCollectionRepository":
    from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository

    return PostgresCollectionRepository(
        build_read_monitoring_configuration(),
        _listing_clock(settings),
        _defer_listing,
        settings.lease,
        scope_transform=build_navigation_catalog().decorate_scope,
    )


def _navigation_task(
    settings: ListingSettings,
    source: "ListingSource",
    geocoding: "Geocoding",
    close: "Callable[[], None] | None" = None,
) -> "ListingTaskHandler":
    from time import monotonic

    from garimpei.config.env import load_navigation_policy
    from garimpei.infra.worker.listing_handler import ListingTaskHandler
    from garimpei.usecase.navigation.run_slice_usecase import RunSliceUseCase

    return ListingTaskHandler(
        RunSliceUseCase(
            _navigation_collection(settings),
            build_navigation_repository(settings),
            source,
            geocoding,
            build_navigation_catalog(),
            load_navigation_policy(),
            monotonic,
            settings.timeout,
            settings.cadence_ms / 1000,
        ),
        close,
    )


def build_navigation_queries() -> "PostgresNavigationQueries":
    from garimpei.config.env import load_navigation_policy
    from garimpei.infra.queries.navigation.postgres_queries import PostgresNavigationQueries

    settings = _effective_listing_settings()
    return PostgresNavigationQueries(
        build_read_monitoring_configuration(),
        _listing_clock(settings),
        load_navigation_policy(),
        settings.timeout,
        settings.cadence_ms / 1000,
    )


def build_read_suggestion() -> "ReadSuggestionUseCase":
    from garimpei.usecase.navigation.read_suggestions_usecase import ReadSuggestionUseCase

    return ReadSuggestionUseCase(build_navigation_queries())


def build_navigation_handler() -> "NavigationHandler":
    from garimpei.infra.http.navigation.navigation_handler import NavigationHandler
    from garimpei.usecase.navigation.read_status_usecase import ReadNavigationStatusUseCase
    from garimpei.usecase.navigation.read_suggestions_usecase import ReadSuggestionsUseCase
    from garimpei.usecase.navigation.resume_work_usecase import ResumeWorkUseCase

    return NavigationHandler(
        ReadNavigationStatusUseCase(build_navigation_queries()),
        ReadSuggestionsUseCase(build_navigation_queries()),
        ResumeWorkUseCase(build_navigation_repository()),
    )


def _handle_navigation_suggestions() -> None:
    from time import monotonic

    from garimpei.config.env import load_navigation_policy
    from garimpei.infra.gateway.listing.cep_geocoding import BrasilApiGeocoding
    from garimpei.infra.gateway.listing.facebook_marketplace import (
        FacebookMarketplace,
        UnavailableMarketplace,
    )
    from garimpei.infra.gateway.listing.fixture_source import FixtureSource
    from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser
    from garimpei.infra.repository.navigation.suggestion_repository import (
        PostgresSuggestionRepository,
    )
    from garimpei.usecase.navigation.run_suggestions_usecase import RunSuggestionsUseCase

    settings = _effective_listing_settings()
    close: Callable[[], None] | None = None
    source: ListingSource
    if settings.fixture_url:
        source = FixtureSource(settings.fixture_url, settings.timeout)
    elif settings.facebook_state is not None or settings.facebook_profile is not None:
        path = settings.facebook_profile or settings.facebook_state
        assert path is not None
        browser = MarketplaceBrowser(
            path, settings.timeout, settings.cadence_ms, profile=settings.facebook_profile
        )
        source = FacebookMarketplace(
            browser, BrasilApiGeocoding(settings.timeout), build_monitoring_catalog().load()
        )
        close = source.close
    else:
        source = UnavailableMarketplace()
    policy = load_navigation_policy()
    store = PostgresSuggestionRepository(
        build_read_monitoring_configuration(),
        build_navigation_catalog(),
        policy,
        _listing_clock(settings),
        settings.timeout,
        settings.cadence_ms / 1000,
    )
    try:
        RunSuggestionsUseCase(
            store, source, policy, monotonic, settings.timeout, settings.cadence_ms / 1000
        ).execute()
    finally:
        if close:
            close()


def reconcile_navigation() -> None:
    from django.db import transaction

    from garimpei.infra.persistence.listing_models import CollectionState
    from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication

    integration = build_integration_repository().read()
    if integration.facebook_mode == "profile" and integration.facebook_phase != "connected":
        return
    with transaction.atomic():
        lock_monitoring_publication()
        if not CollectionState.objects.filter(
            access_suspended=False, current__finished_at__isnull=False
        ).exists():
            return
        _enqueue_navigation_suggestions()


def _enqueue_navigation_suggestions() -> None:
    from django.db import connection, transaction
    from procrastinate.exceptions import AlreadyEnqueued

    register_tasks()
    connection.ensure_connection()
    if not isinstance(connection.connection, Connection):
        raise RuntimeError("Expected psycopg 3 connection for transactional enqueue")
    try:
        with transaction.atomic():
            build_enqueue_app().configure_task(
                name="garimpei.navigation_suggestions",
                queue="listing",
                lock="navigation_suggestions",
                queueing_lock="navigation_suggestions",
                connection=connection.connection,
            ).defer()
    except AlreadyEnqueued:
        return


def build_operational_progress() -> "PostgresOperationalRepository | None":
    from garimpei.config.env import load_operations_settings
    from garimpei.infra.repository.operations.progress_repository import (
        PostgresOperationalRepository,
    )

    settings = load_operations_settings()
    if not settings.enabled:
        return None
    return PostgresOperationalRepository(
        settings.environment_id, _listing_clock(_effective_listing_settings())
    )


def build_operational_status() -> "ReadOperationalStatusUseCase":
    from garimpei.config.env import load_operations_settings
    from garimpei.infra.queries.operations.postgres_queries import PostgresOperationalQueries
    from garimpei.usecase.operations.read_status_usecase import ReadOperationalStatusUseCase

    settings = load_operations_settings()
    return ReadOperationalStatusUseCase(
        PostgresOperationalQueries(
            settings.environment_id,
            settings.recovery_file,
            _listing_clock(_effective_listing_settings()),
            build_read_monitoring_configuration(repeatable_snapshot=True),
        )
    )


def build_backup_repository() -> "PostgresBackupRepository":
    from garimpei.config.env import load_operations_settings
    from garimpei.infra.gateway.operations.archive_gateway import ArchiveGateway
    from garimpei.infra.gateway.operations.snapshot_gateway import BusinessSnapshotGateway
    from garimpei.infra.repository.operations.backup_repository import PostgresBackupRepository
    from garimpei.infra.repository.operations.restore_gateway import RestoreBackupGateway

    settings, config = load_operations_settings(), load_config()
    archive, snapshot = (
        ArchiveGateway(settings.backup_dir, owner=settings.environment_id),
        BusinessSnapshotGateway(),
    )
    restore = RestoreBackupGateway(config, settings.recovery_file, archive, snapshot)
    return PostgresBackupRepository(settings.environment_id, archive, snapshot, restore)


def build_recovery_guard() -> Callable[[], bool]:
    from garimpei.config.env import load_operations_settings
    from garimpei.infra.repository.operations.recovery_guard import dispatch_blocked

    settings = load_operations_settings()
    return lambda: dispatch_blocked(settings.environment_id, settings.recovery_file)


def _handle_operations() -> None:
    build_create_backup().execute(only_due=True)
    build_backup_repository().prune()


def reconcile_operations() -> None:
    from django.db import connection, transaction
    from procrastinate.exceptions import AlreadyEnqueued

    from garimpei.config.env import load_operations_settings

    if not load_operations_settings().enabled:
        return
    register_tasks()
    connection.ensure_connection()
    if not isinstance(connection.connection, Connection):
        raise RuntimeError("Expected psycopg connection for operational enqueue")
    try:
        with transaction.atomic():
            build_enqueue_app().configure_task(
                name="garimpei.operational_maintenance",
                queue="maintenance",
                lock="operational_maintenance",
                queueing_lock="operational_maintenance",
                connection=connection.connection,
            ).defer()
    except AlreadyEnqueued:
        return


def build_operations_handler() -> "OperationsHandler":
    from garimpei.config.env import load_operations_settings
    from garimpei.infra.http.operations.status_handler import OperationsHandler
    from garimpei.infra.repository.operations.progress_repository import (
        PostgresOperationalRepository,
    )
    from garimpei.usecase.operations.export_backup_usecase import ExportBackupUseCase
    from garimpei.usecase.operations.resume_stage_usecase import ResumeStageUseCase

    settings = load_operations_settings()
    repository = PostgresOperationalRepository(
        settings.environment_id, _listing_clock(_effective_listing_settings())
    )
    backups = build_backup_repository()
    return OperationsHandler(
        build_operational_status(),
        ResumeStageUseCase(repository),
        ExportBackupUseCase(backups),
        backups,
    )


def build_create_backup() -> "CreateBackupUseCase":
    from garimpei.usecase.operations.create_backup_usecase import CreateBackupUseCase

    return CreateBackupUseCase(build_backup_repository())


def build_restore_backup() -> "RestoreBackupUseCase":
    from garimpei.usecase.operations.restore_backup_usecase import RestoreBackupUseCase

    return RestoreBackupUseCase(build_backup_repository())


def build_media_store() -> "LocalMediaStore":
    from garimpei.config.env import load_media_settings
    from garimpei.infra.gateway.media.local_store import LocalMediaStore

    settings = load_media_settings()
    return LocalMediaStore(settings.root, settings.policy)


def build_media_repository() -> "PostgresMediaRepository":
    from garimpei.config.env import load_media_settings
    from garimpei.infra.repository.media.postgres_repository import PostgresMediaRepository

    return PostgresMediaRepository(load_media_settings().policy, build_media_store().used_bytes)


def build_media_runner() -> "ObtainMediaUseCase":
    from django.utils import timezone

    from garimpei.config.env import load_media_settings
    from garimpei.infra.gateway.media.image_transport import BoundedImageTransport
    from garimpei.usecase.media.obtain_media_usecase import ObtainMediaUseCase

    settings = load_media_settings()
    return ObtainMediaUseCase(
        build_media_repository(),
        BoundedImageTransport(settings.policy, settings.eval_origin),
        build_media_store(),
        timezone.now,
    )


def build_media_handler() -> "MediaHandler":
    from django.utils import timezone

    from garimpei.infra.http.media.media_handler import MediaHandler
    from garimpei.infra.queries.media.postgres_queries import PostgresMediaQueries
    from garimpei.usecase.media.request_recovery_usecase import RequestMediaRecoveryUseCase

    return MediaHandler(
        PostgresMediaQueries(),
        build_media_store(),
        RequestMediaRecoveryUseCase(build_media_repository(), timezone.now),
    )


def _handle_media(job_id: str) -> None:
    build_media_runner().execute(UUID(job_id))


def reconcile_media() -> None:
    from django.utils import timezone

    from garimpei.usecase.media.clean_media_usecase import CleanMediaUseCase

    repository = build_media_repository()
    now = timezone.now()
    repository.backfill(now)
    for identity in repository.due(now):
        _enqueue("garimpei.media", "media", 0, job_id=str(identity))
    CleanMediaUseCase(repository, build_media_store(), timezone.now).execute()


if TYPE_CHECKING:
    from garimpei.infra.gateway.media.local_store import LocalMediaStore
    from garimpei.infra.http.media.media_handler import MediaHandler
    from garimpei.infra.repository.media.postgres_repository import PostgresMediaRepository
    from garimpei.usecase.media.obtain_media_usecase import ObtainMediaUseCase

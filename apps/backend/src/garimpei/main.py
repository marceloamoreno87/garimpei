from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from garimpei.config.env import AlertSettings
    from garimpei.domain.alert.alert import AlertPolicy
    from garimpei.domain.listing.ports import Clock, CollectionPolicy
    from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser
    from garimpei.infra.gateway.monitoring.facebook_catalog import FacebookCategoryCatalog
    from garimpei.infra.http.integration.integration_handler import IntegrationHandler
    from garimpei.infra.http.listing.condition_handler import ConditionHandler
    from garimpei.infra.http.listing.exploration_handler import ExplorationHandler
    from garimpei.infra.http.monitoring.monitoring_handler import MonitoringHandler
    from garimpei.infra.queries.listing.condition_queries import PostgresConditionQueries
    from garimpei.infra.queries.monitoring.postgres_queries import PostgresMonitoringQueries
    from garimpei.infra.repository.alert.postgres_repository import PostgresAlertRepository
    from garimpei.infra.repository.integration.facebook_profile_repository import (
        PostgresFacebookProfileRepository,
    )
    from garimpei.infra.repository.integration.postgres_repository import (
        PostgresIntegrationRepository,
    )
    from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository
    from garimpei.infra.repository.valuation.postgres_repository import PostgresValuationRepository
    from garimpei.infra.worker.alert_handler import AlertTaskHandler
    from garimpei.infra.worker.facebook_login_handler import FacebookLoginHandler
    from garimpei.infra.worker.listing_handler import ListingTaskHandler
    from garimpei.infra.worker.valuation_handler import ValuationTaskHandler
    from garimpei.usecase.listing.classify_condition_usecase import ClassifyConditionUseCase
    from garimpei.usecase.listing.publish_exploration_usecase import PublishExplorationUseCase
    from garimpei.usecase.listing.read_collection_status_usecase import ReadCollectionStatusUseCase
    from garimpei.usecase.listing.read_condition_usecase import ReadConditionUseCase
    from garimpei.usecase.listing.read_listing_changes_usecase import ReadListingChangesUseCase
    from garimpei.usecase.listing.read_listing_usecase import ReadListingUseCase
    from garimpei.usecase.monitoring.read_configuration_usecase import (
        ReadMonitoringConfigurationUseCase,
    )
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

    app.task(name="garimpei.alert_tick", queue="alert")(_handle_alert)
    app.task(name="garimpei.runtime_probe", queue="runtime")(_handle_runtime_probe)
    app.task(name="garimpei.collect_listings", queue="listing")(_handle_listing)
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
    from garimpei.infra.worker.listing_handler import ListingTaskHandler
    from garimpei.usecase.listing.collect_listings_usecase import CollectListingsUseCase

    settings = _effective_listing_settings()
    store, policy = _collection_store(settings), _listing_policy(settings)
    if settings.fixture_url is not None:
        fixture = FixtureSource(settings.fixture_url, settings.timeout)
        return ListingTaskHandler(CollectListingsUseCase(store, fixture, fixture, policy))
    if settings.facebook_state is not None or settings.facebook_profile is not None:
        return _build_live_listing_handler(settings)
    unavailable = UnavailableMarketplace()
    return ListingTaskHandler(CollectListingsUseCase(store, unavailable, unavailable, policy))


def _build_live_listing_handler(settings: ListingSettings) -> "ListingTaskHandler":
    from garimpei.infra.gateway.listing.cep_geocoding import BrasilApiGeocoding
    from garimpei.infra.gateway.listing.facebook_marketplace import FacebookMarketplace
    from garimpei.infra.gateway.listing.marketplace_browser import MarketplaceBrowser
    from garimpei.infra.worker.listing_handler import ListingTaskHandler
    from garimpei.usecase.listing.collect_listings_usecase import CollectListingsUseCase

    path = settings.facebook_profile or settings.facebook_state
    assert path is not None
    browser = MarketplaceBrowser(
        path, settings.timeout, settings.cadence_ms, profile=settings.facebook_profile
    )
    geocoding = BrasilApiGeocoding(settings.timeout)
    source = FacebookMarketplace(browser, geocoding, build_monitoring_catalog().load())
    return ListingTaskHandler(
        CollectListingsUseCase(
            _collection_store(settings), source, geocoding, _listing_policy(settings)
        ),
        source.close,
    )


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


def build_monitoring_queries() -> "PostgresMonitoringQueries":
    from garimpei.infra.queries.monitoring.postgres_queries import PostgresMonitoringQueries
    from garimpei.infra.repository.monitoring.postgres_repository import (
        PostgresMonitoringRepository,
    )

    return PostgresMonitoringQueries(PostgresMonitoringRepository())


def build_monitoring_catalog() -> "FacebookCategoryCatalog":
    from garimpei.config.env import load_catalog_fixture
    from garimpei.infra.gateway.monitoring.facebook_catalog import FacebookCategoryCatalog

    return FacebookCategoryCatalog(
        load_catalog_fixture()
        or Path(__file__).parent / "infra/gateway/monitoring/facebook_categories.json"
    )


def build_read_monitoring_configuration() -> "ReadMonitoringConfigurationUseCase":
    from garimpei.usecase.monitoring.read_configuration_usecase import (
        ReadMonitoringConfigurationUseCase,
    )

    return ReadMonitoringConfigurationUseCase(build_monitoring_queries())


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

    return PostgresValuationRepository(_defer_valuation)


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
                build_read_monitoring_configuration(), PostgresValuationQueries(), labels
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
    )


def _exploration_worker_active() -> bool:
    return WorkerProbe(load_config()).check()


def build_alert_store() -> "PostgresAlertRepository":
    from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
    from garimpei.infra.repository.alert.postgres_repository import PostgresAlertRepository

    return PostgresAlertRepository(
        build_read_monitoring_configuration(), PostgresListingQueries(), _alert_policy()
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
    from garimpei.usecase.alert.consume_listing_events_usecase import ConsumeListingEventsUseCase
    from garimpei.usecase.alert.evaluate_alert_usecase import EvaluateAlertUseCase
    from garimpei.usecase.alert.reconcile_alert_usecase import ReconcileAlertUseCase
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
    from garimpei.infra.persistence.listing_models import ListingEvent
    from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication

    now = timezone.now()
    with transaction.atomic():
        lock_monitoring_publication()
        if not ListingEvent.objects.exists():
            return
        cursor, _ = AlertFeedCursor.objects.select_for_update().get_or_create(installation="local")
        if recovery:
            AlertIntent.objects.filter(state="review").update(
                state="uncertain", next_action=_listing_clock(load_listing_settings())()
            )
        if cursor.next_tick and cursor.next_tick > now:
            return
        for stage in ("ingest", "evaluate", "reconcile", "send"):
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

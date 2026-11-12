"""F03 scenarios restricted to the disposable instance selected by its private env file."""

import json
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.core.wsgi import get_wsgi_application
from django.db import DatabaseError

from garimpei.config.env import load_config
from garimpei.domain.monitoring.configuration import MonitoringConfiguration
from garimpei.domain.monitoring.errors import CatalogUnavailable
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.domain.monitoring.values import CategoryCatalog
from garimpei.infra.gateway.monitoring.facebook_catalog import FacebookCategoryCatalog
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration as Row
from garimpei.infra.repository.monitoring.postgres_repository import PostgresMonitoringRepository
from garimpei.main import (
    build_monitoring_catalog,
    build_monitoring_handler,
    build_monitoring_queries,
    build_read_monitoring_configuration,
)
from garimpei.usecase.monitoring.save_step_usecase import StepInput


def require_disposable() -> None:
    config = load_config()
    manifest = json.loads((config.directory / "manifest.json").read_text())
    if config.environment != "eval" or not manifest["disposable"]:
        raise RuntimeError("F03 fixtures require an owned disposable eval instance")
    database = settings.DATABASES["default"]
    if database["NAME"] != config.database or int(database["PORT"]) != config.pg_port:
        raise RuntimeError("F03 fixtures require the eval instance database")


def prepare_state(name: str) -> MonitoringSnapshot:
    require_disposable()
    if name not in {"NOVO", "RASCUNHO", "ATIVA"}:
        raise ValueError("Expected NOVO, RASCUNHO or ATIVA")
    Row.objects.all().delete()
    if name == "NOVO":
        return build_read_monitoring_configuration().execute()
    handler = build_monitoring_handler()
    # Factories drive the same injected usecases as HTTP; no cost/default seed exists in runtime.
    handler._save_step.execute(StepInput("regiao", 0, cep="01001000"))
    handler._save_step.execute(
        StepInput("custos", 1, shipping_estimate="25.50", resale_fee_percent="12.50")
    )
    category_id = build_monitoring_catalog().load().entries[0].id
    categories = (category_id,) if name == "ATIVA" else ()
    handler._save_step.execute(
        StepInput("interesses", 2, category_ids=categories, product_names=("PlayStation 5",))
    )
    if name == "ATIVA":
        handler._complete.execute(
            StepInput("interesses", 3, category_ids=categories, product_names=("PlayStation 5",))
        )
    elif name != "RASCUNHO":
        raise ValueError("Expected NOVO, RASCUNHO or ATIVA")
    snapshot = build_read_monitoring_configuration().execute()
    if name == "ATIVA":
        assert snapshot.configured and snapshot.configuration_id is not None
        assert snapshot.pickup_city == "São Paulo" and snapshot.pickup_state == "SP"
        assert snapshot.pickup_radius_km == 20 and snapshot.shipping_scope == "BR"
        assert snapshot.shipping_estimate == Decimal("25.50")
    return snapshot


def state_record() -> dict[str, object]:
    form = build_monitoring_queries().read_form()
    return {
        "form_id": str(form.id) if form else None,
        "form_revision": form.revision if form else 0,
        "public": repr(build_read_monitoring_configuration().execute()),
    }


def failure_application(kind: str) -> WSGIHandler:
    """Launch only in a separate, owned Gunicorn process; no failure route is installed."""
    require_disposable()
    if kind == "catalog":
        patch.object(FacebookCategoryCatalog, "load", fail_catalog).start()
    elif kind == "save":
        patch.object(PostgresMonitoringRepository, "save", fail_after_save).start()
    else:
        raise ValueError("Expected catalog or save")
    return get_wsgi_application()


def fail_catalog(_gateway: FacebookCategoryCatalog) -> CategoryCatalog:
    raise CatalogUnavailable()


_original_save = PostgresMonitoringRepository.save


def fail_after_save(
    repository: PostgresMonitoringRepository, state: MonitoringConfiguration
) -> None:
    _original_save(repository, state)
    raise DatabaseError("controlled transaction failure")

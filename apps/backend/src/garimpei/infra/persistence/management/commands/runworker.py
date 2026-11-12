import logging
import time
from argparse import ArgumentParser
from contextlib import redirect_stderr
from pathlib import Path
from threading import Event, Thread
from typing import TypedDict, Unpack

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections

from garimpei.domain.monitoring.errors import ConfigurationReadFailed
from garimpei.main import (
    build_facebook_login_handler,
    build_publish_exploration,
    build_worker_stderr,
    reconcile_alerts,
    reconcile_inference,
    reconcile_listings,
    reconcile_media,
    reconcile_navigation,
    reconcile_operations,
    reconcile_valuations,
    register_tasks,
)

logger = logging.getLogger(__name__)


class WorkerOptions(TypedDict):
    concurrency: int
    queue_group: str | None


def _reconcile_until_stopped(stopped: Event) -> None:
    recover_access = True
    while not stopped.is_set():
        try:
            build_facebook_login_handler().execute()
            reconcile_listings(recover_access=recover_access)
            reconcile_navigation()
        except ConfigurationReadFailed:
            logger.warning(
                "collection_configuration_read_failed",
                extra={
                    "event": "collection_reconcile_failed",
                    "error_code": "CONFIGURATION_READ_FAILED",
                },
            )
        except Exception:
            logger.exception(
                "collection_reconcile_failed", extra={"event": "collection_reconcile_failed"}
            )
        else:
            recover_access = False
        finally:
            connections.close_all()
        stopped.wait(2)


def _alerts_until_stopped(stopped: Event) -> None:
    recovery = True
    while not stopped.is_set():
        try:
            reconcile_alerts(recovery=recovery)
        except Exception:
            logger.error(
                "alert_schedule_failed",
                extra={"event": "alert_schedule_failed", "error_code": "ALERT_HISTORY_UNAVAILABLE"},
            )
        else:
            recovery = False
        finally:
            connections.close_all()
        stopped.wait(2)


def _publish_when_due(publication_at: float, interval: int) -> float:
    if time.monotonic() < publication_at:
        return publication_at
    build_publish_exploration().execute()
    return time.monotonic() + interval


class Command(BaseCommand):
    help = "Run the separately supervised PostgreSQL worker and reconcile the collection schedule."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--concurrency", type=int, default=3)
        parser.add_argument(
            "--queue-group",
            choices=[
                "runtime",
                "listing",
                "valuation",
                "alert",
                "inference",
                "maintenance",
                "media",
            ],
        )

    def handle(self, *_args: str, **options: Unpack[WorkerOptions]) -> None:
        from garimpei.infra.worker.reserved_consumers import supervise

        register_tasks()
        if options["queue_group"]:
            with redirect_stderr(build_worker_stderr()):
                call_command(
                    "procrastinate",
                    "worker",
                    "--queues",
                    options["queue_group"],
                    "--concurrency",
                    "1",
                    "--shutdown-graceful-timeout",
                    "5",
                )
            return
        stopped = Event()
        targets = (
            _reconcile_until_stopped,
            _alerts_until_stopped,
            _inference_until_stopped,
            _valuations_until_stopped,
            _publication_until_stopped,
            _operations_until_stopped,
            _media_until_stopped,
        )
        reconcilers = [Thread(target=target, args=(stopped,), daemon=True) for target in targets]
        for reconciler in reconcilers:
            reconciler.start()
        try:
            supervise(stopped, Path(__file__).resolve().parents[6])
        finally:
            stopped.set()
            for reconciler in reconcilers:
                reconciler.join(timeout=2)
            build_facebook_login_handler().close()


def _inference_until_stopped(stopped: Event) -> None:
    while not stopped.is_set():
        try:
            reconcile_inference()
        except Exception:
            logger.error(
                "inference_reconcile_failed", extra={"event": "inference_reconcile_failed"}
            )
        finally:
            connections.close_all()
        stopped.wait(5)


def _valuations_until_stopped(stopped: Event) -> None:
    _independent(stopped, reconcile_valuations, "valuation_reconcile_failed")


def _publication_until_stopped(stopped: Event) -> None:
    from garimpei.config.env import load_exploration_settings

    due = 0.0

    def publish() -> None:
        nonlocal due
        due = _publish_when_due(due, load_exploration_settings().interval)

    _independent(stopped, publish, "exploration_publication_failed")


def _operations_until_stopped(stopped: Event) -> None:
    _independent(stopped, reconcile_operations, "operations_reconcile_failed")


def _independent(stopped: Event, operation: "Callable[[], None]", event: str) -> None:
    while not stopped.is_set():
        try:
            operation()
        except Exception:
            logger.error(event, extra={"event": event})
        finally:
            connections.close_all()
        stopped.wait(5)


from collections.abc import Callable  # noqa: E402


def _media_until_stopped(stopped: Event) -> None:
    while not stopped.is_set():
        try:
            reconcile_media()
        except Exception:
            logger.error("media_reconcile_failed", extra={"event": "media_reconcile_failed"})
        finally:
            connections.close_all()
        stopped.wait(30)

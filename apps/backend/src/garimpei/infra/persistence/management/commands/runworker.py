import logging
import time
from argparse import ArgumentParser
from contextlib import redirect_stderr
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
    reconcile_assessments,
    reconcile_inference,
    reconcile_listings,
    reconcile_media,
    reconcile_navigation,
    reconcile_valuations,
    register_tasks,
)

logger = logging.getLogger(__name__)


class WorkerOptions(TypedDict):
    concurrency: int


def _reconcile_until_stopped(stopped: Event) -> None:
    from garimpei.config.env import load_exploration_settings

    interval = load_exploration_settings().interval
    publication_at = 0.0
    recover_access = True
    while not stopped.is_set():
        try:
            build_facebook_login_handler().execute()
            reconcile_listings(recover_access=recover_access)
            reconcile_navigation()
            reconcile_valuations()
            publication_at = _publish_when_due(publication_at, interval)
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

    def handle(self, *_args: str, **options: Unpack[WorkerOptions]) -> None:
        register_tasks()
        stopped = Event()
        reconciler = Thread(target=_reconcile_until_stopped, args=(stopped,), daemon=True)
        reconciler.start()
        alerts = Thread(target=_alerts_until_stopped, args=(stopped,), daemon=True)
        alerts.start()
        inference = Thread(target=_inference_until_stopped, args=(stopped,), daemon=True)
        inference.start()
        media = Thread(target=_media_until_stopped, args=(stopped,), daemon=True)
        media.start()
        assessments = Thread(target=_assessments_until_stopped, args=(stopped,), daemon=True)
        assessments.start()
        try:
            with redirect_stderr(build_worker_stderr()):
                call_command(
                    "procrastinate",
                    "worker",
                    "--queues",
                    "runtime,listing,valuation,alert,inference,media",
                    "--concurrency",
                    str(max(4, options["concurrency"] + 1)),
                    "--shutdown-graceful-timeout",
                    "20",
                )
        finally:
            stopped.set()
            reconciler.join(timeout=2)
            alerts.join(timeout=2)
            inference.join(timeout=2)
            media.join(timeout=2)
            assessments.join(timeout=2)
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


def _media_until_stopped(stopped: Event) -> None:
    while not stopped.is_set():
        try:
            reconcile_media()
        except Exception:
            logger.error("media_reconcile_failed", extra={"event": "media_reconcile_failed"})
        finally:
            connections.close_all()
        stopped.wait(30)


def _assessments_until_stopped(stopped: Event) -> None:
    while not stopped.is_set():
        try:
            reconcile_assessments()
        except Exception:
            logger.error(
                "assessment_reconcile_failed", extra={"event": "assessment_reconcile_failed"}
            )
        finally:
            connections.close_all()
        stopped.wait(5)

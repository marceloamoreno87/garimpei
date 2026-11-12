import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from tests.factories.alert import WahaServer, serve_waha
from tests.factories.listing import ControlledClock, serve
from tests.factories.runtime import FoundationInstance
from tests.factories.runtime import pause_worker as pause_worker
from tests.factories.runtime import resume_worker as resume_worker
from tests.factories.valuation import (
    ValuationSource,
    listing,
    prepare_valuation_instance,
    wait_valuation,
)
from tests.integration.test_collection import command, completed, configure, sql, wait_for

type AlertScenario = tuple[FoundationInstance, ValuationSource, ControlledClock, WahaServer]


@contextmanager
def alert_scenario(private: Path, *, enabled: bool = True) -> Iterator[AlertScenario]:
    source, channel = ValuationSource(), WahaServer()
    source.rows["699"]["description"] = "Com defeito. Não funciona."
    with serve(source) as url, serve_waha(channel) as waha:
        instance, clock = prepare_valuation_instance(
            Path(__file__).resolve().parents[4], private, url
        )
        with instance.private_file.open("a") as file:
            file.write(
                f"GARIMPEI_ALERTS_ENABLED={str(enabled).lower()}\n"
                f"GARIMPEI_ALERT_FIXTURE_URL={waha}\nGARIMPEI_WAHA_SESSION=synthetic\n"
                "GARIMPEI_WAHA_RECIPIENT=100@c.us\nGARIMPEI_WAHA_ACCOUNT=200@c.us\n"
            )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            configure(instance)
            completed(instance, 1)
            wait_valuation(instance, price="2300.00")
            yield instance, source, clock, channel
        except BaseException:
            print(
                "F09 diagnostic decisions",
                sql(
                    instance,
                    "SELECT state,reason,count(*) FROM runtime_alerteventdecision GROUP BY state,reason",
                ),
            )
            print(
                "F09 diagnostic intents",
                sql(
                    instance,
                    "SELECT state,reason,count(*) FROM runtime_alertintent GROUP BY state,reason",
                ),
            )
            raise
        finally:
            source.release.set()
            command(instance, "./scripts/stop.sh", "--clean")


def add_cases(source: ValuationSource, clock: ControlledClock) -> None:
    clock.advance(1)
    cases = json.loads((Path(__file__).parents[1] / "fixtures/alert/cases.json").read_text())[
        "offers"
    ]
    for identity, case in cases.items():
        source.rows[identity] = listing(
            identity,
            case["price"],
            published_at=clock.value.isoformat(),
            delivery=True,
            delivery_cep="01001000",
            pickup=False,
            **{key: value for key, value in case.items() if key not in {"price", "expected"}},
        )


def alert_shell(instance: FoundationInstance, code: str) -> None:
    result = instance.shell(
        """
from datetime import timedelta
from decimal import Decimal
from uuid import UUID
from django.db import transaction
from django.utils import timezone
from garimpei.main import build_alert_store,build_alert_handler,build_read_profit,build_read_condition,build_classify_condition
from garimpei.infra.persistence.alert_models import AlertFeedCursor,AlertEventDecision,AlertIntent,AlertAttempt,ManualConditionHistory
from garimpei.infra.persistence.listing_models import Listing,ListingEvent
from garimpei.domain.alert.alert import Binding,Outcome,Receipt
from garimpei.config.env import load_listing_settings
from garimpei.main import _listing_clock
clock=_listing_clock(load_listing_settings())
store=build_alert_store()
binding=Binding('synthetic','100@c.us','200@c.us')
def target(key='903'): return Listing.objects.get(external_id=key)
def decision(key='903'): return AlertEventDecision.objects.get(event__listing=target(key),event__kind='discovered')
def intent(key='903'): return AlertIntent.objects.get(decision=decision(key))
"""
        + code
    )
    assert result.returncode == 0, result.stdout + result.stderr
    print(result.stdout, end="")


def wait_alerts(instance: FoundationInstance, count: int, clock: ControlledClock) -> None:
    next_advance = time.monotonic() + 6

    def confirmed() -> bool:
        nonlocal next_advance
        if time.monotonic() >= next_advance:
            clock.advance(6)
            next_advance = time.monotonic() + 6
        return sql(
            instance, "SELECT count(*) FROM runtime_alertintent WHERE state='confirmed'"
        ) == [(count,)]

    wait_for(confirmed, f"{count} confirmed alerts", seconds=35)

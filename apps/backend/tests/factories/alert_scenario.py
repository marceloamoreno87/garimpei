import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from tests.factories.alert import WahaServer, serve_waha
from tests.factories.listing import ControlledClock, serve
from tests.factories.runtime import FoundationInstance
from tests.factories.runtime import pause_worker as pause_worker
from tests.factories.runtime import resume_worker as resume_worker
from tests.factories.valuation import (
    FIXED,
    ValuationSource,
    listing,
    prepare_valuation_instance,
    wait_valuation,
)
from tests.integration.test_collection import command, completed, configure, sql, wait_for

type AlertScenario = tuple[FoundationInstance, ValuationSource, ControlledClock, WahaServer]


class HistoricalAlertSource(ValuationSource):
    """Known comparator stock has an expired absolute publication in its detail."""

    def respond(self, path: str, parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
        status, body = super().respond(path, parameters)
        baseline = {
            "600",
            "601",
            "602",
            "603",
            "604",
            "699",
            "610",
            "611",
            "612",
            "613",
            "614",
            "616",
        }
        if path.startswith("/detail/") and path.removeprefix("/detail/") in baseline:
            return status, body | {
                "published_at": (datetime.fromisoformat(FIXED) - timedelta(days=3)).isoformat()
            }
        return status, body


def seed_historical_comparators(instance: FoundationInstance, source: ValuationSource) -> None:
    from tests.integration.test_collection import shell

    # Known expired stock remains available to valuation without unrelated first alerts.
    published = (datetime.fromisoformat(FIXED) - timedelta(days=3)).isoformat()
    shell(
        instance,
        "from datetime import datetime; from garimpei.infra.persistence.listing_models import Listing; "
        + repr(list(source.rows))
        + "; "
        + "\n".join(
            f"Listing.objects.create(source='facebook_marketplace',external_id={identity!r},canonical_url='https://www.facebook.com/marketplace/item/{identity}/',first_seen_at=datetime.fromisoformat({published!r}),origin='initial')"
            for identity in source.rows
        ),
    )


@contextmanager
def alert_scenario(private: Path, *, enabled: bool = True) -> Iterator[AlertScenario]:
    source, channel = HistoricalAlertSource(), WahaServer()
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
            seed_historical_comparators(instance, source)
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
from garimpei.main import build_alert_store,build_first_alert_store,build_alert_handler,build_read_profit,build_read_condition,build_classify_condition
from garimpei.infra.persistence.alert_models import AlertFeedCursor,AlertEventDecision,AlertIntent,AlertAttempt,ManualConditionHistory,FirstAlertIdentity,FirstEligibilityDecision,FirstAlertInventory
from garimpei.infra.persistence.listing_models import Listing,ListingEvent
from garimpei.domain.alert.alert import Binding,Outcome,Receipt
from garimpei.config.env import load_listing_settings
from garimpei.main import _listing_clock
clock=_listing_clock(load_listing_settings())
store=build_alert_store()
binding=Binding('synthetic','100@c.us','200@c.us')
def target(key='903'): return Listing.objects.get(external_id=key)
def decision(key='903'): return AlertEventDecision.objects.get(event__listing=target(key),event__kind='discovered')
def first_state(key='903'): return FirstAlertIdentity.objects.get(listing=target(key))
def first_decision(key='903'): return first_state(key).decisions.latest('generation')
def prepare_first(key='903', at=None):
    listing=target(key);now=at or clock();repository=build_first_alert_store();repository.adopt(now)
    repository.publish(listing.id,repository.prepare(listing.id),build_read_profit().execute(listing.id,event=False),now)
def intent(key='903'):
    row=first_state(key)
    return row.intent if row.intent_id else AlertIntent.objects.get(decision=decision(key))
def financial_decision(row): return row.first_decision if row.first_decision_id else row.decision
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


def wait_listing_alerts(
    instance: FoundationInstance, key: str, count: int, clock: ControlledClock
) -> None:
    next_advance = time.monotonic() + 6

    def confirmed() -> bool:
        nonlocal next_advance
        if time.monotonic() >= next_advance:
            clock.advance(6)
            next_advance = time.monotonic() + 6
        return sql(
            instance,
            "SELECT count(*) FROM runtime_alertintent i LEFT JOIN runtime_firsteligibilitydecision f ON f.id=i.first_decision_id LEFT JOIN runtime_firstalertidentity a ON a.id=f.identity_id LEFT JOIN runtime_alerteventdecision d ON d.id=i.decision_id LEFT JOIN runtime_listingevent e ON e.id=d.event_id JOIN runtime_listing l ON l.id=COALESCE(a.listing_id,e.listing_id) WHERE i.state='confirmed' AND l.external_id='"
            + key
            + "'",
        ) == [(count,)]

    wait_for(confirmed, f"{count} confirmed alerts for {key}", seconds=35)

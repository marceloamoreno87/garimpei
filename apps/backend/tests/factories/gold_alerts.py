"""Controlled F21 corpus. Synthetic expectations are never labelled human review."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast

from garimpei.infra.persistence.alert_models import AlertAttempt, AlertIntent, FirstAlertIdentity
from garimpei.infra.persistence.gold_models import GoldPolicyAdoption, GoldQualification
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.valuation_models import ValuationWork
from garimpei.main import (
    build_alert_handler,
    build_publish_exploration,
    build_qualify_gold_alert,
    build_valuation_handler,
    reconcile_valuations,
)
from tests.factories.alert import WahaServer
from tests.factories.assessment_lab_actions import AssessmentLab
from tests.factories.valuation import listing


def gold_cases() -> dict[str, object]:
    raw = json.loads((Path(__file__).parents[1] / "fixtures/alert/gold_cases.json").read_text())
    assert raw["schema_version"] == 1 and len(raw["comparable_prices"]) == 5
    assert raw["reference_method"] == "controlled_synthetic_expectations"
    assert Decimal(raw["fee_percent"]) == 10
    assert datetime.fromisoformat(raw["now"]).tzinfo is not None
    assert len(raw["cases"]) >= 18
    return cast(dict[str, object], raw)


def gold_rows(case: str, origin: str) -> dict[str, dict[str, object]]:
    corpus = gold_cases()
    cases = cast(dict[str, dict[str, object]], corpus["cases"])
    selected = cases[case]
    observed = datetime.fromisoformat(str(corpus["now"]))
    target = str(corpus["target"])
    rows = {
        target: listing(
            target,
            str(selected.get("purchase", "1900,00")),
            title=selected.get("title", corpus["title"]),
            description=selected.get("description", corpus["description"]),
            published_at=(observed - timedelta(hours=1)).isoformat(),
        ),
    }
    prices = cast(list[str], selected.get("comparable_prices", corpus["comparable_prices"]))
    for index, price in enumerate(prices, 2):
        key = str(21000 + index)
        rows[key] = listing(
            key,
            price,
            title=corpus["title"],
            description=corpus["description"],
            published_at=(observed - timedelta(hours=2)).isoformat(),
        )
    if selected.get("last_comparable_defect"):
        rows["21006"]["description"] = "Não funciona. Com defeito."
    rows[target]["media"] = dict(
        presence="present" if selected.get("photos", True) else "none",
        complete=True,
        reason="",
        photos=[
            dict(
                key="gold-photo",
                primary=True,
                correlated=True,
                variants=[
                    dict(url=origin + "/" + str(corpus["synthetic_photo"]), width=640, height=480)
                ],
            )
        ]
        if selected.get("photos", True)
        else [],
    )
    return rows


@dataclass
class GoldLab:
    assessment: AssessmentLab
    channel: WahaServer
    case: str = ""

    def prepare(self, case: str) -> dict[str, object]:
        from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
        from garimpei.infra.repository.alert.gold_adoption import adopt_gold_policy

        self.case = case
        corpus = gold_cases()
        self.assessment.clock.value = datetime.fromisoformat(str(corpus["now"]))
        self.assessment.clock.advance(0)
        self.assessment.source.rows = gold_rows(case, self.assessment.origin)
        MonitoringConfiguration.objects.filter(slot="active").update(
            resale_fee_percent=Decimal("10")
        )
        adopt_gold_policy(self.assessment.clock.value)
        self.assessment.collect()
        selected = cast(dict[str, dict[str, object]], corpus["cases"])[case]
        self.assessment.context.gateway.fault = cast(str | None, selected.get("analysis_fault"))
        if selected.get("complete_analysis", True):
            self.assessment.complete(str(selected.get("finding", "light_wear")))
        reconcile_valuations()
        for work in ValuationWork.objects.filter(completed=False):
            build_valuation_handler().execute(work.id)
        days = int(str(selected.get("advance_days", 0)))
        self.assessment.clock.advance(days * 86400)
        self.refresh()
        return self.status()

    def refresh(self) -> None:
        for stage in ("adopt", "refresh", "ingest", "evaluate"):
            build_alert_handler(stage).execute()
        build_publish_exploration().execute()

    def status(self) -> dict[str, object]:
        target = Listing.objects.filter(external_id="21001").first()
        row = FirstAlertIdentity.objects.filter(listing=target).first() if target else None
        return dict(
            ready=True,
            case=self.case,
            runtime="controlled_fake",
            real_whatsapp_posts=0,
            url=f"http://127.0.0.1:{self.assessment.instance.config.web_port}",
            listing=str(target.id) if target else None,
            observation=str(target.latest_id) if target else None,
            policy=list(GoldPolicyAdoption.objects.values("state", "policy", "inventory")),
            qualifications=list(
                GoldQualification.objects.filter(listing=target).values(
                    "id",
                    "state",
                    "reason",
                    "reasons",
                    "input_fingerprint",
                    "valid_until",
                )
            ),
            first_state=row.state if row else None,
            first_reason=row.reason if row else None,
            intents=list(
                AlertIntent.objects.values(
                    "id", "state", "reason", "gold_qualification_id", "body", "confirmed_message"
                )
            ),
            attempts=AlertAttempt.objects.count(),
            messages=self.channel.messages.copy(),
        )

    def mutate(self, payload: dict[str, object]) -> None:
        external = str(payload.get("external_id", "21001"))
        field = str(payload["field"])
        if field not in {"price", "title", "description", "condition", "source_available"}:
            raise ValueError("gold mutation field: expected a listing evidence field")
        self.assessment.source.rows[external][field] = payload["value"]
        self.assessment.collect()

    def revalue(self) -> None:
        reconcile_valuations()
        for work in ValuationWork.objects.filter(completed=False):
            build_valuation_handler().execute(work.id)

    def action(self, payload: dict[str, object]) -> dict[str, object]:
        action = str(payload.get("action", "status"))
        if action == "prepare":
            return self.prepare(str(payload.get("case", "BASE")))
        if action == "mutate":
            self.mutate(payload)
        elif action == "revalue":
            self.revalue()
        elif action == "complete":
            self.assessment.complete(str(payload.get("finding", "light_wear")))
        elif action == "send":
            build_alert_handler("send").execute()
        elif action == "refresh":
            self.refresh()
        elif action == "qualify":
            target = Listing.objects.get(external_id="21001")
            build_qualify_gold_alert().execute(target.id)
        elif action == "advance":
            self.assessment.clock.advance(int(str(payload["seconds"])))
        elif action == "status":
            pass
        else:
            raise ValueError(
                "gold action: expected prepare, send, refresh, qualify, advance, status"
            )
        return self.status()

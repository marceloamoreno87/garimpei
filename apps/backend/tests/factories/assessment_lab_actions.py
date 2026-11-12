import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID

from django.db import connections
from django.utils.timezone import now

from garimpei.infra.persistence.alert_models import AlertAttempt, AlertIntent
from garimpei.infra.persistence.assessment_models import AssessmentHead, ConditionAssessment
from garimpei.infra.persistence.inference_models import InferenceControl, InferenceRequest
from garimpei.infra.persistence.listing_models import CollectionState, Listing
from garimpei.main import (
    build_listing_task_handler,
    build_media_repository,
    build_media_runner,
    build_publish_exploration,
    build_read_condition,
    reconcile_listings,
)
from tests.factories.assessment import AssessmentContext, assessment_context
from tests.factories.listing import ControlledClock
from tests.factories.monitoring import require_disposable
from tests.factories.runtime import FoundationInstance, pause_worker, resume_worker
from tests.factories.valuation import ValuationSource


@dataclass
class AssessmentLab:
    instance: FoundationInstance
    source: ValuationSource
    clock: ControlledClock
    origin: str
    context: AssessmentContext
    paused_group: int
    cases: dict[str, str]

    def status(self) -> dict[str, object]:
        require_disposable()
        rows = []
        for listing in Listing.objects.exclude(latest=None):
            state = build_read_condition().execute(listing.id).state
            rows.append(
                dict(
                    id=str(listing.id),
                    external_id=listing.external_id,
                    observation=str(listing.latest_id),
                    tab=state.tab,
                    manual=state.manual,
                    revision=state.revision,
                    automatic=state.analysis.condition,
                    sufficient=state.satisfies_alert_condition,
                    assessment=state.assessment.id if state.assessment else None,
                    assessment_reason=state.assessment.reason if state.assessment else None,
                )
            )
        return dict(
            ready=True,
            url=f"http://127.0.0.1:{self.instance.config.web_port}",
            runtime="controlled_fake",
            cases=self.cases,
            offers=rows,
            heads=list(AssessmentHead.objects.values("listing_id", "generation", "current_id")),
            analyses=list(
                ConditionAssessment.objects.values(
                    "id", "status", "condition", "sufficient", "input_fingerprint", "model_revision"
                )
            ),
            inference_requests=InferenceRequest.objects.count(),
            model_calls=self.context.gateway.calls,
            alert_intents=AlertIntent.objects.count(),
            transmissions=AlertAttempt.objects.count(),
        )

    def prepare_case(self, case_id: str) -> dict[str, object]:
        data = json.loads(
            (Path(__file__).parents[1] / "fixtures/listing/assessment_cases.json").read_text()
        )
        cases = cast(list[dict[str, object]], data["cases"])
        index = next(i for i, row in enumerate(cases) if row["id"] == case_id)
        row = cases[index]
        text = cast(dict[str, object], row["text"])
        external = str(25000 + index)
        photos = cast(list[dict[str, str]], row["photos"])
        self.source.rows[external] = dict(
            external_id=external,
            url=f"https://www.facebook.com/marketplace/item/{external}/",
            title=text["title"],
            description=text["description"],
            condition=text["condition"],
            price="R$ 1.000,00",
            published_at=self.clock.value.isoformat(),
            shipping_offered=True,
            source_available=True,
            media=dict(
                presence="present" if photos else "none",
                complete=True,
                reason="",
                photos=[
                    dict(
                        key=p["id"],
                        primary=True,
                        correlated=True,
                        variants=[
                            dict(
                                url=self.origin + "/" + Path(p["path"]).name, width=640, height=480
                            )
                        ],
                    )
                    for p in photos
                ],
            ),
        )
        self.collect()
        listing = Listing.objects.get(external_id=external)
        self.cases[case_id] = str(listing.id)
        work = self.context.prepare.execute(listing.id)
        if not work.requests:
            self.context.complete.execute(work.id)
        build_publish_exploration().execute()
        return self.status()

    def collect(self) -> dict[str, object]:
        self.clock.advance(61)
        CollectionState.objects.update(next_attempt_at=self.clock.value)
        for _ in range(40):
            reconcile_listings()
            state = CollectionState.objects.filter(current_id__isnull=False).first()
            if state is None:
                break
            build_listing_task_handler().execute(str(state.current_id), state.generation)
        for _ in range(40):
            due = build_media_repository().due(now())
            if not due:
                break
            for job in due:
                build_media_runner().execute(job)
        build_publish_exploration().execute()
        return self.status()

    def complete(self, kind: str = "light_wear") -> dict[str, object]:
        self.context.gateway.kind = kind
        for _ in range(120):
            if not self.context.run.execute():
                break
        for row in ConditionAssessment.objects.filter(publication_order=None):
            self.context.complete.execute(row.id)
        build_publish_exploration().execute()
        return self.status()

    def restart(self) -> dict[str, object]:
        InferenceControl.objects.update(paused=True)
        connections.close_all()
        resume_worker(self.paused_group)
        stopped = self.instance.command("./scripts/stop.sh")
        assert stopped.returncode == 0
        started = self.instance.command("./scripts/init.sh", "--disposable", timeout=120)
        assert started.returncode == 0
        self.paused_group = pause_worker(self.instance)
        InferenceControl.objects.update(paused=False)
        self.context = assessment_context()
        return self.status()

    def action(self, payload: dict[str, object]) -> dict[str, object]:
        action = str(payload.get("action", "status"))
        if action == "status":
            return self.status()
        if action == "prepare_case":
            return self.prepare_case(str(payload["id"]))
        if action == "collect":
            return self.collect()
        if action == "complete":
            return self.complete(str(payload.get("kind", "light_wear")))
        if action == "restart":
            return self.restart()
        if action == "clear_fault":
            self.context.gateway.fault = None
            return self.status()
        if action == "fail":
            self.context.gateway.fault = str(payload.get("code", "invalid_output"))
            return self.status()
        if action == "change_input":
            return self.change_input(payload)
        if action == "evaluate_corpus":
            return dict(
                state="blocked",
                reason="Human review and a separately coordinated real F19 runtime are required; controlled fake results are never quality evidence",
            )
        raise ValueError("Unknown lab action")

    def change_input(self, payload: dict[str, object]) -> dict[str, object]:
        listing = Listing.objects.get(id=UUID(str(payload["listing"])))
        row = self.source.rows[listing.external_id]
        kind = str(payload.get("kind", "text"))
        if kind == "text":
            row["description"] = str(payload["text"])
        elif kind == "photo":
            row["media"] = payload["media"]
        else:
            return dict(
                state="blocked",
                reason="Policy/model changes require an explicit versioned artifact; no canonical lock is modified by the lab",
            )
        self.collect()
        self.context.prepare.execute(listing.id)
        build_publish_exploration().execute()
        return self.status()

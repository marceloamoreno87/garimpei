from uuid import UUID, uuid4

from django.db.models import F
from django.utils.timezone import now

from garimpei.domain.assistance.errors import AssistanceError
from garimpei.infra.persistence.assistance_models import (
    AssistanceOperationsSnapshot,
    AssistancePolicy,
    AssistanceReview,
)
from garimpei.infra.persistence.listing_models import Listing, ListingInterestMatch
from garimpei.infra.persistence.monitoring_models import MonitoringInterest
from garimpei.infra.repository.assistance.publication import current_review

STATES = {
    "pending": "Aguardando análise local",
    "running": "Análise em andamento",
    "supported": "Evidências sustentadas",
    "conflict": "Conflito a revisar",
    "insufficient": "Evidência insuficiente",
    "failed": "Análise indisponível",
    "paused": "Aguardando retomada",
    "awaiting_resource": "Aguardando recurso local",
    "superseded": "Análise de revisão anterior",
}
PURPOSES = {
    "identity": "Identidade",
    "comparables": "Comparáveis",
    "condition": "Condição",
    "investigation": "Investigação",
    "operations": "Diagnóstico",
}
ACTIONS = {
    "check_integrations": "Confira o estado nas Integrações.",
    "check_local_ai": "Confira os recursos da IA local.",
    "recover_local_ai": "A execução anterior precisa de recuperação pelo operador.",
    "review_robot_control": "Confira a pausa no controle do robô.",
    "wait_for_work": "Aguarde o próximo trabalho do recorte.",
}


class PostgresAssistanceQueries:
    def listing(self, identity: UUID) -> dict[str, object]:
        row = Listing.objects.select_related("latest").filter(id=identity).first()
        if row is None or row.latest is None:
            raise AssistanceError("not_found", 404)
        reviews = (
            AssistanceReview.objects.filter(observation__listing=row)
            .select_related("observation", "candidate_observation__listing")
            .order_by("-created_at")[:100]
        )
        return dict(
            listing_id=row.id,
            revision=row.latest.ordinal,
            title=str(row.latest.evidence.get("title") or "Oferta"),
            reviews=[_review(review) for review in reviews],
            command_id=uuid4(),
            listing_page=True,
        )

    def coverage(self) -> dict[str, object]:
        rows = []
        for interest in MonitoringInterest.objects.filter(configuration__slot="active").order_by(
            "label"
        ):
            rows.extend(_interest_coverage(interest))
        return dict(
            rows=rows,
            checked_at=now(),
            integration_page=True,
            policy_active=AssistancePolicy.objects.filter(pk=1, active=True).exists(),
        )

    def operations(self) -> dict[str, object]:
        snapshot = AssistanceOperationsSnapshot.objects.order_by("-revision").first()
        reviews = AssistanceReview.objects.filter(purpose="operations").order_by("-created_at")[:10]
        return dict(
            snapshot=snapshot, reviews=[_review(review) for review in reviews], command_id=uuid4()
        )


def _review(row: AssistanceReview) -> dict[str, object]:
    state = row.state if current_review(row) else "superseded"
    result = row.result or {}
    requests = list(row.requests.select_related("request").all())
    return dict(
        id=row.id,
        purpose=PURPOSES.get(row.purpose, row.purpose),
        state=state,
        state_title=STATES.get(state, "Estado não confirmado"),
        reason=row.reason_code,
        revision=row.input_snapshot.get("revision"),
        created_at=row.created_at,
        completed_at=row.completed_at,
        model="qwen3.5:4b-q4_K_M",
        input_signature=row.input_signature,
        findings=result.get("findings", []),
        evidence=row.input_snapshot.get("facts", []),
        source_texts=row.input_snapshot.get("texts", {}),
        media=row.input_snapshot.get("media", []),
        candidate_listing=row.candidate_observation.listing_id
        if row.candidate_observation
        else None,
        limitations=result.get("limitations", []),
        consumed_by=row.consumed_by,
        cache_reuses=row.cache_reuses,
        requests=[
            dict(
                id=link.request_id,
                artifact=link.request.artifact,
                profile=link.request.prompt_version,
            )
            for link in requests
        ],
        next_action="Confira as evidências e a revisão atual antes de qualificar.",
        candidate=row.candidate_observation_id,
        actions=[
            ACTIONS.get(str(f.get("value")), "Confira o diagnóstico determinístico.")
            for f in result.get("findings", [])
        ]
        if row.purpose == "operations"
        else [],
    )


def _interest_coverage(interest: MonitoringInterest) -> list[dict[str, object]]:
    observations = list(
        ListingInterestMatch.objects.filter(
            kind=interest.kind,
            key=interest.key,
            observation__listing__latest_id=F("observation_id"),
        ).values_list("observation_id", flat=True)
    )
    rows = []
    for purpose in ("identity", "condition", "comparables", "investigation"):
        reviews = (
            AssistanceReview.objects.filter(purpose=purpose, observation_id__in=observations)
            if purpose != "investigation"
            else AssistanceReview.objects.filter(purpose=purpose, target_id=interest.id)
        )
        current = [
            review
            for review in reviews.select_related("observation", "candidate_observation__listing")
            if current_review(review)
        ]
        rows.append(
            dict(
                interest=interest.label,
                purpose=PURPOSES[purpose],
                denominator=(
                    len(observations) * max(0, Listing.objects.exclude(latest=None).count() - 1)
                )
                if purpose == "comparables"
                else len(observations)
                if purpose != "investigation"
                else 1,
                units="pares de ofertas"
                if purpose == "comparables"
                else "interesses"
                if purpose == "investigation"
                else "ofertas",
                requested=len(current)
                if purpose == "comparables"
                else len({str(r.observation_id or r.target_id) for r in current}),
                supported=sum(r.state == "supported" for r in current)
                if purpose == "comparables"
                else len(
                    {
                        str(r.observation_id or r.target_id)
                        for r in current
                        if r.state == "supported"
                    }
                ),
                failed=sum(r.state == "failed" for r in current),
                conflict=sum(r.state == "conflict" for r in current),
                insufficient=sum(r.state == "insufficient" for r in current),
                cache=sum(r.cache_reuses for r in current),
                no_data=not observations,
            )
        )
    return rows

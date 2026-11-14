"""Final gold authorization after slow channel checks, under global/publication order."""

from datetime import datetime

from garimpei.domain.alert.gold_evidence import POLICY
from garimpei.infra.persistence.alert_models import AlertIntent
from garimpei.infra.persistence.assistance_models import AssistancePolicy
from garimpei.infra.repository.alert.gold_adoption import gold_active
from garimpei.infra.repository.alert.gold_evidence_repository import PostgresGoldEvidenceRepository


def prepare_gold(row: AlertIntent, now: datetime) -> str | None:
    if not gold_active():
        return None
    if row.first_decision is not None:
        listing = row.first_decision.identity.listing
        purpose = "first"
        financial = row.financial if row.body else row.first_decision.financial
    else:
        assert row.decision is not None
        listing = row.decision.event.listing
        purpose = "event:" + str(row.decision.event.id)
        financial = row.financial if row.body else row.decision.financial
    decision = PostgresGoldEvidenceRepository.qualify_locked(listing, purpose, financial, now)
    if decision.state != "qualified":
        return decision.reason
    row.gold_qualification_id = decision.id
    row.save(update_fields=["gold_qualification"])
    return None


def attempt_gold_policy() -> str | None:
    if not gold_active():
        return None
    return (
        "assisted-evidence-v1"
        if AssistancePolicy.objects.filter(pk=1, active=True).exists()
        else POLICY
    )

"""Transactional qualification; network/model work is never performed here."""

from dataclasses import replace
from datetime import datetime
from uuid import UUID

from django.db import transaction

from garimpei.domain.alert.gold_evidence import POLICY, GoldDecision
from garimpei.domain.alert.gold_qualification import qualify
from garimpei.infra.persistence.alert_models import AlertEventDecision, FirstEligibilityDecision
from garimpei.infra.persistence.gold_models import GoldQualification
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.repository.alert.gold_snapshot import gold_snapshot
from garimpei.infra.repository.assistance.qualification import qualification_reviews
from garimpei.infra.repository.robot.locking import lock_robot_control


class PostgresGoldEvidenceRepository:
    def qualify(self, listing_id: UUID, purpose_key: str, now: datetime) -> GoldDecision:
        with transaction.atomic():
            lock_robot_control()
            lock_monitoring_publication()
            listing = Listing.objects.select_related("latest").get(id=listing_id)
            if purpose_key == "first":
                first = (
                    FirstEligibilityDecision.objects.filter(identity__listing=listing)
                    .order_by("-generation")
                    .first()
                )
                financial = first.financial if first else {}
            else:
                event = AlertEventDecision.objects.filter(
                    event__id=UUID(purpose_key.removeprefix("event:"))
                ).first()
                financial = event.financial if event else {}
            return self.qualify_locked(listing, purpose_key, financial, now)

    @staticmethod
    def qualify_locked(
        listing: Listing, purpose_key: str, financial: dict[str, object], now: datetime
    ) -> GoldDecision:
        evidence, record = gold_snapshot(listing, financial, now)
        decision = qualify(evidence, now, purpose_key)
        assistance_missing, assistance_refs = qualification_reviews(listing, record)
        if assistance_missing:
            decision = replace(
                decision,
                state="waiting" if decision.state == "qualified" else decision.state,
                reasons=tuple(
                    dict.fromkeys(
                        (
                            *(() if decision.state == "qualified" else decision.reasons),
                            *assistance_missing,
                        )
                    )
                ),
            )
        if assistance_refs or assistance_missing:
            from garimpei.infra.gateway.assistance.snapshots import digest

            decision = replace(
                decision,
                policy="assisted-evidence-v1",
                input_fingerprint=digest(
                    dict(original=decision.input_fingerprint, assistance=record.get("assistance"))
                ),
            )
        if purpose_key.startswith("event:"):
            event = AlertEventDecision.objects.select_related("event").get(
                event__id=UUID(purpose_key.removeprefix("event:"))
            )
            if event.event.observation_id != listing.latest_id:
                decision = replace(decision, state="waiting", reasons=("gold_evidence_changed",))
        record["canonical_name"] = decision.canonical_name
        row, _ = GoldQualification.objects.get_or_create(
            listing=listing,
            purpose_key=purpose_key,
            policy="assisted-evidence-v1" if record.get("assistance") else POLICY,
            input_fingerprint=decision.input_fingerprint,
            defaults=dict(
                observation_id=decision.observation_id,
                state=decision.state,
                reason=decision.reason,
                reasons=list(decision.reasons),
                evidence=record,
                evaluated_at=now,
                valid_until=decision.valid_until,
            ),
        )
        return replace(decision, id=row.id)

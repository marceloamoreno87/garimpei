from datetime import datetime, timedelta
from uuid import UUID

from django.db import transaction
from django.db.models import Q, QuerySet

from garimpei.domain.alert.first_eligibility import first_eligibility, publication_status
from garimpei.domain.alert.first_ports import ReevaluationCause
from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.domain.valuation.profit import ProfitComposition
from garimpei.infra.persistence.alert_models import (
    AlertIntent,
    FirstAlertIdentity,
    FirstAlertInventory,
    FirstEligibilityDecision,
)
from garimpei.infra.persistence.listing_models import Listing, ManualCondition
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.queries.alert.event_source import current_eligibility
from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
from garimpei.infra.repository.alert.first_financial import first_snapshot
from garimpei.infra.repository.alert.first_inputs import automatic_signature
from garimpei.infra.repository.listing.condition_mapper import condition_state
from garimpei.infra.repository.listing.mapper import decode_evidence


class PostgresFirstAlertRepository:
    def __init__(
        self, configuration: ConfigurationReader, listings: PostgresListingQueries
    ) -> None:
        self._configuration, self._listings = configuration, listings

    def adopt(self, now: datetime) -> None:
        with transaction.atomic():
            lock_monitoring_publication()
            inventory, _ = FirstAlertInventory.objects.select_for_update().get_or_create(
                installation="local"
            )
            rows = Listing.objects.order_by("id")
            if inventory.completed:
                rows = rows.exclude(firstalertidentity__installation="local")
            if not inventory.completed and inventory.cursor:
                rows = rows.filter(id__gt=inventory.cursor)
            page = tuple(rows.select_related("latest")[:100])
            for listing in page:
                self._adopt_listing(listing, now)
            if page and not inventory.completed:
                inventory.cursor = page[-1].id
            if len(page) < 100:
                inventory.completed = True
            inventory.updated_at = now
            inventory.save()

    @staticmethod
    def _adopt_listing(listing: Listing, now: datetime) -> None:
        row, created = FirstAlertIdentity.objects.select_for_update().get_or_create(
            listing=listing, defaults={"next_action": now}
        )
        intents = AlertIntent.objects.filter(decision__event__listing=listing).order_by(
            "created_at", "id"
        )
        _adopt_effect(row, intents)
        if created and ManualCondition.objects.filter(listing=listing).exists():
            # No proof of later automatic evidence: conservative adoption consumes it.
            row.manual_signature = automatic_signature(listing)
        row.save()

    def pending(self, now: datetime) -> tuple[UUID, ...]:
        if not FirstAlertInventory.objects.filter(installation="local", completed=True).exists():
            return ()
        return tuple(
            FirstAlertIdentity.objects.filter(next_action__lte=now)
            .order_by("next_action", "listing_id")
            .values_list("listing_id", flat=True)[:100]
        )

    def prepare(self, identity: UUID) -> str:
        return automatic_signature(Listing.objects.select_related("latest").get(id=identity))

    def defer(self, identity: UUID, now: datetime) -> None:
        FirstAlertIdentity.objects.filter(listing_id=identity).update(
            state="waiting", reason="profit_query_failed", next_action=now + timedelta(seconds=5)
        )

    def publish(
        self,
        identity: UUID,
        signature: str,
        profit: ProfitComposition | None,
        now: datetime,
        *,
        cause: ReevaluationCause = "automatic_input",
    ) -> None:
        with transaction.atomic():
            lock_monitoring_publication()
            row = (
                FirstAlertIdentity.objects.select_for_update(of=("self",))
                .select_related("listing__latest", "intent")
                .get(listing_id=identity)
            )
            row.next_action = now + timedelta(seconds=5)
            if signature != automatic_signature(row.listing):
                row.reason = "automatic_input_changed"
                row.save()
                return
            self._publish_locked(row, signature, profit, now, cause)

    def _publish_locked(
        self,
        row: FirstAlertIdentity,
        signature: str,
        profit: ProfitComposition | None,
        now: datetime,
        cause: ReevaluationCause,
    ) -> None:
        listing = row.listing
        if listing.latest is None:
            row.save()
            return
        evidence, condition = decode_evidence(listing.latest.evidence), condition_state(listing)
        current = current_eligibility(listing, self._configuration, self._listings)
        financial_reason, financial = first_snapshot(listing, profit)
        reasons = tuple(reason for reason in (current, financial_reason) if reason != "eligible")
        reason = first_eligibility(
            evidence.published_at,
            evidence.published_at_source,
            now,
            reasons,
            row.manual_signature == signature,
        )
        state = (
            "eligible"
            if reason == "eligible"
            else (
                "excluded"
                if reason
                in {
                    "condition_excluded",
                    "scope_excluded",
                    "listing_unavailable",
                    "publication_expired",
                }
                else "waiting"
            )
        )
        previous = row.decisions.order_by("-generation").first()
        if (
            previous is None
            or previous.signature != signature
            or previous.reason != reason
            or previous.observation_id != listing.latest_id
            or {k: v for k, v in previous.financial.items() if k != "calculated_at"}
            != {k: v for k, v in financial.items() if k != "calculated_at"}
        ):
            row.generation += 1
            decision = FirstEligibilityDecision.objects.create(
                identity=row,
                generation=row.generation,
                signature=signature,
                cause=cause,
                observation=listing.latest,
                condition_revision=condition.revision,
                state=state,
                reason=reason,
                reasons=list(dict.fromkeys((reason, *reasons))) if reason != "eligible" else [],
                financial=financial,
                publication_status=publication_status(
                    evidence.published_at, evidence.published_at_source, now
                ),
                published_at=evidence.published_at,
                publication_source=evidence.published_at_source or "",
                evaluated_at=now,
            )
        else:
            decision = previous
        row.signature, row.state, row.reason = signature, state, reason
        if self._replaceable_untransmitted(row, decision) and state == "eligible":
            assert row.intent is not None
            row.intent.state, row.intent.reason = "cancelled", "untransmitted_snapshot_replaced"
            row.intent.save(update_fields=["state", "reason"])
            row.intent = None
        if row.intent is None and state == "eligible":
            row.intent = AlertIntent.objects.create(
                first_decision=decision, created_at=now, next_action=now
            )
        elif (
            row.intent is not None
            and row.intent.state in {"queued", "blocked", "safe_retry"}
            and not row.intent.body
            and not row.intent.attempts.exists()
            and state == "eligible"
        ):
            row.intent.first_decision = decision
            row.intent.save(update_fields=["first_decision"])
        row.save()

    @staticmethod
    def _replaceable_untransmitted(
        row: FirstAlertIdentity, decision: FirstEligibilityDecision
    ) -> bool:
        intent = row.intent
        if intent is None:
            return False
        if intent.state == "cancelled" and not intent.attempts.exists():
            old = intent.first_decision
            return old is None or old.signature != decision.signature
        if intent.state not in {"queued", "blocked", "safe_retry"} or not intent.body:
            return False
        # Every original attempt must prove non-transmission; never infer it from a missing ACK.
        if (
            not intent.attempts.exists()
            or intent.attempts.exclude(state="safe_retry", reason="not_transmitted").exists()
        ):
            return False
        old = intent.first_decision
        return (
            old is None
            or old.observation_id != decision.observation_id
            or old.signature != decision.signature
            or old.financial != decision.financial
        )


def _adopt_effect(row: FirstAlertIdentity, intents: "QuerySet[AlertIntent]") -> None:
    confirmed = intents.filter(state="confirmed").first()
    if confirmed:
        row.intent, row.state, row.reason = confirmed, "confirmed", "legacy_confirmation"
        return
    possible = (
        intents.filter(
            Q(attempts__isnull=False) | Q(state__in=["authorized", "uncertain", "review"])
        )
        .distinct()
        .first()
    )
    if possible:
        row.intent, row.state, row.reason = (
            possible,
            "history_review",
            "legacy_transmission_possible",
        )
        return
    queued = tuple(intents.filter(state__in=["queued", "blocked", "safe_retry"]))
    if queued:
        row.intent, row.reason = queued[0], "legacy_adopted"
        intents.filter(id__in=[item.id for item in queued[1:]]).update(
            state="cancelled", reason="legacy_duplicate_untransmitted"
        )

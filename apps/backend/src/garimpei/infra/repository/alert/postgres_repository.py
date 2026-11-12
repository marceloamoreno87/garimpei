from datetime import datetime, timedelta
from uuid import UUID

from django.db import transaction
from django.db.models import Q

from garimpei.domain.alert.alert import AlertPolicy, Binding, Delivery, Outcome
from garimpei.domain.alert.eligibility import eligibility
from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.domain.listing.read_models import ChangePage
from garimpei.domain.valuation.profit import ProfitComposition
from garimpei.infra.persistence.alert_models import AlertEventDecision, AlertFeedCursor, AlertIntent
from garimpei.infra.persistence.listing_models import ListingEvent
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.queries.alert.event_source import covered, event_condition
from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
from garimpei.infra.repository.alert.delivery_state import authorize, complete, postpone
from garimpei.infra.repository.alert.financial import financial_snapshot


class PostgresAlertRepository:
    def __init__(
        self,
        configuration: ConfigurationReader,
        listings: PostgresListingQueries,
        policy: AlertPolicy,
    ) -> None:
        self._configuration, self._listings, self._policy = configuration, listings, policy

    def cursor(self) -> int | None:
        row = AlertFeedCursor.objects.filter(installation="local").first()
        return row.sequence if row else None

    def ingest(self, page: ChangePage, now: datetime) -> None:
        with transaction.atomic():
            lock_monitoring_publication()
            cursor, _ = AlertFeedCursor.objects.select_for_update().get_or_create(
                installation="local"
            )
            for change in page.events:
                self._accept(change.id, now)
            cursor.sequence = max(cursor.sequence, page.cursor or 0)
            cursor.history_ready, cursor.updated_at = True, now
            cursor.save()

    @staticmethod
    def _accept(identity: UUID, now: datetime) -> None:
        event = ListingEvent.objects.select_related("observation").get(id=identity)
        condition = event_condition(event)
        reason = eligibility(
            event.kind,
            event.silent,
            covered(event),
            event.observation.matches.exists(),
            condition.condition,
            True,
            False,
        )
        reason = condition.reason or reason
        AlertEventDecision.objects.get_or_create(
            event=event,
            defaults={
                "next_action": now,
                "state": "waiting" if reason == "eligible" else "excluded",
                "reason": "pending_evaluation" if reason == "eligible" else reason,
                "condition_revision": condition.revision,
            },
        )

    def pause(self) -> None:
        AlertFeedCursor.objects.filter(installation="local").update(history_ready=False)

    def defer_evaluation(self, identity: UUID, now: datetime) -> None:
        AlertEventDecision.objects.filter(event__id=identity, state="waiting").update(
            reason="profit_query_failed", next_action=now + timedelta(seconds=self._policy.tick)
        )

    def pending(self, now: datetime) -> tuple[UUID, ...]:
        return tuple(
            AlertEventDecision.objects.filter(state="waiting", next_action__lte=now)
            .order_by("event__sequence")
            .values_list("event__id", flat=True)[:100]
        )

    def evaluate(self, identity: UUID, profit: ProfitComposition | None, now: datetime) -> None:
        with transaction.atomic():
            lock_monitoring_publication()
            row = (
                AlertEventDecision.objects.select_for_update()
                .select_related("event__observation")
                .get(event__id=identity)
            )
            if row.state != "waiting":
                return
            self._evaluate_locked(row, profit, now)

    def _evaluate_locked(
        self, row: AlertEventDecision, profit: ProfitComposition | None, now: datetime
    ) -> None:
        event = row.event
        earlier = AlertIntent.objects.filter(
            decision__event__listing_id=event.listing_id,
            decision__event__sequence__lt=event.sequence,
        )
        previous = earlier.filter(state="confirmed").exists()
        active = earlier.filter(state__in=["queued", "blocked", "safe_retry"]).exists()
        active = (
            active
            or earlier.filter(
                state__in=["authorized", "uncertain"],
                attempts__authorized_at__gt=now - timedelta(seconds=self._policy.window),
            ).exists()
        )
        active = (
            active
            or AlertEventDecision.objects.filter(
                event__listing_id=event.listing_id,
                event__sequence__lt=event.sequence,
                state="waiting",
            ).exists()
        )
        reason = eligibility(
            event.kind, event.silent, covered(event), True, "good", previous, active
        )
        if reason == "waiting_previous":
            row.reason = reason
        elif reason != "eligible":
            row.state, row.reason = "excluded", reason
        else:
            row.state, row.reason, row.financial = financial_snapshot(event, profit)
        row.next_action, row.evaluated_at = now + timedelta(seconds=self._policy.tick), now
        row.save()
        if row.state == "eligible":
            AlertIntent.objects.get_or_create(
                decision=row, defaults={"next_action": now, "created_at": now}
            )

    def ready(self, now: datetime, *, reconcile: bool) -> tuple[UUID, ...]:
        states = ["authorized", "uncertain"] if reconcile else ["queued", "blocked", "safe_retry"]
        return tuple(
            AlertIntent.objects.filter(state__in=states, next_action__lte=now)
            .filter(Q(lease_until=None) | Q(lease_until__lte=now))
            .order_by("created_at")
            .values_list("id", flat=True)[:100]
        )

    def block(self, identity: UUID, reason: str, now: datetime) -> None:
        with transaction.atomic():
            row = AlertIntent.objects.select_for_update().get(id=identity)
            if row.state in ["queued", "blocked", "safe_retry"]:
                postpone(row, reason, now, self._policy)

    def claim(
        self, identity: UUID, binding: Binding | None, now: datetime, *, reconcile: bool
    ) -> Delivery | None:
        with transaction.atomic():
            lock_monitoring_publication()
            cursor = AlertFeedCursor.objects.get(installation="local")
            if not cursor.history_ready or cursor.dispatch_suspended:
                return None
            row = (
                AlertIntent.objects.select_for_update()
                .select_related("decision__event__listing", "decision__event__observation")
                .get(id=identity)
            )
            return authorize(
                row, binding, now, reconcile, self._configuration, self._listings, self._policy
            )

    def finish(self, delivery: Delivery, outcome: Outcome, now: datetime) -> None:
        with transaction.atomic():
            # Confirmation and dependent eligibility reads share one publication order.
            lock_monitoring_publication()
            row = AlertIntent.objects.select_for_update().get(id=delivery.reference)
            if row.generation != delivery.generation or row.state not in [
                "authorized",
                "uncertain",
            ]:
                return
            complete(row, delivery, outcome, now, self._policy)

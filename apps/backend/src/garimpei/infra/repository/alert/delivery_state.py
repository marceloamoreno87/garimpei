import logging
from datetime import datetime, timedelta
from decimal import Decimal

from garimpei.domain.alert.alert import AlertMessage, AlertPolicy, Binding, Delivery, Outcome
from garimpei.domain.alert.eligibility import message_text, verified_receipt
from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.infra.persistence.alert_models import AlertAttempt, AlertIntent
from garimpei.infra.queries.alert.event_source import current_eligibility
from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
from garimpei.infra.repository.alert.assessment_note import assessment_note
from garimpei.infra.repository.alert.financial import decode_snapshot
from garimpei.infra.repository.alert.first_authorization import first_body, prepare_first
from garimpei.infra.repository.alert.message_authorization import prepare_financial

logger = logging.getLogger("garimpei.alert")


def postpone(row: AlertIntent, reason: str, now: datetime, policy: AlertPolicy) -> None:
    row.state, row.reason = "blocked", reason
    row.next_action = now + timedelta(seconds=policy.delay(row.failures))
    row.failures += 1
    row.save()
    log_state(row)


def authorize(
    row: AlertIntent,
    binding: Binding | None,
    now: datetime,
    reconcile: bool,
    configuration: ConfigurationReader,
    listings: PostgresListingQueries,
    policy: AlertPolicy,
) -> Delivery | None:
    if row.lease_until and row.lease_until > now:
        return None
    states = ["authorized", "uncertain"] if reconcile else ["queued", "blocked", "safe_retry"]
    if row.state not in states or row.next_action > now:
        return None
    if reconcile and not all((row.session, row.recipient, row.account)):
        row.state, row.reason, row.lease_until = (
            "review",
            "binding_history_missing" if row.body else "authorized_body_missing",
            None,
        )
        row.save()
        log_state(row)
        return None
    if reconcile:
        binding = Binding(row.session, row.recipient, row.account)
    if binding is None:
        postpone(row, "configuration_missing", now, policy)
        return None
    if row.session and (row.session, row.recipient, row.account) != (
        binding.session,
        binding.recipient,
        binding.account,
    ):
        # Authorized attempts must remain reconcilable in their original channel.
        row.reason, row.next_action = "binding_changed", now + timedelta(seconds=policy.retry_max)
        row.save()
        log_state(row)
        return None
    return _claim(row, binding, now, reconcile, configuration, listings, policy)


def _claim(
    row: AlertIntent,
    binding: Binding,
    now: datetime,
    reconcile: bool,
    configuration: ConfigurationReader,
    listings: PostgresListingQueries,
    policy: AlertPolicy,
) -> Delivery | None:
    if (
        not reconcile
        and row.first_decision_id is None
        and row.decision is not None
        and row.decision.event.kind == "discovered"
    ):
        postpone(row, "first_evaluation_pending", now, policy)
        return None
    if row.first_decision_id is not None:
        return _claim_first(row, binding, now, reconcile, configuration, listings, policy)
    reason = prepare_financial(row, now)
    if reason is not None:
        if row.state != "review":
            postpone(row, reason, now, policy)
        return None
    if not reconcile:
        assert row.decision is not None
        reason = current_eligibility(row.decision.event.listing, configuration, listings)
        if reason in {"waiting_scope", "waiting_condition_assessment"}:
            postpone(row, reason, now, policy)
            return None
        if reason != "eligible":
            row.state, row.reason = "cancelled", reason
            row.save()
            log_state(row)
            return None
    row.generation += 1
    row.lease_until = now + timedelta(seconds=policy.lease)
    attempt = _attempt(row, binding, now, reconcile)
    row.state, row.reason = "uncertain" if reconcile else "authorized", "transmission_possible"
    row.save()
    log_state(row)
    return Delivery(
        row.id,
        row.generation,
        binding,
        row.body,
        attempt.authorized_at,
        attempt.message_id,
        reconcile,
        attempt.id,
    )


def _attempt(row: AlertIntent, binding: Binding, now: datetime, reconcile: bool) -> AlertAttempt:
    if reconcile:
        return row.attempts.latest("ordinal")
    if not row.body:
        assert row.decision is not None
        event, financial = row.decision.event, row.financial
        snapshot = decode_snapshot(financial)
        assert snapshot is not None
        row.body = message_text(
            AlertMessage(
                row.id,
                event.kind,
                event.observation.evidence.get("title") or "Anúncio",
                "Facebook Marketplace",
                Decimal(financial["purchase"]),
                event.previous.price if event.previous else None,
                Decimal(financial["profit"]),
                event.observation.observed_at,
                event.listing.canonical_url,
                profit_policy=snapshot.policy,
                financial=snapshot,
                condition_note=assessment_note(
                    row.decision.assessment_id, row.decision.assessment_revision
                ),
            )
        )
        row.session, row.recipient, row.account = (
            binding.session,
            binding.recipient,
            binding.account,
        )
    return AlertAttempt.objects.create(
        intent=row, ordinal=row.attempts.count() + 1, generation=row.generation, authorized_at=now
    )


def complete(
    row: AlertIntent, delivery: Delivery, result: Outcome, now: datetime, policy: AlertPolicy
) -> None:
    attempt = row.attempts.latest("ordinal")
    receipt = result.receipt
    confirmed = receipt is not None and verified_receipt(receipt, delivery.binding, delivery.body)
    state = "confirmed" if confirmed else result.state
    if state == "confirmed" and not confirmed:
        state = "uncertain"
    row.state, row.reason, row.lease_until = state, result.reason, None
    row.next_action = now + timedelta(seconds=max(policy.delay(row.failures), result.retry_after))
    row.failures += 1
    if confirmed and receipt is not None:
        row.confirmed_at, row.confirmed_message, row.confirmed_ack = now, receipt.id, receipt.ack
    if state == "uncertain" and (now - attempt.authorized_at).total_seconds() >= policy.window:
        row.state, row.reason = "review", "reconciliation_window_ended"
    row.save()
    attempt.state, attempt.reason, attempt.finished_at = row.state, row.reason, now
    if receipt is not None:
        attempt.message_id, attempt.ack = receipt.id, receipt.ack
    attempt.provenance = "history_query" if delivery.reconcile else "send_response"
    attempt.save()
    log_state(row)


def log_state(row: AlertIntent) -> None:
    logger.info(
        "alert_state",
        extra={
            "event": "alert_state",
            "alert_reference": str(row.id),
            "alert_state": row.state,
            "alert_reason": row.reason,
            "alert_body_format": row.body_format,
        },
    )


def _claim_first(
    row: AlertIntent,
    binding: Binding,
    now: datetime,
    reconcile: bool,
    configuration: ConfigurationReader,
    listings: PostgresListingQueries,
    policy: AlertPolicy,
) -> Delivery | None:
    if not reconcile:
        reason = prepare_first(row, now, configuration, listings)
        if reason in {
            "publication_expired",
            "condition_excluded",
            "scope_excluded",
            "listing_unavailable",
        }:
            row.state, row.reason = "cancelled", reason
            row.save()
            log_state(row)
            return None
        if reason != "eligible":
            postpone(row, reason, now, policy)
            return None
    if reconcile and not row.body:
        row.state, row.reason = "review", "authorized_body_missing"
        row.save()
        return None
    row.generation += 1
    row.lease_until = now + timedelta(seconds=policy.lease)
    if reconcile:
        attempt = row.attempts.latest("ordinal")
    else:
        if not row.body:
            row.body = first_body(row)
            row.session, row.recipient, row.account = (
                binding.session,
                binding.recipient,
                binding.account,
            )
        attempt = AlertAttempt.objects.create(
            intent=row,
            ordinal=row.attempts.count() + 1,
            generation=row.generation,
            authorized_at=now,
        )
    row.state, row.reason = "uncertain" if reconcile else "authorized", "transmission_possible"
    row.save()
    log_state(row)
    return Delivery(
        row.id,
        row.generation,
        binding,
        row.body,
        attempt.authorized_at,
        attempt.message_id,
        reconcile,
        attempt.id,
    )

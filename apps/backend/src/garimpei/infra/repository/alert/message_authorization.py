"""Freeze complete financial data at the existing transactional authorization boundary."""

from datetime import datetime

from garimpei.domain.alert.financial_snapshot import FORMAT
from garimpei.infra.persistence.alert_models import AlertIntent
from garimpei.infra.repository.alert.financial import decode_snapshot, encode_snapshot
from garimpei.infra.repository.alert.financial_references import compatible_references


def prepare_financial(row: AlertIntent, now: datetime) -> str | None:
    if row.body:
        return None
    if row.attempts.exists():
        # A possibly transmitted body cannot be reconstructed from mutable data.
        row.state, row.reason, row.lease_until = "review", "authorized_body_missing", None
        row.save()
        return row.reason
    raw = row.decision.financial
    value = decode_snapshot(raw)
    event = row.decision.event
    if value is not None and (
        value.listing_id != event.listing_id
        or value.event_id != event.id
        or value.observation_id != event.observation_id
        or value.purchase != event.observation.price
    ):
        return "profit_observation_mismatch"
    if value is None:
        complete_keys = {"resale", "fee", "fee_percent", "configuration_id", "listing_id"}
        if complete_keys.issubset(raw):
            return "profit_incompatible"
        # Reuse the normal F07 event query on the next evaluation tick; same intent.
        decision = row.decision
        decision.state, decision.reason, decision.next_action = "waiting", "profit_pending", now
        decision.save(update_fields=["state", "reason", "next_action"])
        return "profit_pending"
    if not compatible_references(value, event):
        return "profit_incompatible"
    row.financial, row.body_format = encode_snapshot(value), FORMAT
    return None

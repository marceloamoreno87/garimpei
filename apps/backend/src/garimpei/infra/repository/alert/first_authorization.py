"""Final first-alert checks run after the slow channel check, under publication order."""

from datetime import datetime

from garimpei.domain.alert.alert import AlertMessage
from garimpei.domain.alert.eligibility import message_text
from garimpei.domain.alert.financial_snapshot import FORMAT
from garimpei.domain.alert.first_eligibility import first_eligibility
from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.infra.persistence.alert_models import AlertIntent, FirstAlertInventory
from garimpei.infra.queries.alert.event_source import current_eligibility
from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
from garimpei.infra.repository.alert.assessment_note import assessment_note
from garimpei.infra.repository.alert.financial import decode_snapshot, encode_snapshot
from garimpei.infra.repository.alert.first_financial import first_references
from garimpei.infra.repository.alert.first_inputs import automatic_signature
from garimpei.infra.repository.alert.gold_message import gold_message_note
from garimpei.infra.repository.listing.mapper import decode_evidence


def prepare_first(
    row: AlertIntent,
    now: datetime,
    configuration: ConfigurationReader,
    listings: PostgresListingQueries,
) -> str:
    if not FirstAlertInventory.objects.filter(installation="local", completed=True).exists():
        return "history_inventory_pending"
    decision = row.first_decision
    assert decision is not None
    listing = decision.identity.listing
    observation = listing.latest
    if observation is None:
        return "listing_missing"
    evidence = decode_evidence(observation.evidence)
    current = current_eligibility(listing, configuration, listings)
    reason = first_eligibility(
        evidence.published_at,
        evidence.published_at_source,
        now,
        () if current == "eligible" else (current,),
        False,
    )
    if reason != "eligible":
        return reason
    if (
        observation.id != decision.observation_id
        or automatic_signature(listing) != decision.signature
    ):
        return "automatic_input_changed"
    value = decode_snapshot(row.financial if row.body else decision.financial)
    if value is None:
        return (
            "profit_pending"
            if not {"resale", "fee", "fee_percent", "configuration_id", "listing_id"}.issubset(
                decision.financial
            )
            else "profit_incompatible"
        )
    if (
        value.observation_id != observation.id
        or value.listing_id != listing.id
        or value.purchase != observation.price
    ):
        return "profit_observation_mismatch"
    if value.event_id is not None or not first_references(value, now):
        return "profit_incompatible"
    if not row.body:
        row.financial, row.body_format = encode_snapshot(value), FORMAT
    return "eligible"


def first_body(row: AlertIntent) -> str:
    decision = row.first_decision
    assert decision is not None
    observation = decision.observation
    listing = decision.identity.listing
    value = decode_snapshot(row.financial)
    assert value is not None
    body = message_text(
        AlertMessage(
            row.id,
            "discovered",
            observation.evidence.get("title") or "Anúncio",
            "Facebook Marketplace",
            value.purchase,
            None,
            value.profit,
            observation.observed_at,
            listing.canonical_url,
            profit_policy=value.policy,
            financial=value,
            condition_note=assessment_note(decision.assessment_id, decision.assessment_revision),
        )
    )

    note = gold_message_note(row)
    return body + ("\n" + note if note else "")

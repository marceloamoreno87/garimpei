"""Build a coherent F15/F18/F06/F07 snapshot under the publication transaction."""

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from typing import cast

from garimpei.domain.alert.gold_evidence import GoldEvidence
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
from garimpei.infra.persistence.valuation_models import ValuationProgress
from garimpei.infra.queries.listing.assessment_queries import PostgresAssessmentQueries
from garimpei.infra.repository.alert.financial import decode_snapshot
from garimpei.infra.repository.listing.condition_mapper import condition_state
from garimpei.infra.repository.listing.mapper import decode_evidence
from garimpei.infra.repository.valuation.identity_mapper import (
    current_identification,
    encode_identity,
)
from garimpei.infra.repository.valuation.mapper import (
    decode_valuation,
    encode_comparable,
    listing_comparable,
    mapping,
    valuation_signature,
)


def gold_snapshot(
    listing: Listing, financial: dict[str, object], now: datetime
) -> tuple[GoldEvidence, dict[str, object]]:
    observation = listing.latest
    assert observation is not None
    identity = current_identification(listing)
    assessment = PostgresAssessmentQueries().observation(listing.id, observation.id)
    condition = condition_state(listing)
    configuration = MonitoringConfiguration.objects.filter(slot="active").first()
    progress = (
        ValuationProgress.objects.select_related("current__work").filter(listing=listing).first()
    )
    evaluation = progress.current if progress else None
    valuation = decode_valuation(mapping(evaluation.result)) if evaluation else None
    snapshot = decode_snapshot(financial)
    config_matches = snapshot is None or bool(
        configuration
        and snapshot.configuration_id == configuration.id
        and snapshot.configuration_revision == configuration.revision
        and snapshot.fee_percent == configuration.resale_fee_percent
    )
    applicable = config_matches and _valuation_current(listing, progress)
    record = dict(
        schema_version=1,
        listing_id=str(listing.id),
        observation_id=str(observation.id),
        observation_revision=observation.ordinal,
        source=listing.source,
        external_id=listing.external_id,
        url=listing.canonical_url,
        observation=dict(evidence=observation.evidence, coverage=observation.coverage),
        assessment=asdict(assessment),
        condition=dict(
            effective=condition.effective, manual=condition.manual, revision=condition.revision
        ),
        identity=encode_identity(identity),
        valuation=evaluation.result if evaluation else None,
        valuation_work=evaluation.work.snapshot if evaluation else None,
        valuation_requested=progress.requested if progress else None,
        configuration=dict(
            id=str(configuration.id),
            revision=configuration.revision,
            fee=str(configuration.resale_fee_percent),
        )
        if configuration
        else None,
        financial={key: value for key, value in financial.items() if key != "calculated_at"},
        applicable=applicable,
    )
    canonical = json.dumps(record, sort_keys=True, default=str)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    serializable = cast(dict[str, object], json.loads(canonical))
    return GoldEvidence(
        listing.id,
        observation.id,
        observation.ordinal,
        decode_evidence(observation.evidence),
        condition.effective,
        assessment,
        identity,
        valuation,
        snapshot,
        digest,
        applicable=applicable,
    ), serializable


def _valuation_current(listing: Listing, progress: ValuationProgress | None) -> bool:
    if progress is None or progress.current is None:
        return True
    if progress.requested != progress.current.work.revision:
        return False
    identity = current_identification(listing)
    target = listing_comparable(listing, identity)
    candidates = tuple(
        listing_comparable(row, current_identification(row))
        for row in Listing.objects.exclude(id=listing.id)
        .exclude(latest=None)
        .select_related("latest")
        .order_by("id")
    )
    equivalent = tuple(row for row in candidates if row.product == target.product)
    return (
        valuation_signature(
            dict(
                target=encode_comparable(target),
                candidates=[encode_comparable(row) for row in equivalent],
            ),
            target.product,
        )
        == progress.signature
    )


def automatic_gold_signature(record: dict[str, object]) -> str:
    # Manual choice is deliberately excluded; automatic photos/identity/history remain triggers.
    automatic = {
        key: value for key, value in record.items() if key not in {"condition", "canonical_name"}
    }
    return hashlib.sha256(json.dumps(automatic, sort_keys=True, default=str).encode()).hexdigest()

"""Check immutable valuation references before authorizing a previously unbound body."""

from typing import cast

from garimpei.domain.alert.financial_snapshot import FinancialSnapshot
from garimpei.domain.valuation.identity import identify
from garimpei.infra.persistence.listing_models import ListingEvent
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
from garimpei.infra.persistence.valuation_models import ValuationEvaluation
from garimpei.infra.repository.listing.mapper import EvidenceRecord, decode_evidence
from garimpei.infra.repository.valuation.identity_mapper import current_identification
from garimpei.infra.repository.valuation.mapper import decode_valuation, mapping


def compatible_references(value: FinancialSnapshot, event: ListingEvent) -> bool:
    evaluation = ValuationEvaluation.objects.filter(
        id=value.evaluation_id, work__listing_id=value.listing_id
    ).first()
    if evaluation is None:
        return False
    valuation = decode_valuation(mapping(evaluation.result))
    current = current_identification(event.listing)
    product = (
        current.product_key
        if current.manual_revision
        else identify(decode_evidence(cast(EvidenceRecord, event.observation.evidence)))
    )
    if (
        valuation.id != value.evaluation_id
        or valuation.listing_id != value.listing_id
        or valuation.revision != value.evaluation_revision
        or valuation.product != product
        or valuation.resale.price != value.resale
    ):
        return False
    # Later configuration revisions do not rewrite an already applicable composition.
    return MonitoringConfiguration.objects.filter(
        id=value.configuration_id, revision__gte=value.configuration_revision
    ).exists()

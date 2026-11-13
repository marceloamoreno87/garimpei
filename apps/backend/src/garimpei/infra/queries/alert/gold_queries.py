"""Read-only current qualification, never creating a decision or scheduling work."""

from collections.abc import Callable
from datetime import datetime
from typing import cast
from uuid import UUID

from django.db import DatabaseError

from garimpei.domain.alert.gold_diagnostic import GoldDiagnostic, GoldDiagnosticReadFailed
from garimpei.domain.alert.gold_evidence import POLICY
from garimpei.domain.alert.gold_qualification import qualify
from garimpei.infra.persistence.alert_models import FirstEligibilityDecision
from garimpei.infra.persistence.gold_models import GoldQualification
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.repository.alert.gold_snapshot import gold_snapshot

LABELS = {
    "gold_qualified": "Alerta ouro: evidências suficientes",
    "gold_condition_pending": "Aguardando análise de texto e fotos",
    "gold_photos_missing": "Faltam fotos analisadas desta oferta",
    "gold_condition_insufficient": "Condição de funcionamento ainda insuficiente",
    "gold_condition_defect": "Defeito impede a qualificação do alerta",
    "gold_condition_conflict": "Há contradição nas evidências de condição",
    "gold_identity_pending": "Aguardando identificação do produto",
    "gold_identity_missing_attribute": "Falta um atributo determinante do produto",
    "gold_identity_conflict": "Identidade ou variante em conflito",
    "gold_item_incompatible": "Produto fora da comparação equivalente",
    "gold_history_pending": "Aguardando histórico de preços",
    "gold_history_insufficient": "Faltam cinco comparáveis usados válidos",
    "gold_history_dispersed": "Histórico de preços muito disperso",
    "gold_history_expired": "Referências de preços vencidas",
    "gold_profit_pending": "Lucro estimado ainda indisponível",
    "gold_profit_non_positive": "Lucro estimado zero ou negativo impede alerta",
    "gold_evidence_changed": "Evidências alteradas; aguardando nova qualificação",
    "gold_dependency_unavailable": "Não foi possível consultar a qualificação do alerta",
}


class PostgresGoldDiagnosticQueries:
    def __init__(self, clock: Callable[[], datetime]) -> None:
        self._clock = clock

    def read(self, listing_id: UUID) -> GoldDiagnostic | None:
        try:
            return self._read(listing_id)
        except (DatabaseError, ValueError, KeyError) as error:
            raise GoldDiagnosticReadFailed() from error

    def _read(self, listing_id: UUID) -> GoldDiagnostic | None:
        listing = Listing.objects.select_related("latest").filter(id=listing_id).first()
        if listing is None or listing.latest is None:
            return None
        first = (
            FirstEligibilityDecision.objects.filter(identity__listing_id=listing_id)
            .order_by("-generation")
            .first()
        )
        snapshot, _ = gold_snapshot(listing, first.financial if first else {}, self._clock())
        decision = qualify(snapshot, self._clock())
        rows = GoldQualification.objects.filter(
            listing_id=listing_id, purpose_key="first", policy=POLICY
        )
        # Input identity is authoritative; controlled clocks and UUIDs do not establish order.
        row = rows.filter(
            input_fingerprint=decision.input_fingerprint, observation_id=listing.latest_id
        ).first()
        row = row or rows.order_by("-evaluated_at").first()
        if row is None:
            return None
        current = (
            row.input_fingerprint == decision.input_fingerprint
            and row.observation_id == listing.latest_id
        )
        reason = decision.reason if current else "gold_evidence_changed"
        valuation = cast(dict[str, object], row.evidence.get("valuation") or {})
        resale = cast(dict[str, object], valuation.get("resale") or {})
        return GoldDiagnostic(
            decision.state if current else "waiting",
            reason,
            decision.reasons if current else (reason,),
            LABELS[reason],
            str(row.evidence.get("canonical_name") or ""),
            decision.product_key or "",
            row.policy,
            row.evaluated_at,
            row.observation_id,
            current,
            int(str(resale.get("after", 0))),
            str(valuation.get("method") or "median-brl-v1"),
            row.valid_until,
            row.evidence,
        )

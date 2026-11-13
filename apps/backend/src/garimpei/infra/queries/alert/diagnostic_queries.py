from datetime import timedelta
from uuid import UUID

from django.db import DatabaseError
from django.db.models import Q

from garimpei.domain.alert.diagnostic import (
    AlertDiagnostic,
    AlertDiagnosticReadFailed,
    AlertHistory,
)
from garimpei.domain.alert.gold_diagnostic import GoldDiagnosticQueries, GoldDiagnosticReadFailed
from garimpei.infra.persistence.alert_models import (
    AlertFeedCursor,
    AlertIntent,
    FirstAlertIdentity,
    FirstAlertInventory,
)
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.repository.valuation.identity_mapper import identify_row

LABELS = {
    "analysis_pending": "Aguardando análise das fotos",
    "legacy_history_conflict": "Histórico com transmissões possíveis exige revisão",
    "pending_evaluation": "Aguardando avaliação do primeiro alerta",
    "publication_missing": "Aguardando data de publicação na origem",
    "publication_untrusted": "Aguardando confirmação da data de publicação",
    "publication_future": "A publicação informada está no futuro",
    "publication_expired": "Prazo de 48 horas da publicação encerrado",
    "condition_excluded": "A condição efetiva ainda não permite alerta",
    "manual_change_only": "Sua classificação foi salva; aguardando nova entrada automática",
    "waiting_scope": "Aguardando confirmação do interesse vigente",
    "scope_excluded": "Oferta fora dos interesses vigentes",
    "listing_unavailable": "Oferta indisponível na origem",
    "profit_pending": "Aguardando avaliação de preços",
    "aguardando_avaliacao": "Aguardando avaliação de preços",
    "amostra_insuficiente": "Aguardando comparáveis usados suficientes",
    "amostra_dispersa": "Aguardando uma amostra de preços consistente",
    "familia_sem_suporte": "A família ou modelo ainda não tem suporte de comparação",
    "atributo_ausente": "Falta um atributo determinante para identificar o produto",
    "identidade_em_conflito": "Revise os atributos de identidade em conflito",
    "item_excluido": "Acessório, peça ou conjunto fora da comparação",
    "produto_indeterminado": "Aguardando identificação do produto",
    "produto_incompativel": "Aguardando avaliação da variante atual",
    "configuration_missing": "Aguardando configuração do canal",
    "pending_channel": "Pronta para envio; aguardando o canal",
    "session_unavailable": "Canal indisponível; nova tentativa agendada",
    "profit_query_failed": "Falha recuperável ao consultar a estimativa",
    "history_unavailable": "Histórico de alertas indisponível; envio suspenso",
    "legacy_transmission_possible": "Histórico anterior requer revisão; novo envio suspenso",
    "transmission_possible": "Envio incerto; aguardando reconciliação",
    "confirmed": "Confirmada no servidor",
    "eligible": "Oferta pronta para o primeiro alerta",
}


def reason_label(reason: str) -> str:
    return LABELS.get(reason, "Aguardando dados consistentes para o alerta")


class PostgresAlertDiagnosticQueries:
    def __init__(self, gold: GoldDiagnosticQueries | None = None) -> None:
        self._gold = gold

    def read(
        self, listing_id: UUID, displayed_observation_id: UUID | None
    ) -> AlertDiagnostic | None:
        try:
            return self._read(listing_id, displayed_observation_id)
        except DatabaseError as error:
            raise AlertDiagnosticReadFailed() from error

    def _read(self, listing_id: UUID, displayed: UUID | None) -> AlertDiagnostic | None:
        listing = (
            Listing.objects.select_related("latest", "identity_progress__manual__observation")
            .filter(id=listing_id)
            .first()
        )
        if listing is None:
            return None
        row = FirstAlertIdentity.objects.filter(listing_id=listing_id, installation="local").first()
        decision = row.decisions.order_by("-generation").first() if row else None
        intents = tuple(
            AlertIntent.objects.filter(
                Q(first_decision__identity__listing_id=listing_id)
                | Q(decision__event__listing_id=listing_id)
            )
            .select_related("decision__event")
            .order_by("created_at", "id")
        )
        confirmed = next(
            (
                i
                for i in intents
                if i.state == "confirmed"
                and i.confirmed_message
                and i.confirmed_ack
                and i.confirmed_at
            ),
            None,
        )
        active = next(
            (i for i in reversed(intents) if i.state in {"authorized", "uncertain", "review"}), None
        )
        active = active or next(
            (i for i in reversed(intents) if i.state in {"queued", "blocked", "safe_retry"}), None
        )
        state, reason = (row.state, row.reason) if row else ("waiting", "pending_evaluation")
        if active:
            state, reason = active.state, active.reason
        elif confirmed:
            state, reason = "confirmed", "confirmed"
        if sum(i.state in {"authorized", "uncertain", "review"} for i in intents) > 1:
            state, reason = "history_review", "legacy_history_conflict"
        inventory = FirstAlertInventory.objects.filter(
            installation="local", completed=True
        ).exists()
        cursor = AlertFeedCursor.objects.filter(installation="local").first()
        if not inventory or (
            cursor is not None and (not cursor.history_ready or cursor.dispatch_suspended)
        ):
            state, reason = "suspended", "history_unavailable"
        first = row.intent if row and row.intent_id else None
        first_state = first.state if first else ("confirmed" if confirmed else "not_sent")
        financial = decision.financial if decision else {}
        published = decision.published_at if decision else None
        observation = decision.observation_id if decision else None
        reasons = tuple(dict.fromkeys((reason, *(decision.reasons if decision else ()))))
        if (
            not inventory
            or (cursor is not None and (not cursor.history_ready or cursor.dispatch_suspended))
        ) and first_state != "confirmed":
            first_state = "history_unknown"
        current_reason = decision.reason if decision else reason
        if listing.latest:
            identity = identify_row(listing, getattr(listing, "identity_progress", None))
            current_reason = identity.reason or current_reason
        gold, gold_failed = None, False
        if self._gold is not None:
            try:
                gold = self._gold.read(listing_id)
            except GoldDiagnosticReadFailed:
                gold_failed = True
        gold_blocks = gold is not None and gold.state != "qualified"
        if gold_blocks and gold is not None:
            current_reason = gold.reason
        if (
            gold_blocks
            and gold is not None
            and active
            and active.state in {"queued", "blocked", "safe_retry"}
        ):
            state, reason = gold.state, gold.reason
            reasons = tuple(dict.fromkeys((gold.reason, *reasons)))
        if gold_failed and active and active.state in {"queued", "blocked", "safe_retry"}:
            state, reason, current_reason = (
                "waiting",
                "gold_dependency_unavailable",
                "gold_dependency_unavailable",
            )
        label = reason_label(reason)
        if gold_blocks and gold is not None and state in {"waiting", "blocked"}:
            label = gold.label
        return AlertDiagnostic(
            gold=gold,
            gold_failed=gold_failed,
            listing_id=listing_id,
            state=state,
            reason=reason,
            label="Envio incerto; aguardando reconciliação"
            if state in {"authorized", "uncertain", "review"}
            else label,
            first_alert_state=first_state,
            reasons=reasons,
            current_reason=current_reason,
            current_label=gold.label
            if gold_blocks and gold is not None
            else reason_label(current_reason),
            evaluated_at=decision.evaluated_at if decision else None,
            next_action_at=active.next_action if active else (row.next_action if row else None),
            observation_id=observation,
            configuration_revision=financial.get("configuration_revision"),
            valuation_revision=financial.get("evaluation_revision"),
            condition_revision=decision.condition_revision if decision else None,
            displayed_observation_id=displayed,
            matches_displayed_observation=displayed is None
            or observation is None
            or observation == displayed,
            publication_status=decision.publication_status if decision else "missing",
            published_at=published,
            first_alert_deadline=published + timedelta(hours=48)
            if published and decision and decision.publication_status == "trusted"
            else None,
            history=tuple(
                AlertHistory(
                    i.id,
                    i.decision.event.kind if i.decision else "first_eligibility",
                    i.state,
                    i.confirmed_at,
                )
                for i in intents
            ),
            confirmed_at=confirmed.confirmed_at if confirmed else None,
            intent_reference=confirmed.id if confirmed else (active.id if active else None),
        )

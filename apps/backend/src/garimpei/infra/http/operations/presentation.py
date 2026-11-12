"""Translate operational diagnostics into user-facing states without exposing internals."""

STAGES = {
    "listing": "Coleta",
    "valuation": "Avaliação de preços",
    "alert": "Alertas",
    "exploration": "Ofertas disponíveis",
    "maintenance": "Cópias dos dados",
    "inference": "Análise local",
    "media": "Fotografias",
}
STATES = {
    "idle": "Sem trabalho pendente",
    "running": "Em andamento",
    "waiting": "Aguardando prazo",
    "stalled": "Sem avanço recente",
    "suspended": "Recuperação suspensa",
    "unavailable": "Etapa indisponível",
}
REASONS = {
    "no_new_frontier": "A consulta terminou sem informação nova.",
    "capacity_available": "Há espaço na fila para retomar o processamento.",
    "historical_not_measured": "O progresso anterior à adoção deste diagnóstico não foi medido.",
    "stage_unavailable": "Esta etapa ainda não está disponível nesta instalação.",
    "progress_confirmed": "Uma nova informação foi confirmada e preservada.",
    "pending": "Há trabalho aguardando processamento.",
    "access_denied": "Confirme o acesso à fonte nas integrações antes de retomar.",
    "source_transport": "A fonte não respondeu. O progresso confirmado continua preservado.",
    "source_rate_limit": "A fonte pediu uma espera antes da próxima consulta.",
    "source_http_503": "A fonte está temporariamente indisponível.",
    "valuation_publication_failed": "Não foi possível confirmar a avaliação. Os dados anteriores continuam preservados.",
    "explicit_resume": "Você solicitou uma nova tentativa com orçamento limitado.",
    "recovery_barrier": "O intervalo após a restauração precisa ser reconciliado antes de novos envios.",
    "queue_full": "A fila atingiu o limite. O pedido e seu progresso foram preservados.",
    "archive_storage_limit": "Falta espaço para uma nova cópia. As cópias concluídas foram preservadas.",
    "media_pending": "Há fotografias ainda não confirmadas. Consulte a oferta para ver o estado de cada imagem.",
    "media_configuration_required": "A cópia das fotografias precisa de configuração ou espaço. Confira a oferta antes de repetir.",
    "media_attention_required": "Uma fotografia esgotou suas tentativas. Abra a oferta para conferir e solicitar nova obtenção.",
    "analysis_service_unavailable": "A análise local está pausada ou indisponível. Confira seu estado em Integrações.",
    "analysis_pending": "Há análise local pendente; isso não impede as outras etapas.",
}


def status_context(value: dict[str, object]) -> dict[str, object]:
    stages = value.get("stages")
    if isinstance(stages, list):
        for stage in stages:
            stage["label"] = STAGES.get(stage["stage"], "Acompanhamento")
            stage["state_label"] = STATES.get(stage["state"], "Estado a confirmar")
            stage["reason_label"] = REASONS.get(
                stage["reason"],
                "A etapa não conseguiu concluir a tentativa; os dados confirmados continuam preservados.",
            )
    return value

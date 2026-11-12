from garimpei.domain.listing.exploration import Offer

REASONS = {
    "no_photos": "Condição não confirmada: não há fotos para avaliar",
    "waiting_photos": "Aguardando obtenção das fotos para análise",
    "waiting_inference": "Aguardando análise das fotos",
    "insufficient_visual_evidence": "As fotos não permitem concluir a condição; a oferta aguarda revisão",
    "partial_photo_coverage": "Parte das fotos não foi analisada; condição não confirmada",
    "unresolved_conflict": "Há suspeita ou conflito de evidências que requer revisão",
    "unsupported_category": "Categoria ou critérios insuficientes para concluir a condição",
    "identity_conflict": "A identidade apresenta conflito; não foi confirmada pelas fotos",
    "function_not_declared": "O funcionamento não foi declarado; aparência não comprova funcionamento",
    "not_tested": "O anúncio informa que o produto não foi testado",
    "functional_failure": "O anúncio informa falha funcional",
    "abnormal_power_restriction": "O anúncio informa restrição anormal de energia",
    "power_context_unknown": "O contexto da restrição de energia precisa de revisão",
    "clear_defect": "Defeito declarado ou dano relevante identificado nas evidências",
    "seller_declared_visual_assessment": "Funcionamento declarado pelo vendedor; aparência avaliada nas fotos disponíveis",
    "superseded_input": "Análise anterior não aplicável à entrada vigente",
    "model_unavailable": "Não foi possível concluir a análise local. A oferta aguarda revisão",
    "inference_timeout": "A análise local excedeu o prazo. A oferta aguarda revisão",
    "gpu_resource_unavailable": "Recursos locais de IA indisponíveis. A oferta aguarda revisão",
    "invalid_analysis": "A resposta da análise não apresentou evidência válida. A oferta aguarda revisão",
}


def assessment_context(offer: Offer) -> dict[str, object]:
    assessment = offer.condition.assessment
    if assessment is None:
        return {}
    evidence = []
    for finding in assessment.findings:
        refs = []
        for reference in finding.references:
            photo = next(
                (p for p in assessment.photo_coverage if p["photo_id"] == reference.photo_id), None
            )
            refs.append(
                dict(kind=reference.kind, field=reference.field, quote=reference.quote, photo=photo)
            )
        evidence.append(
            dict(
                dimension=finding.dimension,
                kind=finding.assessment,
                text=finding.description,
                references=refs,
            )
        )
    return dict(
        assessment=assessment,
        assessment_reason=REASONS.get(
            assessment.reason, "Condição não confirmada; a oferta aguarda revisão"
        ),
        assessment_findings=evidence,
        assessment_text=tuple((s.field, s.text) for s in offer.condition.analysis.signals),
        assessment_count=sum(p.get("examined") is True for p in assessment.photo_coverage),
        assessment_total=len(assessment.photo_coverage),
    )

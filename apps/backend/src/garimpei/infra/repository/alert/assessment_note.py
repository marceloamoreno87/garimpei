from uuid import UUID

from garimpei.infra.persistence.assessment_models import ConditionAssessment
from garimpei.infra.repository.listing.assessment_mapper import decode_assessment


def assessment_note(identity: UUID | None, revision: int | None = None) -> str:
    if identity is None:
        return ""
    row = ConditionAssessment.objects.filter(id=identity).first()
    if row is None or not row.result:
        return ""
    assessment = decode_assessment(row.result)
    caveats = "; ".join(f.description for f in assessment.findings if f.assessment == "light_wear")
    return (
        "Condição provável: funcionamento declarado pelo vendedor; aparência avaliada nas fotos disponíveis."
        + (" Ressalvas: " + caveats if caveats else "")
        + " Avaliação "
        + str(identity)
        + " revisão "
        + str(revision if revision is not None else assessment.revision)
        + "."
    )

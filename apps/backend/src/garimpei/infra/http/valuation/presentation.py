from garimpei.domain.valuation.identity_ports import IdentityView
from garimpei.infra.http.valuation.identity_forms import FAMILY_LABELS, IdentityForm

STATE_LABELS = {
    "identified": "Identidade reconhecida",
    "missing_attribute": "Falta um atributo determinante",
    "unsupported_family": "Modelo sem suporte de comparação",
    "conflicting_identity": "Há informações de identidade em conflito",
    "excluded_item": "Acessório, peça ou conjunto fora da comparação",
    "unrecognized": "Produto não reconhecido",
}
ATTRIBUTE_LABELS = {
    "family": "Família",
    "model": "Modelo",
    "generation": "Versão",
    "edition": "Edição",
    "capacity": "Capacidade",
    "brand": "Marca",
    "memory_type": "Tipo de memória",
}


def identity_context(view: IdentityView, action_url: str) -> dict[str, object]:
    value = view.result
    initial: dict[str, object] = (
        dict(view.manual_values)
        if view.manual_values
        else {a.name: a.value for a in value.attributes}
    )
    initial.update(
        action="resolve" if value.conflicts and view.manual_values else "save",
        observed_revision=value.input_revision,
        manual_revision=value.manual_revision,
    )
    return dict(
        product_identity=view,
        identity_label=STATE_LABELS[value.state],
        identity_attributes=tuple(
            dict(
                label=ATTRIBUTE_LABELS.get(a.name, a.name),
                value=attribute_value(a.name, a.value),
                origin="Sua correção" if a.origin == "manual" else "Anúncio",
                quote=a.quote,
                field=a.field,
                recorded_at=a.recorded_at,
                reviewed_revision=a.reviewed_revision,
            )
            for a in value.attributes
        ),
        identity_missing=tuple(ATTRIBUTE_LABELS.get(x, x) for x in value.missing_attributes),
        identity_form=IdentityForm(initial=initial),
        identity_action_url=action_url,
    )


def attribute_value(name: str, value: str) -> str:
    if name == "family":
        return FAMILY_LABELS.get(value, value)
    if name == "capacity" or name == "memory_type":
        return value.upper()
    return {
        "disc": "Com leitor de disco",
        "standard": "Padrão",
        "promax": "Pro Max",
        "body": "Somente o corpo",
    }.get(value, value)

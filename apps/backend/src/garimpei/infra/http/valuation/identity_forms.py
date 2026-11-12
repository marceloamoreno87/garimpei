from django import forms

from garimpei.domain.valuation.product_catalog import REQUIRED

FAMILY_LABELS = {
    "playstation5": "PlayStation 5",
    "iphone": "iPhone",
    "xbox": "Xbox Series",
    "switch": "Nintendo Switch",
    "graphics_card": "Placa RTX",
    "camera": "Corpo de câmera",
    "television": "TV de modelo conhecido",
    "headphone": "Fone de modelo conhecido",
}


class IdentityForm(forms.Form):
    action = forms.ChoiceField(
        choices=(("save", "Salvar"), ("resolve", "Revisar")), widget=forms.HiddenInput
    )
    observed_revision = forms.IntegerField(
        min_value=0, max_value=2**63 - 1, widget=forms.HiddenInput
    )
    manual_revision = forms.IntegerField(min_value=0, max_value=2**63 - 1, widget=forms.HiddenInput)
    family = forms.ChoiceField(
        label="Família",
        choices=(("", "Selecione a família"), *[(key, FAMILY_LABELS[key]) for key in REQUIRED]),
        required=False,
    )
    model = forms.CharField(
        label="Modelo",
        max_length=120,
        required=False,
        help_text="Use somente o modelo examinado, por exemplo ps5, 13, 4060 ou tune520bt.",
    )
    generation = forms.ChoiceField(
        label="Versão do aparelho",
        required=False,
        choices=(
            ("", "Selecione a versão"),
            ("slim", "Slim"),
            ("fat", "Original (Fat)"),
            ("pro", "Pro"),
            ("oled", "OLED"),
            ("lite", "Lite"),
            ("v1", "V1"),
            ("v2", "V2"),
        ),
    )
    edition = forms.ChoiceField(
        label="Edição ou mídia",
        required=False,
        choices=(
            ("", "Selecione a edição"),
            ("disc", "Com leitor de disco"),
            ("digital", "Digital"),
            ("standard", "Padrão"),
            ("pro", "Pro"),
            ("promax", "Pro Max"),
            ("mini", "Mini"),
            ("plus", "Plus"),
            ("body", "Somente o corpo"),
        ),
    )
    capacity = forms.CharField(
        label="Capacidade",
        max_length=120,
        required=False,
        help_text="Exemplos de formato: 128gb, 825gb ou 1tb. Não inclua memória externa.",
    )
    brand = forms.CharField(label="Marca", max_length=120, required=False)
    memory_type = forms.ChoiceField(
        label="Tipo de memória da placa",
        required=False,
        choices=(("", "Não especificado"), ("gddr6", "GDDR6"), ("gddr6x", "GDDR6X")),
        help_text="Preencha quando o modelo diferencia o tipo de memória.",
    )
    resolution = forms.ChoiceField(
        choices=(
            ("", ""),
            ("keep_manual", "Manter minha correção"),
            ("use_observed", "Usar somente o anúncio"),
            ("correct", "Salvar os valores revisados"),
        ),
        required=False,
        widget=forms.HiddenInput,
    )

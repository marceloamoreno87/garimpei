import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal

from garimpei.domain.monitoring.errors import MonitoringError


def normalize_cep(raw: str) -> str:
    value = raw.strip()
    if not re.fullmatch(r"[0-9]{5}-?[0-9]{3}", value):
        raise MonitoringError(f"CEP {raw!r} inválido. Use 01001-000 ou oito dígitos.", "cep")
    return value.replace("-", "")


def parse_cost(raw: str, field: str) -> Decimal:
    value = raw.strip()
    maximum = Decimal("100") if field == "resale_fee_percent" else Decimal("999999.99")
    if not re.fullmatch(r"[0-9]+([.,][0-9]{1,2})?", value) or len(value) > 32:
        raise MonitoringError(
            f"Valor {raw!r} inválido. Informe de 0 a {maximum}, com até duas casas decimais.", field
        )
    number = Decimal(value.replace(",", "."))
    if number > maximum:
        raise MonitoringError(f"Valor {raw!r} fora do intervalo esperado: 0 a {maximum}.", field)
    return number.quantize(Decimal("0.01"))


@dataclass(frozen=True)
class Interest:
    kind: str
    key: str
    label: str

    @classmethod
    def product(cls, raw: str) -> "Interest":
        name = " ".join(unicodedata.normalize("NFC", raw).split())
        if not 1 <= len(name) <= 120:
            raise MonitoringError(
                f"Nome/modelo {raw!r} inválido. Informe de 1 a 120 caracteres.", "product_names"
            )
        return cls("product", name.casefold(), name)


@dataclass(frozen=True)
class Category:
    id: str
    label: str
    parent_id: str | None
    source_url: str
    selectable: bool = True


@dataclass(frozen=True)
class CategoryCatalog:
    verified_at: str
    evidence_url: str
    entries: tuple[Category, ...]

    def select(self, key: str) -> Interest:
        entry = next((x for x in self.entries if x.id == key and x.selectable), None)
        if entry is None:
            raise MonitoringError(
                f"Categoria {key!r} inválida. Selecione uma categoria disponível da fonte.",
                "category_ids",
            )
        return Interest("category", entry.id, entry.label)

    def path(self, entry: Category) -> str:
        if entry.parent_id is None:
            return entry.label
        parent = next(x for x in self.entries if x.id == entry.parent_id)
        return f"{self.path(parent)} / {entry.label}"

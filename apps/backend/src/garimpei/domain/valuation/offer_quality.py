import re
from decimal import Decimal

from garimpei.domain.listing.condition import normalized
from garimpei.domain.listing.listing import Evidence, money


def installment_price(text: str, price: Decimal) -> bool:
    labels = re.findall(r"(?:parcela\s*(?:de)?|\d+x\s*(?:de)?)\s*(r\$\s*[0-9.,]+)", text)
    return any(money(label.upper().rstrip(".")) == price for label in labels)


def ambiguous_purchase(evidence: Evidence) -> bool:
    text = normalized((evidence.title or "") + " " + (evidence.description or ""))
    if re.search(r"\b(?:entrada de|somente troca|apenas troca|valor (?:da |de )?parcela)\b", text):
        return True
    return evidence.price is not None and installment_price(text, evidence.price)

import re
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from statistics import median

from garimpei.domain.listing.condition import automatic_condition, normalized
from garimpei.domain.valuation.offer_quality import installment_price
from garimpei.domain.valuation.values import Comparable, NewQuote, NewReference, Resale

VALUATION_POLICY = "exact-electronics-v2"
USED_WINDOW = timedelta(days=14)
NEW_WINDOW = timedelta(days=7)


def eligible(candidate: Comparable, product: str, now: datetime) -> bool:
    evidence = candidate.evidence
    text = normalized((evidence.title or "") + " " + (evidence.description or ""))
    positive = re.search(
        r"\b(funcionando (perfeitamente|normalmente)|testado e funcionando|"
        r"funcionamento 100\s*%|100\s*% funcional|funciona (bem|perfeitamente))",
        text,
    )
    negative = re.search(
        r"\b(nao (?:esta )?funciona\w*|nao liga|com defeito|defeituoso|"
        r"precisa de reparo|para pecas|trincos?|trincad\w*|entrada de|somente troca|"
        r"apenas troca|lote de|somente pecas|somente controle|controle avulso)\b",
        text,
    )
    return (
        candidate.product == product
        and normalized(evidence.condition or "").startswith("usado")
        and evidence.source_available is True
        and candidate.price is not None
        and candidate.price.is_finite()
        and candidate.price > 0
        and timedelta() <= now - candidate.observed_at <= USED_WINDOW
        and automatic_condition(evidence).condition == "good"
        and positive is not None
        and not _accessory_only(text, positive.start())
        and negative is None
        and not re.search(
            r"\b(lote|[2-9]\s*(?:unidades|consoles|aparelhos|ps5|playstation))\b", text
        )
        and not installment_price(text, candidate.price)
    )


def estimate(target: Comparable, candidates: tuple[Comparable, ...], now: datetime) -> Resale:
    product = target.product
    if product is None:
        return Resale(None, target.identity_reason, (), 0, 0, None)
    latest: dict[tuple[str, str], Comparable] = {}
    for row in candidates:
        key = (row.source, row.external_id)
        previous = latest.get(key)
        if row.observed_at <= now and (
            previous is None
            or (row.observed_at, row.revision) > (previous.observed_at, previous.revision)
        ):
            latest[key] = row
    accepted = tuple(
        row
        for row in latest.values()
        if row.listing_id != target.listing_id
        and (row.source, row.external_id) != (target.source, target.external_id)
        and eligible(row, product, now)
    )
    before = len(accepted)
    if not accepted:
        return Resale(None, "amostra_insuficiente", (), before, 0, None)
    preliminary = Decimal(median([row.price for row in accepted if row.price is not None]))
    retained = tuple(
        row
        for row in accepted
        if row.price is not None and preliminary / 2 <= row.price <= preliminary * Decimal("1.5")
    )
    prices = [row.price for row in retained if row.price is not None]
    reason = (
        "amostra_insuficiente"
        if len(prices) < 5
        else "amostra_dispersa"
        if max(prices) > min(prices) * Decimal("1.5")
        else None
    )
    price = (
        Decimal(median(prices)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
        if reason is None
        else None
    )
    validity = min((row.observed_at + USED_WINDOW for row in retained), default=None)
    return Resale(price, reason, retained, before, len(retained), validity)


def new_reference(
    product: str,
    offers: tuple[NewQuote, ...],
    failed: bool,
    previous: NewQuote | None,
    now: datetime,
) -> NewReference:
    valid = tuple(quote for quote in offers if _valid_quote(quote, product, now))
    if failed:
        fallback = previous if previous and _valid_quote(previous, product, now) else None
        return NewReference(
            "disponivel" if fallback else "fonte_indisponivel", fallback, "source_failed"
        )
    if not valid:
        return NewReference("sem_referencia")
    return NewReference("disponivel", min(valid, key=lambda quote: (quote.price, quote.url)))


def _valid_quote(quote: NewQuote, product: str, now: datetime) -> bool:
    return (
        quote.product == product
        and quote.currency == "BRL"
        and quote.available
        and quote.price.is_finite()
        and quote.price > 0
        and timedelta() <= now - quote.observed_at <= NEW_WINDOW
    )


def _accessory_only(text: str, position: int) -> bool:
    clause = re.split(r"[.!?\n]", text[:position])[-1][-40:]
    return "controle" in clause and not re.search(r"console|aparelho|ps5|playstation", clause)

from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from garimpei.domain.alert.alert import AlertMessage, Binding, Receipt


def eligibility(
    kind: str,
    silent: bool,
    covered: bool,
    matched: bool,
    condition: str,
    previous_confirmed: bool,
    previous_pending: bool,
) -> str:
    if silent:
        return "silent"
    if kind not in {"discovered", "price_decreased"}:
        return "unsupported_event"
    if not covered:
        return "coverage_unconfirmed"
    if not matched:
        return "interest_unconfirmed"
    if condition != "good":
        return "condition_excluded"
    if kind == "discovered":
        return "eligible"
    if previous_pending:
        return "waiting_previous"
    return "eligible" if previous_confirmed else "no_previous_confirmation"


def brl(value: Decimal) -> str:
    number = f"{abs(value):,.2f}".translate(str.maketrans(",.", ".,"))
    return ("-" if value < 0 else "") + "R$ " + number


def message_text(value: AlertMessage) -> str:
    header = "Nova oferta" if value.kind == "discovered" else "Preço reduzido"
    price = brl(value.price)
    if value.previous_price is not None and value.kind == "price_decreased":
        price = brl(value.previous_price) + " → " + price
    observed = value.observed_at.astimezone(ZoneInfo("America/Sao_Paulo"))
    profit_label = (
        "Lucro potencial antes de frete/transporte"
        if value.profit_policy == "potential-before-freight-v2"
        else "Lucro estimado (regra anterior)"
    )
    return "\n".join(
        (
            header + " · " + " ".join(value.title.split()),
            value.source,
            "Compra: " + price,
            profit_label + ": " + brl(value.profit),
            observed.strftime("Observado em %d/%m/%Y às %H:%M (São Paulo)"),
            value.url,
            "Ref. " + str(value.reference),
        )
    )


def verified_receipt(value: Receipt, binding: Binding, body: str) -> bool:
    return bool(
        value.id
        and value.outgoing
        and value.chat == binding.recipient
        and value.body == body
        and 1 <= value.ack <= 4
    )


def pricing_decision(reason: str, observed_at: datetime, now: datetime) -> tuple[str, str]:
    if reason not in {"amostra_insuficiente", "amostra_dispersa", "evidencia_vencida"}:
        return "excluded", reason
    if now - observed_at >= timedelta(hours=48):
        return "excluded", "reference_wait_expired"
    return "waiting", reason

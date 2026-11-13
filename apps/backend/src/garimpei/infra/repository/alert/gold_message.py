from garimpei.infra.persistence.alert_models import AlertIntent
from garimpei.infra.repository.valuation.mapper import mapping, records


def gold_message_note(row: AlertIntent) -> str:
    if row.gold_qualification_id is None:
        return ""
    gold = row.gold_qualification
    if gold is None:
        return ""
    valuation = mapping(gold.evidence.get("valuation") or {})
    resale = mapping(valuation.get("resale") or {})
    comparables = records(resale.get("comparables") or [])
    dates = sorted(str(item["observed_at"])[:10] for item in comparables)
    period = " a ".join((dates[0], dates[-1])) if dates else "não disponível"
    links = "\n".join(str(item["url"]) for item in comparables[:5])
    return (
        "Produto normalizado: "
        + str(gold.evidence["canonical_name"])
        + "\nBase histórica: "
        + str(resale.get("after", 0))
        + " anúncios usados equivalentes; mediana dos preços pedidos."
        + "\nData-base: "
        + period
        + "; política "
        + gold.policy
        + "."
        + "\nCondição provável; preço pedido não comprova venda nem garante lucro."
        + ("\nReferências: \n" + links if links else "")
    )

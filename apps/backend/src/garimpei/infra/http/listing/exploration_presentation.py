from dataclasses import replace
from typing import TypedDict, Unpack
from urllib.parse import urlencode, urlsplit
from uuid import UUID

from garimpei.domain.listing.exploration import Criteria, Offer, OfferPage, money_label
from garimpei.domain.valuation.identity import identify
from garimpei.infra.http.listing.condition_presentation import TABS


class ContextChanges(TypedDict, total=False):
    tab: str
    query: str
    category: str
    modality: str
    page: int
    version: UUID | None


def url(criteria: Criteria, path: str = "/ofertas/", **changes: Unpack[ContextChanges]) -> str:
    value = replace(criteria, **changes)
    data = {
        "aba": value.tab,
        "q": value.query,
        "categoria": value.category,
        "pagina": str(value.page),
    }
    if value.version:
        data["versao"] = str(value.version)
    return path + "?" + urlencode(data)


def safe_url(value: str) -> str:
    parsed = urlsplit(value)
    return (
        value
        if parsed.scheme == "https"
        and parsed.hostname
        and not parsed.username
        and not parsed.password
        else ""
    )


def card(offer: Offer, criteria: Criteria) -> dict[str, object]:
    composition = offer.composition
    result: dict[str, object] = dict(
        offer=offer,
        source_label="Facebook Marketplace"
        if offer.source == "facebook_marketplace"
        else offer.source,
        title=offer.title,
        identity=str(offer.id),
        key=offer.external_id,
        price=money_label(composition.purchase.value)
        if composition.purchase.value is not None
        else "Preço não informado",
        profit=money_label(composition.profit.value if complete_components(offer) else None),
        profit_label="Lucro estimado",
        profit_scope="Revisão histórica da estimativa"
        if composition.policy == "profit-brl-v1"
        else "",
        complete_profit_label="Lucro estimado",
        resale=money_label(composition.resale.value),
        finance_reason=reason_label(composition.resale.reason),
        detail_url=url(criteria, f"/ofertas/{offer.id}/"),
        url=safe_url(offer.url),
    )
    if not compatible_composition(offer):
        result.update(
            price=money_label(offer.evidence.price),
            resale="Indisponível",
            profit="Indisponível",
            finance_reason="A composição não corresponde à revisão desta oferta",
        )
    from garimpei.infra.http.media.presentation import media_context

    result.update(media_context(offer, url(criteria, f"/ofertas/{offer.id}/imagens/reprocessar/")))
    return result


def complete_components(offer: Offer) -> bool:
    value = offer.composition
    return all(
        component is not None
        for component in (
            value.purchase.value,
            value.resale.value,
            value.fee.value,
            value.fee_percent,
        )
    )


def compatible_composition(offer: Offer) -> bool:
    value = offer.composition
    return (
        value.listing_id == offer.id
        and offer.observation_id is not None
        and value.observation_id == offer.observation_id
        and value.purchase.value == offer.evidence.price
        and value.currency == "BRL"
        and (value.resale.value is None or compatible_valuation(offer))
    )


def compatible_valuation(offer: Offer) -> bool:
    valuation = offer.valuation
    return bool(
        valuation is not None
        and valuation.listing_id == offer.id
        and valuation.id == offer.composition.evaluation_id
        and valuation.revision == offer.composition.evaluation_revision
        and valuation.product
        == (offer.identification.product_key if offer.identification else identify(offer.evidence))
        and valuation.resale.price == offer.composition.resale.value
    )


def list_context(page: OfferPage, labels: dict[str, str]) -> dict[str, object]:
    criteria = page.criteria
    return dict(
        listing_page=True,
        page=page,
        criteria=criteria,
        cards=tuple(card(o, criteria) for o in page.offers),
        tabs=tuple(
            dict(key=k, label=label, count=count, url=url(criteria, tab=k, page=1))
            for (k, label), count in zip(TABS, page.counts, strict=True)
        ),
        categories=tuple(labels.items()),
        canonical=url(criteria),
        previous=url(criteria, page=max(1, criteria.page - 1)),
        next=url(criteria, page=criteria.page + 1),
        refresh=url(criteria, version=None),
        clear=url(criteria, query="", category="", modality="todas", page=1),
        status_url=url(criteria, "/ofertas/atualizacoes/"),
    )


def detail_context(offer: Offer, criteria: Criteria) -> dict[str, object]:
    value = card(offer, criteria)
    composition = offer.composition
    valuation = offer.valuation
    refs = valuation.resale.comparables if valuation else ()
    quote = valuation.new.quote if valuation else None
    value.update(
        listing_page=True,
        criteria=criteria,
        back=url(criteria),
        refresh=url(criteria, f"/ofertas/{offer.id}/", version=None),
        status_url=url(criteria, "/ofertas/atualizacoes/"),
        condition_url=url(criteria, f"/ofertas/{offer.id}/condicao/"),
        destination=url(criteria, tab=offer.condition.tab, page=1),
        fee=money_label(composition.fee.value)
        if composition.fee.value is not None
        else "Indisponível",
        percent=str(composition.fee_percent).replace(".", ",")
        if composition.fee_percent is not None
        else "Não configurada",
        references=tuple(
            dict(
                title=r.title,
                source="Facebook Marketplace" if r.source == "facebook_marketplace" else r.source,
                key=r.external_id,
                date=r.observed_at,
                url=safe_url(r.url),
                price=money_label(r.price),
            )
            for r in refs
        ),
        new=dict(
            title=quote.title,
            source=quote.source,
            key=quote.external_id,
            date=quote.observed_at,
            url=safe_url(quote.url),
            price=money_label(quote.price),
        )
        if quote
        else None,
        reason=reason_label(
            composition.purchase.reason
            or composition.resale.reason
            or composition.fee.reason
            or composition.profit.reason
        ),
    )
    if not compatible_composition(offer):
        value.update(
            fee="Indisponível",
            percent="Não disponível",
            reason="Composição indisponível para esta revisão",
        )
    return value


def reason_label(reason: str | None) -> str | None:
    if reason is None:
        return None
    return {
        "preco_parcial_ou_troca": "O anúncio informa entrada, parcela ou somente troca; o preço total de compra não está confirmado",
        "aguardando_avaliacao": "A avaliação de preços ainda está em andamento",
        "amostra_insuficiente": "Ainda não há comparáveis usados suficientes",
        "amostra_dispersa": "Os preços da amostra variam demais para estimar a revenda",
        "familia_sem_suporte": "A família ou modelo ainda não tem suporte de comparação",
        "atributo_ausente": "Falta um atributo determinante para identificar o produto",
        "identidade_em_conflito": "Revise os atributos de identidade em conflito",
        "item_excluido": "Acessório, peça ou conjunto fora da comparação",
        "produto_indeterminado": "O modelo e a variante do produto ainda não foram identificados",
        "produto_incompativel": "A avaliação disponível corresponde a outra variante",
        "evidencia_vencida": "As referências de preços precisam ser atualizadas",
        "compra_indisponivel": "O preço de compra ainda não está confirmado",
        "taxa_nao_configurada": "Configure a taxa de revenda para estimar o lucro",
        "modalidade_indisponivel": "A cobertura de retirada ou envio ainda não foi confirmada",
    }.get(reason, "Os dados necessários ainda não estão completos")

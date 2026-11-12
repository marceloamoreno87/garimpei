"""A fixed presentation keeps its ordering, but cannot expose invalid current profits."""

from dataclasses import replace

from garimpei.domain.listing.exploration import Offer
from garimpei.domain.valuation.profit import Component
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.repository.valuation.identity_mapper import identify_row


def identity_overlay(offer: Offer, listing: Listing) -> Offer:
    if listing.latest is None:
        return offer
    current = identify_row(listing, getattr(listing, "identity_progress", None))
    previous = offer.identification
    revision_changed = current.manual_revision != (previous.manual_revision if previous else 0)
    if current.state == "identified" and not revision_changed:
        return offer
    reason = current.reason or "aguardando_avaliacao"
    absent = Component(None, "indisponivel", "identity", reason)
    value = offer.composition
    value = replace(
        value,
        resale=absent,
        fee=absent,
        modalities=tuple(replace(m, profit=absent, reasons=(reason,)) for m in value.modalities),
        reasons=(reason,),
    )
    valuation = offer.valuation
    if valuation:
        valuation = replace(
            valuation,
            resale=replace(valuation.resale, price=None, reason=reason),
            identification=current,
        )
    return replace(offer, composition=value, valuation=valuation, identification=current)

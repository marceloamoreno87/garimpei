"""Versioned exploration contracts. Manual condition is the only live overlay."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from garimpei.domain.listing.condition import ConditionState, normalized
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.media.media import MediaGallery
from garimpei.domain.valuation.profit import ProfitComposition
from garimpei.domain.valuation.values import Valuation


class ExplorationError(Exception):
    status = 503
    message = "Não foi possível consultar as ofertas. Tente novamente."


class InvalidExplorationInput(ExplorationError):
    status = 400

    def __init__(
        self, message: str = "Filtro inválido: use uma aba, modalidade e página válidas."
    ) -> None:
        self.message = message
        super().__init__(message)


class ExpiredExploration(ExplorationError):
    status = 410
    message = "Esta revisão expirou. Carregue a versão atual para continuar."


def money_label(value: Decimal | None) -> str:
    if value is None:
        return "Estimativa indisponível"
    number = f"{abs(value):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return ("−" if value < 0 else "") + "R$ " + number


@dataclass(frozen=True)
class Criteria:
    tab: str = "funcionam"
    query: str = ""
    category: str = ""
    modality: str = "todas"
    page: int = 1
    version: UUID | None = None

    @property
    def search(self) -> str:
        return normalized(self.query)

    @classmethod
    def parse(cls, values: Mapping[str, str]) -> "Criteria":
        tab, mode = values.get("aba", "funcionam"), values.get("modalidade", "todas")
        page, query = values.get("pagina", "1"), values.get("q", "")
        if tab not in {"funcionam", "defeitos", "incerta"} or mode not in {
            "todas",
            "retirada",
            "envio",
        }:
            raise InvalidExplorationInput()
        if not re.fullmatch(r"[1-9][0-9]{0,8}", page) or len(query) > 120:
            raise InvalidExplorationInput(
                "Entrada inválida: busca até 120 caracteres e página inteira positiva até 999999999."
            )
        raw = values.get("versao", "")
        if raw and not re.fullmatch(r"[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}", raw):
            raise InvalidExplorationInput("Revisão inválida: esperado UUID publicado.")
        return cls(
            tab, query, values.get("categoria", ""), "todas", int(page), UUID(raw) if raw else None
        )

    def at(self, version: UUID | None, page: int | None = None) -> "Criteria":
        return replace(self, version=version, page=self.page if page is None else page)


@dataclass(frozen=True)
class Offer:
    id: UUID
    external_id: str
    source: str
    url: str
    first_seen_at: datetime
    observed_at: datetime
    evidence: Evidence
    condition: ConditionState
    categories: tuple[str, ...]
    pickup: bool
    shipping: bool
    visible: bool
    composition: ProfitComposition
    valuation: Valuation | None
    unavailable: bool = False
    last_valid_at: datetime | None = None
    observation_id: UUID | None = None
    media: MediaGallery | None = None

    @property
    def title(self) -> str:
        return self.evidence.title or "Anúncio sem título informado"


@dataclass(frozen=True)
class OfferPage:
    criteria: Criteria
    offers: tuple[Offer, ...]
    total: int
    pages: int
    counts: tuple[int, ...]
    published_at: datetime | None

    @property
    def start(self) -> int:
        return (self.criteria.page - 1) * 20 + 1 if self.total else 0

    @property
    def end(self) -> int:
        return min(self.criteria.page * 20, self.total)


class ExplorationReader(Protocol):
    def page(self, criteria: Criteria) -> OfferPage: ...
    def detail(self, identity: UUID, version: UUID | None) -> tuple[Offer | None, UUID | None]: ...
    def updates(self, version: UUID | None) -> tuple[bool, bool]: ...


class ExplorationPublisher(Protocol):
    def publish(self, now: datetime) -> UUID | None: ...

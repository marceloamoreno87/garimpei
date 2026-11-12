import uuid
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal

from garimpei.domain.monitoring.errors import ConfigurationConflict, MonitoringError
from garimpei.domain.monitoring.values import Interest, normalize_cep, parse_cost


@dataclass(frozen=True)
class MonitoringConfiguration:
    id: uuid.UUID
    slot: str = "draft"
    revision: int = 0
    cep: str | None = None
    shipping_estimate: Decimal | None = None
    resale_fee_percent: Decimal | None = None
    interests: tuple[Interest, ...] = ()
    completed_at: datetime | None = None
    completion_revision: int | None = None

    @classmethod
    def create(cls) -> "MonitoringConfiguration":
        return cls(id=uuid.uuid4())

    @property
    def next_step(self) -> str:
        if self.cep is None:
            return "regiao"
        if self.resale_fee_percent is None:
            return "custos"
        return "interesses"

    def save_region(self, cep: str, revision: int) -> "MonitoringConfiguration":
        return self._change(replace(self, cep=normalize_cep(cep)), revision)

    def save_costs(self, shipping: str, fee: str, revision: int) -> "MonitoringConfiguration":
        candidate = replace(
            self,
            shipping_estimate=parse_cost(shipping, "shipping_estimate")
            if shipping.strip()
            else None,
            resale_fee_percent=parse_cost(fee, "resale_fee_percent"),
        )
        return self._change(candidate, revision)

    def save_interests(
        self, interests: tuple[Interest, ...], revision: int
    ) -> "MonitoringConfiguration":
        unique = {(item.kind, item.key): item for item in reversed(interests)}
        normalized = tuple(unique[key] for key in sorted(unique))
        return self._change(replace(self, interests=normalized), revision)

    def publish(self, revision: int) -> "MonitoringConfiguration":
        self._require_complete()
        if revision != self.revision:
            raise ConfigurationConflict()
        return replace(
            self,
            slot="active",
            revision=1,
            completed_at=datetime.now(UTC),
            completion_revision=revision,
        )

    def update(
        self, cep: str, shipping: str, fee: str, interests: tuple[Interest, ...], revision: int
    ) -> "MonitoringConfiguration":
        # Validate the candidate independently; only the final whole version is published.
        candidate = replace(self, revision=0)
        candidate = candidate.save_region(cep, candidate.revision)
        candidate = candidate.save_costs(shipping, fee, candidate.revision)
        candidate = candidate.save_interests(interests, candidate.revision)
        candidate._require_complete()
        return self._change(replace(candidate, revision=self.revision), revision)

    def _require_complete(self) -> None:
        if self.cep is None:
            raise MonitoringError("Informe um CEP com oito dígitos.", "cep")
        if self.resale_fee_percent is None:
            raise MonitoringError(
                "Preencha o percentual provisório de revenda.", "resale_fee_percent"
            )
        if not self.interests:
            raise MonitoringError("Selecione uma categoria ou informe um nome/modelo.")

    def _change(
        self, candidate: "MonitoringConfiguration", revision: int
    ) -> "MonitoringConfiguration":
        if candidate == self and 0 <= revision <= self.revision:
            return self
        if revision != self.revision:
            raise ConfigurationConflict()
        return replace(candidate, revision=self.revision + 1)

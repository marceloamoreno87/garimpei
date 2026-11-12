from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.identification_values import AttributeConflict
from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.product_catalog import product_title, validated_values


@dataclass(frozen=True)
class ManualIdentity:
    values: tuple[tuple[str, str], ...]
    revision: int
    reviewed_revision: int
    recorded_at: datetime
    reviewed_conflicts: tuple[str, ...] = ()
    reviewed_observation_id: UUID | None = None

    @classmethod
    def create(
        cls,
        values: Mapping[str, str],
        *,
        revision: int,
        reviewed_revision: int,
        recorded_at: datetime,
    ) -> "ManualIdentity":
        return cls(validated_values(values), revision, reviewed_revision, recorded_at)

    @property
    def product_key(self) -> str:
        result = identify(Evidence(title=product_title(dict(self.values))))
        assert result is not None
        return result

    def review(
        self,
        conflicts: tuple[AttributeConflict, ...],
        *,
        reviewed_revision: int,
        recorded_at: datetime,
    ) -> "ManualIdentity":
        return replace(
            self,
            revision=self.revision + 1,
            reviewed_revision=reviewed_revision,
            recorded_at=recorded_at,
            reviewed_conflicts=tuple(
                sorted({*self.reviewed_conflicts, *(conflict.review_key for conflict in conflicts)})
            ),
        )

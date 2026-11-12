from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class MonitoringSnapshot:
    configured: bool = False
    configuration_id: UUID | None = None
    revision: int | None = None
    completed_at: datetime | None = None
    source: str = "facebook_marketplace"
    cep: str | None = None
    pickup_city: str = "São Paulo"
    pickup_state: str = "SP"
    pickup_radius_km: int = 20
    shipping_scope: str = "BR"
    category_ids: tuple[str, ...] = ()
    product_names: tuple[str, ...] = ()
    shipping_estimate: Decimal | None = None
    resale_fee_percent: Decimal | None = None

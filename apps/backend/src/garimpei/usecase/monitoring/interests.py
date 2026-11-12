from garimpei.domain.monitoring.ports import CatalogGateway
from garimpei.domain.monitoring.values import Interest


def resolve_interests(
    gateway: CatalogGateway,
    category_ids: tuple[str, ...],
    product_names: tuple[str, ...],
    existing: tuple[Interest, ...] = (),
) -> tuple[Interest, ...]:
    products = tuple(Interest.product(name) for name in product_names)
    if not category_ids:
        return products
    retained = {item.key: item for item in existing if item.kind == "category"}
    new_ids = set(category_ids) - retained.keys()
    catalog = gateway.load() if new_ids else None
    categories = tuple(retained[key] for key in sorted(set(category_ids)) if key in retained)
    if catalog is not None:
        categories += tuple(catalog.select(key) for key in sorted(new_ids))
    return categories + products

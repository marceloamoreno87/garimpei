from garimpei.domain.monitoring.values import Interest


class PreviewProductsUseCase:
    def execute(self, names: tuple[str, ...]) -> tuple[str, ...]:
        products = [Interest.product(name) for name in names]
        unique = {item.key: item.label for item in reversed(products)}
        return tuple(unique[key] for key in sorted(unique))

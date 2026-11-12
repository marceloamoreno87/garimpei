from unicodedata import category, normalize


def tokens(value: str) -> tuple[str, ...]:
    normalized = normalize("NFKD", normalize("NFKC", value).casefold())
    return tuple(
        "".join(
            character if character.isalnum() else " "
            for character in normalized
            if not category(character).startswith("M")
        ).split()
    )


def matches_product(product: str, title: str) -> bool:
    expected = tokens(product)
    actual = tokens(title)
    return bool(expected) and any(
        actual[start : start + len(expected)] == expected for start in range(len(actual))
    )

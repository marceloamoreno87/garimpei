import unicodedata


def normalize_text(text: str) -> str:
    value = unicodedata.normalize("NFKD", unicodedata.normalize("NFKC", text).casefold())
    return " ".join("".join(char for char in value if not unicodedata.combining(char)).split())

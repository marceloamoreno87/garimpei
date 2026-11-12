import re
from urllib.parse import urlsplit


def marketplace_id(link: str) -> str | None:
    try:
        parsed = urlsplit(link)
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.netloc.lower() not in {
        "facebook.com",
        "www.facebook.com",
    }:
        return None
    match = re.fullmatch(r"/marketplace/item/([0-9]{1,40})/?", parsed.path)
    return match.group(1) if match else None

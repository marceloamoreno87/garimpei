import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from garimpei.domain.monitoring.errors import CatalogUnavailable
from garimpei.domain.monitoring.values import Category, CategoryCatalog


class FacebookCategoryCatalog:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> CategoryCatalog:
        try:
            return self._parse(json.loads(self._path.read_text()))
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            raise CatalogUnavailable() from error

    def _parse(self, data: dict[str, object]) -> CategoryCatalog:
        if data["source"] != "facebook_marketplace":
            raise ValueError("Unexpected source")
        timestamp = str(data["verified_at"])
        if not timestamp.endswith("Z") or datetime.fromisoformat(timestamp).utcoffset() is None:
            raise ValueError("UTC timestamp required")
        evidence = self._url(data["evidence_url"])
        raw_entries = data["entries"]
        if not isinstance(raw_entries, list) or not raw_entries:
            raise ValueError("Non-empty verified catalog required")
        entries = tuple(self._entry(item) for item in raw_entries)
        self._validate_tree(entries)
        return CategoryCatalog(timestamp, evidence, entries)

    def _entry(self, item: object) -> Category:
        if not isinstance(item, dict):
            raise ValueError("Category object expected")
        identity, label, parent = item["id"], item["label"], item["parent_id"]
        if not isinstance(identity, str) or not 1 <= len(identity) <= 255:
            raise ValueError("Invalid category ID")
        if not isinstance(label, str) or not 1 <= len(label) <= 255:
            raise ValueError("Invalid category label")
        if parent is not None and not isinstance(parent, str):
            raise ValueError("Invalid parent")
        selectable = item.get("selectable", True)
        if not isinstance(selectable, bool):
            raise ValueError("Invalid selectable flag")
        return Category(identity, label, parent, self._url(item["source_url"]), selectable)

    def _url(self, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Source URL expected")
        url = urlparse(value)
        if (
            url.scheme != "https"
            or url.netloc != "www.facebook.com"
            or not url.path.startswith("/marketplace/")
        ):
            raise ValueError("Facebook Marketplace URL expected")
        return value

    def _validate_tree(self, entries: tuple[Category, ...]) -> None:
        parents = {item.id: item.parent_id for item in entries}
        if len(parents) != len(entries):
            raise ValueError("Duplicate category ID")
        for item in entries:
            self._ancestors(item.id, parents)

    def _ancestors(self, identity: str, parents: dict[str, str | None]) -> None:
        seen: set[str] = set()
        current: str | None = identity
        while current is not None:
            if current in seen or current not in parents:
                raise ValueError("Invalid category hierarchy")
            seen.add(current)
            current = parents[current]

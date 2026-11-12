import json
from pathlib import Path

from garimpei.domain.navigation.catalog import Catalog, Family, Relation


def load_catalog(path: Path) -> Catalog:
    data = json.loads(path.read_text())
    return Catalog(
        str(data["version"]),
        tuple(
            Family(row["family"], row["canonical"], tuple(row["aliases"]), tuple(row["excluded"]))
            for row in data["families"]
        ),
        tuple(Relation(**row) for row in data["relations"]),
    )

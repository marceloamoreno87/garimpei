import json
from pathlib import Path

from garimpei.domain.valuation.research_diagnostic import InterestCoverage

FAMILY_LABELS = {
    "playstation5": "PlayStation 5",
    "iphone": "iPhone",
    "xbox": "Xbox Series",
    "switch": "Nintendo Switch",
    "graphics_card": "Placas RTX",
    "camera": "Câmeras",
    "television": "TVs",
    "headphone": "Fones",
}
ATTRIBUTE_LABELS = {
    "family": "família",
    "model": "modelo",
    "generation": "versão",
    "edition": "edição",
    "capacity": "capacidade",
    "brand": "marca",
    "memory_type": "tipo de memória",
}


def read_interest_corpus(
    path: Path,
) -> tuple[str | None, str | None, tuple[InterestCoverage, ...], str | None]:
    try:
        raw = json.loads(path.read_text())
        analysis_path = path.with_name("coverage-analysis.json")
        analysis = json.loads(analysis_path.read_text()) if analysis_path.is_file() else {}
        valid = analysis.get("corpus_hash") == raw.get("snapshot_hash")
        metrics = (
            {(row["kind"], row["key"]): row for row in analysis.get("interests", [])}
            if valid
            else {}
        )
        coverage = tuple(
            _coverage(row, metrics.get((row["kind"], row["key"]), {}))
            for row in raw.get("interests", [])
        )
        return (
            str(raw.get("captured_at", "")),
            str(raw.get("snapshot_hash", "")),
            coverage,
            str(raw.get("version", "")),
        )
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        return None, None, (), None


def _coverage(row: dict[str, object], metrics: dict[str, object]) -> InterestCoverage:
    from typing import cast

    states = cast(dict[str, int], metrics.get("states", {}))
    valuation = cast(dict[str, int], metrics.get("valuation", {}))
    families = cast(dict[str, int], metrics.get("families", {}))
    attributes = cast(dict[str, int], metrics.get("attributes", {}))
    return InterestCoverage(
        str(row.get("label", row.get("key", ""))),
        int(str(metrics.get("sample_size", row.get("sample_size", 0)))),
        states.get("identified", 0),
        str(row.get("coverage_note", "Suporte restrito ao recorte examinado.")),
        tuple(f"{FAMILY_LABELS.get(key, key)}: {count}" for key, count in sorted(families.items())),
        tuple(
            f"{ATTRIBUTE_LABELS.get(key, key)}: {count}"
            for key, count in sorted(attributes.items())
        ),
        states.get("unsupported_family", 0),
        states.get("missing_attribute", 0),
        states.get("conflicting_identity", 0),
        states.get("unrecognized", 0),
        states.get("excluded_item", 0),
        valuation.get("amostra_insuficiente", 0),
        valuation.get("not_evaluated", 0),
    )

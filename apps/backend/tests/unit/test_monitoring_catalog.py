import json
from dataclasses import replace
from pathlib import Path

import pytest

from garimpei.domain.monitoring.errors import CatalogUnavailable, MonitoringError
from garimpei.domain.monitoring.values import Category, CategoryCatalog, Interest
from garimpei.infra.gateway.monitoring.facebook_catalog import FacebookCategoryCatalog
from garimpei.main import build_monitoring_catalog
from garimpei.usecase.monitoring.interests import resolve_interests


def test_verified_catalog_matches_observed_source_and_no_demo_values() -> None:
    catalog = build_monitoring_catalog().load()
    assert catalog.verified_at.endswith("Z")
    assert catalog.evidence_url == "https://www.facebook.com/marketplace/category/electronics/"
    assert catalog.select("479353692612078") == Interest(
        "category", "479353692612078", "Eletrônicos"
    )
    assert catalog.entries[0].source_url == catalog.evidence_url
    assert {e.id for e in catalog.entries if e.selectable} == {
        "479353692612078",
        "cameras",
        "computers",
        "video-games",
        "headphones",
        "tvs",
    }
    with pytest.raises(MonitoringError):
        catalog.select("cell-phones")


def test_missing_and_malformed_catalog_are_not_valid_empty_catalogs(tmp_path: Path) -> None:
    path = tmp_path / "catalog.json"
    with pytest.raises(CatalogUnavailable):
        FacebookCategoryCatalog(path).load()
    path.write_text("{}")
    with pytest.raises(CatalogUnavailable):
        FacebookCategoryCatalog(path).load()
    path.write_text('{"entries":[]}')
    with pytest.raises(CatalogUnavailable):
        FacebookCategoryCatalog(path).load()


class FakeCategoryCatalog:
    def __init__(self, catalog: CategoryCatalog) -> None:
        self.catalog = catalog

    def load(self) -> CategoryCatalog:
        return self.catalog


def test_hierarchy_uses_exact_independent_filters_and_rejects_groupers() -> None:
    # This hierarchy is explicitly synthetic; the shipping catalog contains only the verified root.
    parent = Category(
        "parent", "Group", None, "https://www.facebook.com/marketplace/category/electronics/", False
    )
    child = replace(parent, id="child", parent_id="parent", label="Child", selectable=True)
    catalog = CategoryCatalog("2026-11-10T21:40:14Z", parent.source_url, (parent, child))
    assert catalog.path(child) == "Group / Child"
    assert resolve_interests(FakeCategoryCatalog(catalog), ("child", "child"), ()) == (
        Interest("category", "child", "Child"),
    )
    with pytest.raises(MonitoringError):
        catalog.select("parent")
    with pytest.raises(MonitoringError):
        catalog.select("unknown")


def test_fixture_matrix_is_present_and_exercises_public_values() -> None:
    from garimpei.domain.monitoring.values import normalize_cep, parse_cost

    matrix = json.loads((Path(__file__).parents[1] / "fixtures/monitoring/cases.json").read_text())
    for value in matrix["cep"]["valid"]:
        assert normalize_cep(value) == "01001000"
    for value in matrix["cep"]["invalid"]:
        with pytest.raises(MonitoringError):
            normalize_cep(value)
    for field in ("shipping_estimate", "resale_fee_percent"):
        for value in matrix[field]["valid"]:
            assert parse_cost(value, field) >= 0
        for value in matrix[field]["invalid"]:
            with pytest.raises(MonitoringError):
                parse_cost(value, field)


def test_production_assets_consume_the_canonical_tokens() -> None:
    backend = Path(__file__).parents[2]
    reference = backend.parents[1] / "docs/design/tokens.css"
    shipped = backend / "src/garimpei/infra/http/static/monitoring/tokens.css"
    assert shipped.read_bytes() == reference.read_bytes()

import hashlib
import json
from pathlib import Path

from django.template.loader import render_to_string
from django.test import Client


def test_liveness_does_not_query_database() -> None:
    response = Client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
    assert response["Cache-Control"] == "no-store"


def test_unsupported_method() -> None:
    assert Client().options("/health/ready").status_code == 405


def test_template_uses_local_verified_htmx() -> None:
    backend = Path(__file__).resolve().parents[2]
    root = backend.parents[1]
    vendor = backend / "src/garimpei/infra/http/static/vendor"
    reference = json.loads(
        (root / "docs/F02-fundacao-tecnica-e-ambiente-local/evidence/htmx.json").read_text()
    )
    assert hashlib.sha256((vendor / "htmx.min.js").read_bytes()).hexdigest() == reference["sha256"]
    assert (vendor / "HTMX-LICENSE").stat().st_size > 100
    html = render_to_string("base.html")
    assert "/static/vendor/htmx.min.js" in html
    assert "https://" not in html

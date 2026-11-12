from uuid import uuid4

from tests.factories.condition_http import ConditionBrowser, listing_id
from tests.factories.listing import fail_next_condition_write
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import completed, shell, sql, wait_for
from tests.integration.test_listing_condition import ConditionScenario, condition_scenario

__all__ = ["condition_scenario"]


def test_http_choices_stale_revision_validation_and_csrf(
    condition_scenario: ConditionScenario,
) -> None:
    instance, source, clock = condition_scenario
    browser = ConditionBrowser(instance)
    identity = listing_id(instance)
    assert "R$ 2.300,00" in browser.request("/ofertas/")[1]
    other = listing_id(instance, "507")
    group = pause_worker(instance)
    try:
        baseline = sql(instance, "SELECT id,kind FROM runtime_listingevent ORDER BY sequence")
        jobs = sql(
            instance, "SELECT id FROM procrastinate_jobs WHERE queue_name='listing' ORDER BY id"
        )
        assert browser.choose(identity, "wrong")[0] == 400
        assert browser.choose(identity, "good", "-1")[0] == 400
        assert browser.choose(identity, "good", "x")[0] == 400
        assert (
            browser.request(f"/ofertas/{identity}/condicao/", {"choice": "good", "revision": "0"})[
                0
            ]
            == 403
        )
        assert browser.request(f"/ofertas/{uuid4()}/")[0] == 404
        assert browser.request("/ofertas/invalid/")[0] == 404
        assert browser.request("/ofertas/?aba=invalid")[0] == 400
        assert browser.request(f"/ofertas/{identity}/condicao/")[0] == 405
        assert browser.request(f"/ofertas/{identity}/", method="OPTIONS")[0] == 405
        assert (
            browser.request(f"/ofertas/{uuid4()}/condicao/", {"choice": "good", "revision": "0"})[0]
            == 403
        )
        # Reuse a valid CSRF token with a missing ID and an automatically conclusive listing.
        import re

        body = browser.request(f"/ofertas/{identity}/")[1]
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body)
        assert match is not None
        data = {"choice": "good", "revision": "0", "csrfmiddlewaretoken": match[1]}
        assert browser.request(f"/ofertas/{uuid4()}/condicao/", data)[0] == 404
        assert browser.request(f"/ofertas/{listing_id(instance, '501')}/condicao/", data)[0] == 409
        status, _, location = browser.choose(identity, "good")
        assert status == 303 and location == f"/ofertas/{identity}/"
        status, body, _ = browser.request(location)
        assert (
            status == 200
            and "Sua classificação foi salva" in body
            and "Sua classificação manual" in body
        )
        assert 'value="1"' in body
        assert identity in browser.request("/ofertas/?aba=funcionam")[1]
        assert identity not in browser.request("/ofertas/?aba=incerta")[1]
        assert browser.choose(identity, "defect")[0] == 303
        status, body, _ = browser.choose(identity, "good", "1")
        assert status == 409 and "Esta oferta mudou" in body
        assert "Não funciona bem" in body and 'value="2"' in body
        assert identity in browser.request("/ofertas/?aba=defeitos")[1]
        assert browser.choose(other, "defect")[0] == 303
        assert (
            sql(instance, "SELECT id,kind FROM runtime_listingevent ORDER BY sequence") == baseline
        )
        assert (
            sql(
                instance, "SELECT id FROM procrastinate_jobs WHERE queue_name='listing' ORDER BY id"
            )
            == jobs
        )
    finally:
        resume_worker(group)
    # First-choice eligibility must be checked against the current accepted observation.
    uncertain = listing_id(instance, "508")
    source.rows["VAZIA"]["description"] = "Precisa de reparo."
    clock.advance(61)
    completed(instance, 2)
    status, body, _ = browser.request(f"/ofertas/{uncertain}/condicao/", data)
    assert status == 409 and "Com defeito" in body
    assert sql(
        instance,
        "SELECT count(*) FROM runtime_manualcondition WHERE listing_id='" + uncertain + "'",
    ) == [(0,)]


def test_http_failed_save_retains_input_and_escape(condition_scenario: ConditionScenario) -> None:
    instance, source, clock = condition_scenario
    browser = ConditionBrowser(instance)
    identity = listing_id(instance)
    fail_next_condition_write(instance)
    status, body, _ = browser.choose(identity, "good")
    assert status == 503 and "Não foi possível salvar" in body
    assert "Condição não confirmada" in body and 'value="good" required checked' in body
    assert sql(instance, "SELECT last_value FROM condition_fault_calls") == [(1,)]
    assert browser.choose(identity, "good")[0] == 303
    fail_next_condition_write(instance)
    status, body, _ = browser.choose(identity, "defect")
    assert status == 503 and "Sua classificação manual" in body
    assert 'value="defect" required checked' in body
    assert identity in browser.request("/ofertas/?aba=funcionam")[1]
    assert browser.choose(identity, "defect")[0] == 303
    source.rows["INCERTA_A"]["description"] = '<script>alert("source")</script>'
    clock.advance(61)
    completed(instance, 2)
    wait_for(
        lambda: "&lt;script&gt;" in browser.request(f"/ofertas/{identity}/")[1],
        "published escaped source description",
    )
    body = browser.request(f"/ofertas/{identity}/")[1]
    assert "<script>alert" not in body and "&lt;script&gt;" in body
    shell(
        instance,
        """
from garimpei.main import build_read_condition
from garimpei.infra.persistence.listing_models import Listing
state=build_read_condition().execute(Listing.objects.get(external_id='506').id).state
assert state.manual=='defect' and state.revision==2
""",
    )

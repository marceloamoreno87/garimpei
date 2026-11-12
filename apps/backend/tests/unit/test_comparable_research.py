from dataclasses import asdict
from pathlib import Path

import pytest

from garimpei.domain.valuation.research_limits import InvalidResearchLimits, ResearchLimits
from garimpei.infra.gateway.valuation.research_manifest import load_research_limits
from tests.factories.comparable_research import controlled_limits


def manifest() -> dict[str, object]:
    raw: dict[str, object] = asdict(controlled_limits())
    raw["evidence_paths"] = list(controlled_limits().evidence_paths)
    raw["retry_delays_seconds"] = list(controlled_limits().retry_delays_seconds)
    return raw


@pytest.mark.parametrize(
    "field,value",
    [
        ("lease_seconds", 30),
        ("max_queries_per_slice", 0),
        ("request_timeout_seconds", True),
        ("max_attempts_per_input", -1),
        ("retry_delays_seconds", []),
        ("evidence_paths", ["one.json"]),
        ("corpus_hash", "not-a-hash"),
        ("measured_at", "2026-11-12T12:00:00"),
    ],
)
def test_research_limits_reject_unsafe_or_unmeasured_inputs(field: str, value: object) -> None:
    raw = manifest() | {field: value}
    with pytest.raises(InvalidResearchLimits):
        ResearchLimits.parse(raw)


def test_manifest_requires_real_and_controlled_measurement_files(tmp_path: Path) -> None:
    import json

    path = tmp_path / "limits.json"
    assert load_research_limits(path, tmp_path) is None
    path.write_text(json.dumps(manifest()))
    assert load_research_limits(path, tmp_path) is None
    for name in controlled_limits().evidence_paths:
        (tmp_path / name).write_text(
            json.dumps({"source_kind": "controlled", "measurements": [0.1]})
        )
    assert load_research_limits(path, tmp_path) is None
    (tmp_path / controlled_limits().evidence_paths[1]).write_text(
        json.dumps({"source_kind": "real", "measurements": [2.4]})
    )
    assert load_research_limits(path, tmp_path) == controlled_limits()


def test_controlled_corpus_identity_exclusions_age_and_dispersion() -> None:
    import json
    from dataclasses import replace
    from datetime import timedelta
    from decimal import Decimal
    from uuid import uuid4

    from garimpei.domain.valuation.identification import identify_product
    from garimpei.domain.valuation.policy import eligible, estimate
    from garimpei.domain.valuation.values import Comparable
    from tests.factories.comparable_research import KEY, NOW, candidate

    raw = json.loads(
        (Path(__file__).parents[1] / "fixtures/valuation/research_cases.json").read_text()
    )
    for name in ("UNKNOWN", "MISSING", "CONFLICT"):
        row = raw[name]
        evidence = candidate("19000", title=row["title"]).evidence
        evidence = replace(evidence, description=row.get("description"))
        value = identify_product(evidence, uuid4(), 1)
        assert value.state == row["state"], name

    def comparable(identity: str, price: str = "2300") -> Comparable:
        evidence = candidate(identity, price).evidence
        return Comparable(
            uuid4(),
            "facebook_marketplace",
            identity,
            evidence.title or "",
            "https://example.invalid/",
            evidence.price,
            NOW,
            1,
            evidence,
        )

    target = comparable("19001", "1000")
    sample = tuple(
        comparable(str(19010 + i), price) for i, price in enumerate(raw["SUFFICIENT"]["prices"])
    )
    result = estimate(target, sample + sample + (target,), NOW)
    assert result.price == Decimal(raw["SUFFICIENT"]["resale"]) and result.after == 5
    for exclusion in raw["EXCLUSIONS"]:
        row = comparable("19030")
        assert not eligible(replace(row, evidence=replace(row.evidence, **exclusion)), KEY, NOW)
    assert eligible(
        replace(
            sample[0], evidence=replace(sample[0].evidence, published_at=NOW - timedelta(days=60))
        ),
        KEY,
        NOW,
    )
    assert not eligible(replace(sample[0], observed_at=NOW + timedelta(seconds=1)), KEY, NOW)
    boundary = raw["AGE_BOUNDARY"]
    assert eligible(
        replace(sample[0], observed_at=NOW - timedelta(seconds=boundary["accepted_seconds"])),
        KEY,
        NOW,
    )
    assert not eligible(
        replace(sample[0], observed_at=NOW - timedelta(seconds=boundary["rejected_seconds"])),
        KEY,
        NOW,
    )
    dispersed = tuple(
        comparable(str(19040 + i), price) for i, price in enumerate(raw["DISPERSION"]["prices"])
    )
    assert estimate(target, dispersed, NOW).reason == raw["DISPERSION"]["reason"]


def test_controlled_worker_policy_requires_explicit_eval_loopback_admission(tmp_path: Path) -> None:
    import json

    raw = manifest() | {"environment": "eval-controlled"}
    path = tmp_path / "limits.json"
    path.write_text(json.dumps(raw))
    for name in controlled_limits().evidence_paths:
        (tmp_path / name).write_text(
            json.dumps({"source_kind": "controlled", "measurements": [0.1]})
        )
    assert load_research_limits(path, tmp_path) is None
    assert load_research_limits(path, tmp_path, allow_controlled=True) is not None
    path.write_text(json.dumps(manifest()))
    assert load_research_limits(path, tmp_path, allow_controlled=True) is None


def test_cold_browser_rebuild_reserves_all_calls_before_source_io() -> None:
    from dataclasses import replace
    from uuid import uuid4

    from garimpei.domain.listing.listing import Match
    from garimpei.domain.listing.scope import Search
    from garimpei.domain.valuation.research import ResearchUnit
    from garimpei.usecase.valuation.run_research_usecase import RunComparableResearchUseCase
    from tests.factories.comparable_research import (
        KEY,
        ControlledResearchSource,
        ForbiddenResearchStore,
        scope,
    )

    limits = replace(
        controlled_limits(), request_timeout_seconds=20, max_slice_seconds=180, lease_seconds=240
    )
    unit = ResearchUnit(
        uuid4(),
        1,
        scope(),
        Search(Match("product", KEY), "PlayStation 5", "marketplace"),
        KEY,
        limits,
        "source:opaque",
        1,
        (),
    )
    clock = [60.0]
    # No store/source operation may run in this boundary test.
    runner = RunComparableResearchUseCase(
        ForbiddenResearchStore(), ControlledResearchSource(), lambda: clock[0]
    )
    assert runner._can_start(unit, 0, 0, 0)
    clock[0] = 61
    assert not runner._can_start(unit, 0, 0, 0)
    clock[0] = 120
    pending = replace(unit, pending=("200",))
    assert runner._can_start(pending, 0, 0, 0)
    assert not runner._can_start(pending, 0, 0, limits.max_details_per_slice)


def test_measured_policy_does_not_bypass_explicit_geography_block(tmp_path: Path) -> None:
    import json

    from garimpei.infra.gateway.valuation.research_manifest import research_activation_reason

    path = tmp_path / "limits.json"
    path.write_text(
        json.dumps(
            manifest()
            | {"automatic_activation": False, "activation_block_reason": "real_geography_unproved"}
        )
    )
    assert load_research_limits(path, tmp_path) is None
    assert research_activation_reason(path) == "real_geography_unproved"

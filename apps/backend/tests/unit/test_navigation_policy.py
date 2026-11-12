from datetime import UTC, datetime, timedelta
from uuid import uuid4

from garimpei.domain.navigation.catalog import Catalog, Family, Relation
from garimpei.domain.navigation.policy import NavigationPolicy, eligible_suggestion, select_turn
from garimpei.domain.navigation.work import Turn

NOW = datetime(2026, 11, 12, tzinfo=UTC)


def test_both_fronts_progress_within_two_n_turns() -> None:
    turns = [
        Turn(uuid4(), interest, front, 0, None)
        for interest in ("ps5", "phone")
        for front in ("discovery", "investigation")
    ]
    seen = []
    for order in range(1, 5):
        chosen = select_turn(tuple(turns), NOW)
        assert chosen is not None
        seen.append((chosen.interest, chosen.front))
        turns = [turn.attempted(order) if turn.id == chosen.id else turn for turn in turns]
    assert len(set(seen)) == 4


def test_source_wait_does_not_block_independent_work() -> None:
    waiting = Turn(uuid4(), "ps5", "discovery", 0, NOW + timedelta(seconds=15))
    healthy = Turn(uuid4(), "phone", "investigation", 1, None)
    assert select_turn((waiting, healthy), NOW) == healthy


def test_alias_keeps_variant_and_requires_listing_evidence() -> None:
    catalog = Catalog(
        "1",
        (
            Family("console", "PlayStation 5 Slim", ("PS5 Slim",), ("pro",)),
            Family("phone", "iPhone 13 128 GB", (), ("pro",)),
        ),
        (),
    )
    assert catalog.terms("PlayStation 5 Slim") == ("PlayStation 5 Slim", "PS5 Slim")
    assert catalog.terms("PS5 Slim") == ("PS5 Slim", "PlayStation 5 Slim")
    assert catalog.terms("PS5 Pro") == ("PS5 Pro",)
    assert catalog.matches("PlayStation 5 Slim", "Console PS5 Slim funcionando")
    assert not catalog.matches("PlayStation 5 Slim", "PS5 Pro")
    assert not catalog.matches("iPhone 13 128 GB", "iPhone 13 Pro 128 GB")
    assert not catalog.matches("iPhone 13 128 GB", "iPhone 13 256 GB")


def test_only_explicit_directed_relations_are_researchable() -> None:
    relation = Relation(
        "slim-pro", "PlayStation 5 Slim", "PS5 Pro", "Outro modelo da mesma família"
    )
    catalog = Catalog(
        "1", (Family("console", "PlayStation 5 Slim", ("PS5 Slim",), ("pro",)),), (relation,)
    )
    assert catalog.related("PS5 Slim") == (relation,)
    assert catalog.related("televisão") == ()


def test_idle_budget_admission_and_no_restart_reset() -> None:
    policy = NavigationPolicy()
    assert not eligible_suggestion(
        policy, NOW, active_ready=True, active_due=None, last_slice=None, timeout=20, cadence=1.2
    )
    assert not eligible_suggestion(
        policy,
        NOW,
        active_ready=False,
        active_due=NOW + timedelta(seconds=26),
        last_slice=None,
        timeout=20,
        cadence=1.2,
    )
    assert eligible_suggestion(
        policy,
        NOW,
        active_ready=False,
        active_due=NOW + timedelta(seconds=27),
        last_slice=None,
        timeout=20,
        cadence=1.2,
    )
    assert not eligible_suggestion(
        policy,
        NOW,
        active_ready=False,
        active_due=None,
        last_slice=NOW - timedelta(seconds=299),
        timeout=20,
        cadence=1.2,
    )


def test_shared_interest_front_not_starved_by_research_turns() -> None:
    turns: tuple[Turn, ...] = (
        Turn(uuid4(), "ps5", "discovery", 0, None),
        Turn(uuid4(), "ps5", "discovery", 0, None),
        Turn(uuid4(), "ps5", "investigation", 0, None),
    )
    chosen = select_turn(turns, NOW)
    assert chosen is not None
    turns = tuple(
        turn.attempted(1)
        if (turn.interest, turn.front) == (chosen.interest, chosen.front)
        else turn
        for turn in turns
    )
    other = select_turn(turns, NOW)
    assert other is not None and other.front != chosen.front

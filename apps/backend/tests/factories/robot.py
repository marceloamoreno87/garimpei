"""F22 probes restricted to the caller's disposable PostgreSQL instance."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

from django.db import DatabaseError, connections

from garimpei.domain.robot.control import OperationOutcome, RobotCommand, RobotPermit
from garimpei.domain.robot.errors import RobotConflict, RobotUnavailable
from garimpei.infra.persistence.robot_models import (
    RobotControl,
    RobotControlCommand,
    RobotOperation,
)
from garimpei.infra.queries.robot.postgres_queries import PostgresRobotQueries
from garimpei.infra.repository.robot.postgres_repository import PostgresRobotRepository
from tests.factories.monitoring import require_disposable


@dataclass
class RobotAdmissionFake:
    enabled: bool = True
    requests: list[str] = field(default_factory=list)
    outcomes: list[tuple[str, OperationOutcome]] = field(default_factory=list)

    def authorize(
        self, stage: str, unit_key: str, input_revision: str, resource_generation: int
    ) -> RobotPermit | None:
        self.requests.append(stage)
        if not self.enabled:
            return None
        return RobotPermit(uuid4(), stage, unit_key, input_revision, resource_generation, 1)

    def complete(
        self, permit: RobotPermit, outcome: OperationOutcome = "completed", reason: str = ""
    ) -> None:
        self.outcomes.append((permit.stage, outcome))


def _fresh() -> tuple[PostgresRobotRepository, PostgresRobotQueries]:
    require_disposable()
    RobotOperation.objects.all().delete()
    RobotControlCommand.objects.all().delete()
    RobotControl.objects.filter(pk="local").update(requested_enabled=True, revision=0, epoch=0)
    return PostgresRobotRepository(), PostgresRobotQueries()


def admission_cases() -> None:
    repository, queries = _fresh()
    prior = repository.authorize("media", "prior", "observation:1", 1)
    assert prior is not None
    pause = RobotCommand(uuid4(), False, 0)
    repository.command(pause)
    repository.command(pause)
    assert queries.status().revision == 1 and queries.status().state == "draining"
    stages = (
        "navigation",
        "research",
        "suggestion",
        "media",
        "valuation",
        "assessment",
        "inference",
        "alert",
    )
    for stage in stages:
        assert repository.authorize(stage, "denied", "observation:1", 1) is None
    assert RobotOperation.objects.count() == 1
    repository.complete(prior)
    repository.complete(prior)
    assert queries.status().state == "disabled"
    assert RobotOperation.objects.get(id=prior.id).state == "completed"
    repository.command(RobotCommand(uuid4(), True, 1))
    current = queries.status()
    repository.command(pause)  # replay old pause must not overwrite the newer enable.
    assert queries.status() == current
    assert RobotControlCommand.objects.count() == 2
    for conflict in (RobotCommand(pause.id, True, 0), RobotCommand(uuid4(), False, 0)):
        try:
            repository.command(conflict)
        except RobotConflict:
            pass
        else:
            raise AssertionError("stale/mismatched commands must conflict")


def concurrent_cases() -> None:
    repository, queries = _fresh()
    barrier = Barrier(2)

    def run(enabled: bool) -> bool:
        try:
            barrier.wait(timeout=5)
            repository.command(RobotCommand(uuid4(), enabled, 0))
            return True
        except RobotConflict:
            return False
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, [False, False]))
    assert sorted(results) == [False, True]
    assert not queries.status().enabled and queries.status().revision == 1
    assert RobotControlCommand.objects.count() == 1
    # Both linearizations of pause/authorization: a prior permit drains, later admission is denied.
    repository.command(RobotCommand(uuid4(), True, 1))
    permit = repository.authorize("alert", "before-pause", "attempt:1", 1)
    assert permit is not None
    repository.command(RobotCommand(uuid4(), False, 2))
    assert repository.authorize("alert", "after-pause", "attempt:2", 2) is None
    repository.complete(permit, "unknown", "transmission_possible")
    assert queries.status().state == "unknown"
    repository.complete(permit, "completed", "receipt_confirmed")
    assert queries.status().state == "disabled"


def failure_cases() -> None:
    repository, queries = _fresh()
    before = queries.status()
    with patch(
        "garimpei.infra.repository.robot.postgres_repository.locked_control",
        side_effect=DatabaseError,
    ):
        actions: tuple[Callable[[], object], ...] = (
            lambda: repository.authorize("alert", "blocked", "1", 1),
            lambda: repository.command(RobotCommand(uuid4(), False, 0)),
        )
        for action in actions:
            try:
                action()
            except RobotUnavailable:
                pass
            else:
                raise AssertionError("unreadable control must fail closed")
    assert queries.status() == before
    assert not RobotControlCommand.objects.exists() and not RobotOperation.objects.exists()


def inference_cases() -> None:
    from django.utils.timezone import now

    from garimpei.domain.inference.ports import PreparedPart
    from garimpei.domain.inference.request import AnalysisInput
    from garimpei.infra.persistence.inference_models import (
        InferenceControl,
        InferencePart,
        InferenceRequest,
    )
    from garimpei.infra.persistence.management.commands.local_ai import _smoke_observation
    from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository

    robot, queries = _fresh()
    InferencePart.objects.all().delete()
    InferenceRequest.objects.all().delete()
    InferenceControl.objects.all().delete()
    observation, text = _smoke_observation("robot-control", "text")
    repository = PostgresInferenceRepository(lambda: 0, 3, robot=robot)
    ticket = repository.admit(
        AnalysisInput(observation, 1, text, ()),
        "fake-artifact",
        (PreparedPart("one", text), PreparedPart("two", text)),
    )
    work = repository.claim(now())
    assert work
    robot.command(RobotCommand(uuid4(), False, 0))
    assert not repository.authorize(work)
    assert InferencePart.objects.get(pk=work.part_id).attempts == 0
    assert InferencePart.objects.get(pk=work.part_id).state == "pending"
    assert repository.claim(now()) is None
    assert not InferenceControl.objects.get(pk=1).paused
    robot.command(RobotCommand(uuid4(), True, 1))
    work = repository.claim(now())
    assert work and repository.authorize(work)
    robot.command(RobotCommand(uuid4(), False, 2))
    assert repository.claim(now()) is None
    robot.command(RobotCommand(uuid4(), True, 3))
    assert (
        repository.claim(now()) is None
    )  # An enabled global switch does not free an occupied GPU generation.
    robot.command(RobotCommand(uuid4(), False, 4))
    assert repository.publish(work, {"test": "accepted response"}, {}, now())
    assert repository.claim(now()) is None
    assert InferenceRequest.objects.get(pk=ticket.request_id).state == "pending"
    assert (
        InferencePart.objects.filter(request_id=ticket.request_id, state="succeeded").count() == 1
    )
    assert not RobotOperation.objects.filter(stage="inference", state="active").exists()
    repository.control(True, 1)
    robot.command(RobotCommand(uuid4(), True, 5))
    assert repository.claim(now()) is None and InferenceControl.objects.get(pk=1).paused
    assert queries.status().enabled

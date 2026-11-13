"""Synthetic engineering inputs; never represent independent human labels."""

import json
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from garimpei.domain.assistance.review import ReviewCommand, ReviewTicket


def identity_snapshot() -> dict[str, object]:
    return dict(
        facts=[
            dict(
                id="title-model",
                field="model",
                value="ps5",
                source="text",
                text_field="title",
                start=0,
                end=13,
                quote="PlayStation 5",
            )
        ],
        texts=dict(title="PlayStation 5 Slim Digital 825GB"),
        allowed_values=dict(model=["ps5"]),
        required_fields=["model"],
        conflict=False,
    )


def supported_response() -> dict[str, object]:
    return dict(
        outcome="supported",
        findings=[
            dict(
                field="model",
                value="ps5",
                evidence_refs=["title-model"],
                reason_code="explicit_evidence",
            )
        ],
        limitations=[],
    )


@dataclass
class NamedAssistanceRepository:
    commands: list[ReviewCommand] = field(default_factory=list)
    identity: UUID = field(default_factory=uuid4)

    def admit(self, command: ReviewCommand) -> ReviewTicket:
        self.commands.append(command)
        return ReviewTicket(self.identity, command.purpose, "pending", False)

    def reconcile(self) -> None:
        return None


def serialized_snapshot() -> str:
    return json.dumps(identity_snapshot())

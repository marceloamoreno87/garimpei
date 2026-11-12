"""Measured activation policy. An absent or incomplete manifest never enables research."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime


class InvalidResearchLimits(ValueError):
    pass


@dataclass(frozen=True)
class ResearchLimits:
    policy_version: str
    measured_at: str
    environment: str
    corpus_hash: str
    evidence_paths: tuple[str, ...]
    max_queries_per_slice: int
    max_pages_per_query: int
    max_details_per_slice: int
    max_slice_seconds: int
    request_timeout_seconds: int
    max_attempts_per_input: int
    retry_delays_seconds: tuple[int, ...]
    lease_seconds: int
    max_wait_slices_per_interest: int
    max_pending_per_interest: int

    @classmethod
    def parse(cls, raw: Mapping[str, object]) -> "ResearchLimits":
        try:
            return cls._parse(raw)
        except (KeyError, TypeError, ValueError):
            raise InvalidResearchLimits("research_limits_unmeasured") from None

    @classmethod
    def _parse(cls, raw: Mapping[str, object]) -> "ResearchLimits":
        def positive(name: str) -> int:
            value = raw[name]
            if type(value) is not int or value <= 0:
                raise ValueError(name)
            return value

        def text(name: str) -> str:
            value = raw[name]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(name)
            return value

        stamp = datetime.fromisoformat(text("measured_at"))
        if stamp.tzinfo is None:
            raise ValueError("measured_at")
        corpus = text("corpus_hash")
        if len(corpus) != 64 or any(c not in "0123456789abcdef" for c in corpus):
            raise ValueError("corpus_hash")
        evidence, retries = raw["evidence_paths"], raw["retry_delays_seconds"]
        if (
            not isinstance(evidence, list)
            or len(evidence) < 2
            or not all(isinstance(p, str) and p for p in evidence)
        ):
            raise ValueError("evidence_paths")
        if (
            not isinstance(retries, list)
            or not retries
            or not all(type(n) is int and n > 0 for n in retries)
        ):
            raise ValueError("retry_delays_seconds")
        values = {
            name: positive(name)
            for name in (
                "max_queries_per_slice",
                "max_pages_per_query",
                "max_details_per_slice",
                "max_slice_seconds",
                "request_timeout_seconds",
                "max_attempts_per_input",
                "lease_seconds",
                "max_wait_slices_per_interest",
                "max_pending_per_interest",
            )
        }
        if (
            values["request_timeout_seconds"] >= values["max_slice_seconds"]
            or values["lease_seconds"] <= values["max_slice_seconds"]
        ):
            raise ValueError("slice_and_lease")
        return cls(
            text("policy_version"),
            text("measured_at"),
            text("environment"),
            corpus,
            tuple(str(p) for p in evidence),
            retry_delays_seconds=tuple(int(n) for n in retries),
            **values,
        )

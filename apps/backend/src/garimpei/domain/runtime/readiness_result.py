from dataclasses import dataclass


@dataclass(frozen=True)
class ReadinessResult:
    ready: bool
    checks: dict[str, str]

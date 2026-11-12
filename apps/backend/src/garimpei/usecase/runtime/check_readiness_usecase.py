from collections.abc import Mapping

from garimpei.domain.runtime.readiness_gateway import ReadinessGateway
from garimpei.domain.runtime.readiness_result import ReadinessResult


class CheckReadinessUseCase:
    def __init__(self, probes: Mapping[str, ReadinessGateway]) -> None:
        self._probes = probes

    def execute(self) -> ReadinessResult:
        checks = {
            name: "ready" if probe.check() else "unavailable"
            for name, probe in self._probes.items()
        }
        return ReadinessResult(
            bool(checks) and all(value == "ready" for value in checks.values()), checks
        )

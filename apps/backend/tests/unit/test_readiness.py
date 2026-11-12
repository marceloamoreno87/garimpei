from garimpei.usecase.runtime.check_readiness_usecase import CheckReadinessUseCase


class AvailableProbe:
    def check(self) -> bool:
        return True


class UnavailableDatabaseProbe:
    def check(self) -> bool:
        return False


def test_unavailable_dependency_cannot_be_ready() -> None:
    result = CheckReadinessUseCase(
        {"database": UnavailableDatabaseProbe(), "worker": AvailableProbe()}
    ).execute()
    assert not result.ready
    assert result.checks == {"database": "unavailable", "worker": "ready"}


def test_all_probes_must_pass() -> None:
    result = CheckReadinessUseCase({"worker": AvailableProbe()}).execute()
    assert result.ready

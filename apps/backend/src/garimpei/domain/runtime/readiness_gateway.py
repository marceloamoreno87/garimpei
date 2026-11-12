from typing import Protocol


class ReadinessGateway(Protocol):
    def check(self) -> bool: ...

class RobotError(Exception):
    def __init__(self, code: str, message: str, status: int = 503) -> None:
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


class RobotUnavailable(RobotError):
    def __init__(self) -> None:
        super().__init__(
            "robot_control_unavailable",
            "Não foi possível consultar ou gravar o controle do robô. A última decisão confirmada foi preservada.",
        )


class RobotConflict(RobotError):
    def __init__(self) -> None:
        super().__init__(
            "robot_control_conflict",
            "O estado mudou em outra janela ou o comando já foi usado. Reabra o acompanhamento.",
            409,
        )


class RobotPaused(Exception):
    """Control-flow denial: leave pending work and retry budgets untouched."""

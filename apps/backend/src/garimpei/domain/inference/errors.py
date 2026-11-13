class InferenceError(Exception):
    def __init__(
        self,
        code: str,
        status: int = 400,
        *,
        sent: bool = False,
        diagnostic: str = "",
        metrics: dict[str, object] | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.status = status
        self.sent = sent
        self.diagnostic = diagnostic
        self.metrics = dict(metrics or {})


RECOVERABLE = frozenset({"service_unavailable", "out_of_memory", "gpu_unavailable"})

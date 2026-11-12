class InferenceError(Exception):
    def __init__(self, code: str, status: int = 400, *, sent: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.status = status
        self.sent = sent


RECOVERABLE = frozenset({"service_unavailable", "out_of_memory", "gpu_unavailable"})

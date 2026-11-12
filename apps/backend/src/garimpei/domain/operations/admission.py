from dataclasses import dataclass


@dataclass(frozen=True)
class Admission:
    pending: int
    business_bytes: int
    free_bytes: int
    queue_limit: int = 1000
    data_limit: int = 10 * 1024**3
    reserve: int = 1024**3

    @property
    def reason(self) -> str | None:
        if self.pending >= self.queue_limit:
            return "queue_full"
        if self.business_bytes >= self.data_limit:
            return "business_storage_limit"
        if self.free_bytes <= self.reserve:
            return "filesystem_reserve"
        return None

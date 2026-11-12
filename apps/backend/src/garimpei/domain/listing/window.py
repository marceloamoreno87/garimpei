from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class PublicationWindow:
    start: datetime
    end: datetime

    @classmethod
    def ending_at(cls, end: datetime) -> "PublicationWindow":
        return cls(end - timedelta(hours=48), end)

    def contains(self, published_at: datetime | None) -> bool | None:
        if published_at is None:
            return None
        return self.start <= published_at <= self.end

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaPolicy:
    budget_bytes: int | None = None
    max_photos: int = 12
    max_file_bytes: int = 20 * 1024 * 1024
    max_pixels: int = 40_000_000
    thumb_edge: int = 640
    timeout_seconds: int = 20
    min_free_bytes: int = 256 * 1024 * 1024
    lease_seconds: int = 60

    def retry_delay(self, attempts: int, source_delay: int = 0) -> int | None:
        if attempts > 3:
            return None
        return max((15, 60, 300)[max(0, attempts - 1)], source_delay)

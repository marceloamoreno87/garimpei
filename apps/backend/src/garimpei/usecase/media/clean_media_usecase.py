from collections.abc import Callable
from datetime import datetime

from garimpei.domain.media.ports import MediaRepository, MediaStore


class CleanMediaUseCase:
    def __init__(
        self, repository: MediaRepository, store: MediaStore, clock: Callable[[], datetime]
    ) -> None:
        self._repository, self._store, self._clock = repository, store, clock

    def execute(self) -> None:
        for file in self._repository.cleanable(self._clock()):
            try:
                self._store.remove(file)
                self._repository.removed(file.version_id, self._clock())
            except OSError:
                continue  # Persisted removing state is retried; never claim successful unlink.

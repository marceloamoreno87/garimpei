from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from garimpei.domain.media.errors import MediaError
from garimpei.domain.media.ports import ImageTransport, MediaRepository, MediaStore
from garimpei.domain.robot.admission import admitted_unit
from garimpei.domain.robot.errors import RobotPaused, RobotUnavailable
from garimpei.domain.robot.ports import RobotAdmission


class ObtainMediaUseCase:
    def __init__(
        self,
        repository: MediaRepository,
        transport: ImageTransport,
        store: MediaStore,
        clock: Callable[[], datetime],
        robot: RobotAdmission | None = None,
        on_pause: Callable[["MediaClaim"], None] | None = None,
    ) -> None:
        self._robot, self._on_pause = robot, on_pause
        self._repository, self._transport, self._store, self._clock = (
            repository,
            transport,
            store,
            clock,
        )

    def execute(self, identity: UUID) -> None:
        claim = self._repository.claim(identity, self._clock())
        if claim is None:
            return
        try:
            self._execute_claim(claim)
        except (RobotPaused, RobotUnavailable):
            if self._on_pause:
                self._on_pause(claim)

    def _execute_claim(self, claim: "MediaClaim") -> None:
        if claim.kind == "thumbnail":
            self._derive(claim)
            return
        reason = ""
        for variant in claim.variants:
            failure = self._obtain(claim, variant.url, reason)
            if failure is None:
                return
            reason = failure.code
            if self._failed(claim, failure):
                return
        self._repository.fail(claim, reason or "media_no_candidate", self._clock())

    def _obtain(self, claim: "MediaClaim", url: str, reason: str) -> MediaError | None:
        with admitted_unit(
            self._robot, "media", str(claim.id), str(claim.observation_id), claim.generation
        ):
            return self._obtain_authorized(claim, url, reason)

    def _obtain_authorized(self, claim: "MediaClaim", url: str, reason: str) -> MediaError | None:
        try:
            content = self._transport.fetch(url)
            key = self._store.put(claim, content)
            self._repository.publish(claim, content, key, self._clock(), reason)
        except MediaError as failure:
            return failure
        except OSError:
            return MediaError("media_write_failed")
        return None

    def _failed(self, claim: "MediaClaim", failure: MediaError) -> bool:
        if failure.code in {"media_file_limit", "media_pixel_limit"}:
            return False
        self._repository.fail(claim, failure.code, self._clock(), failure.retry_after)
        return True

    def _derive(self, claim: "MediaClaim") -> None:
        with admitted_unit(
            self._robot, "media", str(claim.id), str(claim.observation_id), claim.generation
        ):
            self._derive_authorized(claim)

    def _derive_authorized(self, claim: "MediaClaim") -> None:
        try:
            original = self._repository.original(claim)
            file = self._store.derive(claim, original)
            self._repository.thumbnail(claim, file, self._clock())
        except (MediaError, OSError):
            self._repository.fail(claim, "media_thumbnail_failed", self._clock())


from garimpei.domain.media.media import MediaClaim  # noqa: E402

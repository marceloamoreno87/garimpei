import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from uuid import UUID

from django.utils.timezone import now

from garimpei.config.env import InferenceSettings
from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.request import ImageReference
from garimpei.domain.listing.assessment_ports import AssessmentWork
from garimpei.domain.media.errors import MediaError
from garimpei.domain.media.ports import MediaQueries, MediaRepository, MediaStore
from garimpei.domain.robot.admission import admitted_unit
from garimpei.domain.robot.ports import RobotAdmission
from garimpei.infra.gateway.inference.registry import register_file
from garimpei.infra.gateway.listing.assessment_image import assessment_derivative


def prepare_photos(
    work: AssessmentWork,
    media: MediaRepository,
    store: MediaStore,
    queries: MediaQueries,
    settings: InferenceSettings,
    robot: RobotAdmission | None = None,
) -> tuple[tuple[ImageReference, ...], tuple[UUID, ...], dict[str, str]]:
    photos = cast(list[dict[str, object]], work.value.snapshot["photos"])
    available = [p for p in photos if p["state"] == "available" and p["sha256"]]
    pins = []
    references = {}
    omissions = {}
    for photo in available:
        version = UUID(str(photo["version_id"]))
        pin = media.acquire(
            work.value.listing_id,
            work.value.observation_id,
            version,
            "condition-assessment",
            str(work.id),
            now(),
        )
        pins.append(pin.reference_id)
        digest = str(photo["sha256"])
        if digest in references or digest in omissions:
            continue
        with admitted_unit(robot, "assessment_photo", str(version), str(work.id), work.generation):
            reference, reason = _register(work, photo, store, queries, settings)
        if reference:
            references[digest] = reference
        else:
            omissions[digest] = reason
    return tuple(references.values()), tuple(pins), omissions


def _register(
    work: AssessmentWork,
    photo: dict[str, object],
    store: MediaStore,
    queries: MediaQueries,
    settings: InferenceSettings,
) -> tuple[ImageReference | None, str]:
    try:
        original = queries.file(work.value.listing_id, UUID(str(photo["version_id"])), "original")
        raw = store.read(original)
        derived = assessment_derivative(raw)
        # Only the existing F19 registry persists data and accounts for its quota.
        with TemporaryDirectory(prefix="garimpei-assessment-") as temporary:
            path = Path(temporary) / "input.png"
            path.write_bytes(derived)
            path.chmod(0o600)
            result = register_file(
                settings,
                path,
                dict(
                    id=photo["photo_id"],
                    revision=1,
                    sha256=hashlib.sha256(derived).hexdigest(),
                    source_sha256=photo["sha256"],
                    authorization="F14 pinned analysis input",
                ),
            )
            return result, ""
    except (InferenceError, MediaError) as error:
        return None, error.code

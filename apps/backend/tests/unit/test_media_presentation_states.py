from uuid import uuid4

import pytest

from garimpei.domain.media.media import MediaGallery, MediaPhoto
from garimpei.infra.http.media.presentation import gallery_label


@pytest.mark.parametrize(
    ("states", "expected"),
    [
        (("removed", "removed"), "Fotos removidas após encerramento da retenção"),
        (("removing", "removed"), "Remoção de fotos em andamento"),
        (("available", "removed"), "Cópias disponíveis; parte das fotos foi removida"),
        (("available",), "Fotos conservadas neste computador"),
    ],
)
def test_retention_label_matches_actual_photo_availability(
    states: tuple[str, ...], expected: str
) -> None:
    photos = tuple(
        MediaPhoto(str(index), index, index == 0, uuid4(), state=state)
        for index, state in enumerate(states)
    )
    historical = MediaGallery(
        uuid4(), uuid4(), presence="present", state="ready", complete=True, photos=photos
    )
    assert gallery_label(historical, True) == expected

from uuid import UUID

from garimpei.domain.media.media import MediaGallery
from garimpei.domain.media.ports import MediaQueries


class ReadMediaGalleryUseCase:
    def __init__(self, queries: MediaQueries) -> None:
        self._queries = queries

    def execute(
        self, listing_id: UUID, observation_id: UUID, expected_revision: int | None = None
    ) -> MediaGallery:
        return self._queries.gallery(listing_id, observation_id, expected_revision)

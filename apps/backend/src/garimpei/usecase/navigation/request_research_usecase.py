from uuid import UUID

from garimpei.domain.navigation.ports import NavigationStore


class RequestResearchUseCase:
    def __init__(self, repository: NavigationStore) -> None:
        self._repository = repository

    def execute(
        self,
        request_id: UUID,
        scope_revision: int,
        origin_interest: str,
        canonical_term: str,
        constraints: str,
        purpose: str,
    ) -> UUID:
        # No caller-supplied geographic scope; repository checks the current approved scope hash.
        return self._repository.request_research(
            request_id, scope_revision, origin_interest, canonical_term, purpose, constraints
        )

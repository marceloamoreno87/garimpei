import hashlib

from garimpei.domain.listing.ports import Revisit
from garimpei.domain.listing.scope import Search
from garimpei.domain.navigation.work import NavigationUnit, Turn
from garimpei.infra.persistence.navigation_models import NavigationCheckpoint, NavigationWork


def to_unit(
    row: NavigationWork, checkpoint: NavigationCheckpoint, query: Search, target: Revisit | None
) -> NavigationUnit:
    context = f"{checkpoint.context_hash}:{checkpoint.term_index}:{checkpoint.pages}:{checkpoint.cursor or 'start'}"
    unit_key = (
        "detail:" + target.external_id
        if target
        else "page:" + hashlib.sha256(context.encode()).hexdigest()
    )
    return NavigationUnit(
        Turn(row.id, row.origin_interest, row.front, row.last_turn, row.next_attempt_at),
        row.generation,
        row.revision,
        query,
        tuple(checkpoint.terms),
        checkpoint.term_index,
        checkpoint.cursor,
        tuple(checkpoint.signatures),
        checkpoint.pages,
        checkpoint.details,
        row.failures,
        target,
        unit_key,
        row.purpose,
    )

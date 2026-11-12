"""Explicit equivalences and directed relations; source content never defines scope."""

from dataclasses import dataclass, replace

from garimpei.domain.listing.interest_match import matches_product, tokens
from garimpei.domain.listing.scope import Scope, Search


@dataclass(frozen=True)
class Family:
    family: str
    canonical: str
    aliases: tuple[str, ...]
    excluded: tuple[str, ...] = ()

    def recognizes(self, term: str) -> bool:
        return tokens(term) in {tokens(name) for name in (self.canonical, *self.aliases)}


@dataclass(frozen=True)
class Relation:
    key: str
    origin: str
    target: str
    reason: str


@dataclass(frozen=True)
class Catalog:
    version: str
    families: tuple[Family, ...]
    relations: tuple[Relation, ...]

    def terms(self, original: str) -> tuple[str, ...]:
        family = next((row for row in self.families if row.recognizes(original)), None)
        if family is None:
            return (original,)
        return tuple(dict.fromkeys((original, family.canonical, *family.aliases)))

    def matches(self, original: str, title: str) -> bool:
        family = next((row for row in self.families if row.recognizes(original)), None)
        if family and any(tokens(word)[0] in tokens(title) for word in family.excluded):
            return False
        return any(matches_product(term, title) for term in self.terms(original))

    def related(self, original: str) -> tuple[Relation, ...]:
        terms = {tokens(term) for term in self.terms(original)}
        return tuple(row for row in self.relations if tokens(row.origin) in terms)

    def permits(self, original: str, term: str) -> bool:
        return tokens(term) in {tokens(value) for value in self.terms(original)} or any(
            tokens(row.target) == tokens(term) for row in self.related(original)
        )

    def decorate_scope(self, scope: Scope) -> Scope:
        def decorate(search: Search) -> Search:
            family = next((row for row in self.families if row.recognizes(search.term)), None)
            return replace(
                search,
                equivalent_terms=self.terms(search.term),
                excluded_terms=family.excluded if family else (),
            )

        return replace(scope, searches=tuple(decorate(search) for search in scope.searches))

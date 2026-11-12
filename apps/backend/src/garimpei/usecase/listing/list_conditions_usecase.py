from garimpei.domain.listing.condition import Tab
from garimpei.domain.listing.condition_ports import ConditionQueries, ConditionView


class ListConditionsUseCase:
    def __init__(self, queries: ConditionQueries) -> None:
        self._queries = queries

    def execute(self, tab: Tab) -> tuple[ConditionView, ...]:
        return tuple(view for view in self._queries.all_visible() if view.state.tab == tab)

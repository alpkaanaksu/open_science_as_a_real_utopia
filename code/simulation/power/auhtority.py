from typing import Any, Callable, Iterable, List

from .domain import Domain


DecisionFn = Callable[[Any], bool]


class Authority:
    """
    Controls a domain via a pipeline of decision functions.
    """

    def __init__(self, name: str, domain: Domain, decisions: Iterable[DecisionFn] = ()):
        self.name = name
        self.domain = domain
        self.decision_functions: List[DecisionFn] = list(decisions)

    def decide(self, entity: Any) -> bool:
        for fn in self.decision_functions:
            if not fn(entity):
                return False
        return True

    def exercise_power(self, entity: Any) -> bool:
        outcome = self.decide(entity)
        if outcome:
            self.domain.add(entity)
        else:
            self.domain.remove(entity)
        return outcome

    def __repr__(self):
        return f"<Authority {self.name} controls '{self.domain.name}'>"

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List


IntrospectorFn = Callable[[Any, Dict[str, "Domain"]], None]


class Domain:
    """
    A space where entities can be added/removed and introspected.

    Introspectors:
        - are fixed at construction time
        - run in order
        - mutate entities in place
        - may read from other domains via `all_domains`
    """

    def __init__(
        self,
        name: str,
        initial: Iterable[Any] = None,
        introspectors: Iterable[IntrospectorFn] = (),
    ):
        self.name = name
        self.entities: List[Any] = list(initial) if initial else []
        self.introspectors: List[IntrospectorFn] = list(introspectors)

    # --- entity ops ------------------------------------------------------

    def add(self, entity: Any):
        if entity not in self.entities:
            self.entities.append(entity)
        return entity

    def remove(self, entity: Any):
        if entity in self.entities:
            self.entities.remove(entity)
        return entity

    # --- introspection ---------------------------------------------------

    def introspect(self, all_domains: Dict[str, "Domain"]):
        """
        Run all introspectors on all entities in this domain.
        """
        for entity in self.entities:
            for fn in self.introspectors:
                fn(entity, all_domains)
        return self.entities

    def __repr__(self):
        return f"<Domain {self.name}: {self.entities}>"

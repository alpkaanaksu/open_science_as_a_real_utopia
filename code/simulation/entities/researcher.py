from dataclasses import dataclass
from typing import Optional
from ..enums import ResearcherActivityStatus


@dataclass(slots=True, unsafe_hash=True)
class Researcher:
    researcher_id: int
    replication_probability: float
    target_power: float

    timestep_active: int
    timestep_next_paper: int
    timestep_inactive: Optional[int]

    activity_status: ResearcherActivityStatus

    @staticmethod
    def create(researcher_id: int, timestep: int) -> "Researcher":
        """
        Initializes a researcher based on Section 5.2 of spec.
        """
        import random
        
        # Replication probability: Bernoulli(0.5) -> 0 or 1
        repl_prob = 1.0 if random.random() < 0.5 else 0.0
        
        # Target power: Uniform(0.01, 0.99)
        power = random.uniform(0.01, 0.99)
        
        return Researcher(
            researcher_id=researcher_id,
            replication_probability=repl_prob,
            target_power=power,
            timestep_active=timestep,
            timestep_next_paper=timestep, # Immediately ready
            timestep_inactive=None,
            activity_status=ResearcherActivityStatus.ACTIVE
        )

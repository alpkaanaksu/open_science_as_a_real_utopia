from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ResearcherActivityStatus(Enum):
    INACTIVE = 0
    ACTIVE = 1


@dataclass(slots=True)
class Researcher:
    researcher_id: int
    replication_probability: float
    target_power: float

    timestep_active: int
    timestep_next_paper: int
    timestep_inactive: Optional[int]

    activity_status: ResearcherActivityStatus

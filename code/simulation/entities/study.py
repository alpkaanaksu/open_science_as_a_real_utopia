from dataclasses import dataclass
from enum import Enum


class StudyType(Enum):
    ORIGINAL = 0
    REPLICATION = 1


class PublicationStatus(Enum):
    FILE_DRAWER = 0
    PUBLISHED = 1


@dataclass(slots=True)
class Study:
    study_id: int
    researcher_id: int
    effect_id: int

    study_type: StudyType
    publication_status: PublicationStatus

    timestep_completed: int
    sample_size: int

    estimated_mean: float
    estimated_se: float
    p_value: float

    novelty_contribution: float
    truth_contribution: float

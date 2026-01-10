from dataclasses import dataclass
from ..enums import StudyType, PublicationStatus


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

    publishing_journal: str = None

    @staticmethod
    def calculate_duration(study_type: StudyType, sample_size: int) -> int:
        from ..formulas import calculate_study_duration
        return calculate_study_duration(study_type, sample_size)

    @staticmethod
    def calculate_sample_size(target_power: float, reference_effect_size: float, is_two_sided: bool) -> int:
        """
        Calculates sample size based on target power and reference effect size.
        Section 7.3 of spec.
        """
        from ..formulas import calculate_sample_size
        return calculate_sample_size(target_power, reference_effect_size, is_two_sided)

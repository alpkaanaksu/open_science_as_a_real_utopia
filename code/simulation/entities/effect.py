from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Effect:
    effect_id: int
    timestep: int

    true_effect_size: float
    true_effect_variance: float

    prior_effect_size: float
    prior_effect_variance: float

    posterior_effect_size: float
    posterior_effect_variance: float

    study_id: Optional[int]

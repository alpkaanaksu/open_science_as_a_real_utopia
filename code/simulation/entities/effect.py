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

    def update_belief(self, study_result_d: float, study_se: float, study_id: int):
        from ..formulas import update_belief_posterior
        
        self.posterior_effect_size, self.posterior_effect_variance = update_belief_posterior(
            self.posterior_effect_size, 
            self.posterior_effect_variance,
            study_result_d, 
            study_se
        )
        self.study_id = study_id

    @staticmethod
    def create(effect_id: int, timestep: int) -> "Effect":
        import random
        from .. import config
        
        # True effect size generation
        if random.random() < config.base_null_probability:
            true_d = 0.0
        else:
            true_d = random.normalvariate(config.effect_size_mean, config.effect_size_variance**0.5)
            
        return Effect(
            effect_id=effect_id,
            timestep=timestep,
            true_effect_size=true_d,
            true_effect_variance=0.01, # Fixed as per spec
            prior_effect_size=config.uninformed_prior_mean,
            prior_effect_variance=config.uninformed_prior_variance,
            posterior_effect_size=config.uninformed_prior_mean,
            posterior_effect_variance=config.uninformed_prior_variance,
            study_id=None
        )

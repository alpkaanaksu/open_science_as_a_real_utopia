# Population parameters
number_of_researchers = 500
number_of_effects = 100_000

# Temporal parameters
timesteps_max = 300
timesteps_per_career_step = 35

# Peer Review
max_journal_submissions = 5 # Number of journals a paper can be submitted to before giving up

# Replications
max_replications_per_effect = None # Maximum number of replications per effect
replication_journal = True # Whether to include a specialized replication journal

# Effects distribution parameters
base_null_probability = 0.9
effect_size_mean = 0.3
effect_size_variance = 0.1

# Prior belief parameters
uninformed_prior_mean = 0.0
uninformed_prior_variance = 1.0

# Study duration parameters
duration_per_observation = 0.1
duration_original_intercept = 1

from .enums import SelectionStrategy, PublicationBias

# Carrer selection parameters
initial_selection_condition = SelectionStrategy.NOVELTY # 0 = truth selection, 1 = novelty selection
career_turnover_selection_rate = 0.5
innovation_sd = 0

# Publication bias parameters
publication_bias = PublicationBias.WEAK # 0 = none, 1 = weak, 2 = strong

hold_samples_constant_at = None # If not None, fixes sample size for all studies

# Journal Configuration
from .journal_config import journals, JournalSpecification
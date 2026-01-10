import math
from scipy import stats
from . import config
from .enums import StudyType, PublicationBias

def calculate_sample_size(target_power: float, reference_effect_size: float, is_two_sided: bool) -> int:
    """
    Calculates sample size based on target power and reference effect size.
    Section 7.3 of spec.
    """
    if config.hold_samples_constant_at is not None:
        return config.hold_samples_constant_at
        
    alpha = 0.05
    
    # Critical values
    if is_two_sided:
        z_alpha = stats.norm.ppf(1 - alpha/2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
        
    z_beta = stats.norm.ppf(target_power)
    
    # Sample size formula: n = 2 * [(z_alpha + z_beta)^2 / delta^2] + 1
    numerator = (z_alpha + z_beta)**2
    denominator = reference_effect_size**2
    
    n = 2 * (numerator / denominator) + 1
    return math.ceil(n)

def calculate_study_duration(study_type: StudyType, sample_size: int) -> int:
    """
    Calculates study duration.
    Section 7.4 of spec.
    """
    base_term = config.duration_per_observation * sample_size
    
    if study_type == StudyType.ORIGINAL:
        duration = config.duration_original_intercept + base_term
    else:
        duration = base_term
        
    return max(1, math.ceil(duration))

def update_belief_posterior(prior_mean: float, prior_var: float, 
                          study_d: float, study_se: float) -> tuple[float, float]:
    """
    Updates collective beliefs using Bayesian conjugate analysis for normal distributions.
    Returns (new_mean, new_variance).
    Section 7.6 of spec.
    """
    # SE is standard error, so var_likelihood = SE^2
    likelihood_variance = study_se**2
    
    inv_prior_var = 1.0 / prior_var
    inv_likelihood_var = 1.0 / likelihood_variance
    
    new_posterior_variance = 1.0 / (inv_prior_var + inv_likelihood_var)
    
    new_posterior_mean = new_posterior_variance * (
        prior_mean / prior_var + 
        study_d / likelihood_variance
    )
    
    return new_posterior_mean, new_posterior_variance

def calculate_kl_divergence(m1: float, v1: float, m2: float, v2: float) -> float:
    """
    Calculates KL Divergence between two normal distributions N(m1, v1) and N(m2, v2).
    D_KL(P || Q) where P is N(m1, v1) and Q is N(m2, v2).
    """
    term1 = math.log(math.sqrt(v2) / math.sqrt(v1))
    term2 = (v1 + (m1 - m2)**2) / (2 * v2)
    return term1 + term2 - 0.5

def simulate_study_result(sample_size: int, true_d: float) -> tuple[float, float, float]:
    """
    Simulates study results (d_obs, se_d, t_obs).
    Section 7.5 of spec.
    Returns (d_obs, se_d, t_obs).
    """
    ncp = (sample_size / 2.0)**0.5 * true_d
    df = 2 * (sample_size - 1)
    
    t_obs = stats.nct.rvs(df, ncp)
    d_obs = t_obs * (2.0 / sample_size)**0.5
    
    # Hedges-Olkin formula for SE
    se_d = (2.0/sample_size + d_obs**2 / (4*sample_size))**0.5
    
    return d_obs, se_d, t_obs, df

def calculate_p_value(t_obs: float, df: int, study_type: StudyType, original_direction: float = 1.0) -> float:
    """
    Calculates p-value from t-statistic.
    """
    if study_type == StudyType.ORIGINAL:
        # Two-sided
        return 2 * (1 - stats.t.cdf(abs(t_obs), df))
    else:
        # One-sided in direction of original
        if original_direction > 0:
            return 1 - stats.t.cdf(t_obs, df)
        else:
            return stats.t.cdf(t_obs, df)

def calculate_publication_probability(is_sig: bool, novelty: float, bias_level: PublicationBias) -> float:
    """
    Calculates publication probability based on significance, novelty, and bias level.
    Section 7.8 of spec.
    """
    # Level: (sig_y_int, sig_mid, sig_k, nonsig_mid, nonsig_k)
    params = {
        PublicationBias.NONE: (1.0, 0.0, 0.0, 0.0, 0.0),
        PublicationBias.WEAK: (0.5, 0.5, 3.0, 1.5, 3.0),
        PublicationBias.STRONG: (0.8, 0.2, 3.0, 3.0, 3.0)
    }
    
    if bias_level == PublicationBias.NONE:
        return 1.0
        
    sig_y_int, sig_m, sig_k, nonsig_m, nonsig_k = params.get(bias_level, params[PublicationBias.WEAK])
    
    if is_sig:
        # P = y_int + (1 - y_int) / (1 + exp(-k * (novelty - m)))
        return sig_y_int + (1 - sig_y_int) / (1 + math.exp(-sig_k * (novelty - sig_m)))
    else:
        # P = 1 / (1 + exp(-k * (novelty - m)))
        return 1.0 / (1 + math.exp(-nonsig_k * (novelty - nonsig_m)))

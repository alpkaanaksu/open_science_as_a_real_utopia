import csv
import json
import os
from typing import List, Dict, Any, Optional
import statistics

from . import config
from .enums import StudyType

class StatisticsCollector:
    def __init__(self):
        self.step_data: List[Dict[str, Any]] = []
        self.study_data: List[Dict[str, Any]] = []
        
    def collect_step(self, sim):
        """
        Collects population-level statistics for the current timestep.
        """
        researchers = sim.researchers
        published = sim.published_studies
        
        # Trait statistics
        if researchers:
            repl_probs = [r.replication_probability for r in researchers]
            target_powers = [r.target_power for r in researchers]
            
            mean_repl = statistics.mean(repl_probs)
            sd_repl = statistics.stdev(repl_probs) if len(repl_probs) > 1 else 0
            
            mean_power = statistics.mean(target_powers)
            sd_power = statistics.stdev(target_powers) if len(target_powers) > 1 else 0
        else:
            mean_repl = sd_repl = mean_power = sd_power = 0
            
        # Additional Stats for Visualization
        total_studies = sim.all_studies
        n_total = len(total_studies)
        n_repl_total = sum(1 for s in total_studies if s.study_type == StudyType.REPLICATION)
        
        unique_effects = {s.effect_id for s in total_studies}
        n_explored = len(unique_effects)
        avg_per_effect = n_total / n_explored if n_explored > 0 else 0.0
        
        # Calculate Belief Accuracy (MAE for published effects)
        # Access effects domain directly
        all_effects = sim.effects
        # Filter for effects that have been updated (have at least one published study)
        # We can use study_id check or check if posterior variance < prior variance
        # study_id check is safer if we trust update_belief sets it
        explored_effects_objs = [e for e in all_effects if e.study_id is not None]
        
        if explored_effects_objs:
            from .formulas import calculate_kl_divergence
            # D_KL(True || Posterior)
            # Spec 7.10: "sum of KL divergences" -> "accuracy metric".
            # User wants "Mean KL divergence".
            
            kl_divs = []
            for e in explored_effects_objs:
                # True dist: N(true_d, 0.01) - variance assumes spec default or we need to access it
                # Effect entity has true_effect_variance? Checking properties...
                # Checked previous files: Effect has true_effect_variance (default 0.01? or initialized)
                
                # Using e.true_effect_variance if it exists, else hardcode small var as per spec?
                # Spec 5.1 creates effects. Let's assume the attribute exists.
                true_var = e.true_effect_variance if hasattr(e, 'true_effect_variance') else 0.01
                
                kl = calculate_kl_divergence(
                    e.true_effect_size, true_var,
                    e.posterior_effect_size, e.posterior_effect_variance
                )
                kl_divs.append(kl)
                
            mean_kl = sum(kl_divs) / len(kl_divs)
            
            mean_kl = sum(kl_divs) / len(kl_divs)
        else:
            mean_kl = 0.0

        
        # Count types in published
        # Optimized: Sim maintains separate list or we filter. 
        # For performance, iterating here is O(N_published). N ~ 1000s -> acceptable.
        n_orig = sum(1 for s in published if s.study_type == StudyType.ORIGINAL)
        n_repl = sum(1 for s in published if s.study_type == StudyType.REPLICATION)
        
        # Record
        row = {
            "timestep": sim.current_timestep,
            "n_researchers": len(researchers),
            "n_published": len(published),
            "n_published_original": n_orig,
            "n_published_replication": n_repl,
            "n_file_drawer": len(sim.all_studies) - len(sim.published_studies) - len(sim.pending_studies),
            "mean_replication_prob": mean_repl,
            "sd_replication_prob": sd_repl,
            "mean_target_power": mean_power,
            "sd_target_power": sd_power,
            
            # New Metrics
            "n_total_studies": n_total,
            "n_total_replications": n_repl_total,
            "n_explored_effects": n_explored,
            "avg_studies_per_effect": avg_per_effect,
            "mean_kl_divergence": mean_kl,
            "mean_kl_divergence": mean_kl,
            
            # Placeholder for belief accuracy if we implement it later
            # "belief_accuracy": sim.calculate_belief_accuracy() 
        }
        
        # Per-Journal Stats
        from . import config
        # Initialize counts
        journal_counts = {j.name: 0 for j in config.journals}
        for s in published:
            if s.publishing_journal in journal_counts:
                journal_counts[s.publishing_journal] += 1
        
        #Flatten into row
        for name, count in journal_counts.items():
            row[f"pub_journal_{name}"] = count
            
        self.step_data.append(row)

    def collect_study(self, study):
        """
        Collects data for a single completed study.
        """
        row = {
            "study_id": study.study_id,
            "researcher_id": study.researcher_id,
            "effect_id": study.effect_id,
            "timestep_completed": study.timestep_completed,
            "study_type": str(study.study_type), # Enum to str
            "sample_size": study.sample_size,
            "estimated_mean": study.estimated_mean,
            "estimated_se": study.estimated_se,
            "p_value": study.p_value,
            "novelty_contribution": study.novelty_contribution,
            "truth_contribution": study.truth_contribution,
            "publication_status": str(study.publication_status), # Enum to str
            "publishing_journal": study.publishing_journal
        }
        self.study_data.append(row)

    def save(self, prefix: str = "simulation_output"):
        """
        Saves collected data to CSV files.
        """
        # Save Step Data
        if self.step_data:
            keys = self.step_data[0].keys()
            with open(f"{prefix}_steps.csv", "w", newline="") as f:
                dict_writer = csv.DictWriter(f, keys)
                dict_writer.writeheader()
                dict_writer.writerows(self.step_data)
                
        # Save Study Data
        if self.study_data:
            keys = self.study_data[0].keys()
            with open(f"{prefix}_studies.csv", "w", newline="") as f:
                dict_writer = csv.DictWriter(f, keys)
                dict_writer.writeheader()
                dict_writer.writerows(self.study_data)

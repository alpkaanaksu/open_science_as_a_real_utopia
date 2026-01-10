import random
import math
from typing import List, Optional, Dict, Callable, Any
from scipy import stats

from . import config
from .enums import SelectionStrategy, PublicationBias, StudyType, PublicationStatus, ResearcherActivityStatus
from .entities.study import Study
from .entities.researcher import Researcher
from .entities.effect import Effect
from .statistics import StatisticsCollector

class Simulation:
    def __init__(self):
        # 3. Create Domains (Now Refactored to Lists)
        # All Effects (Knowledge Base)
        self.effects: List[Effect] = [
            Effect.create(effect_id=i, timestep=0) 
            for i in range(config.number_of_effects)
        ]
        
        # Active Researchers
        self.researchers: List[Researcher] = [
            Researcher.create(researcher_id=i, timestep=0)
            for i in range(config.number_of_researchers)
        ]
        
        # Published Studies (Literature)
        self.published_studies: List[Study] = []
        
        # Pending Studies (Staging for Peer Review)
        self.pending_studies: List[Study] = []
        
        # Track all studies (including file drawer)
        self.all_studies: List[Study] = []
        self.study_counter = 0
        
        # Statistics
        self.stats = StatisticsCollector()
        
        # Configuration
        self.journals = config.journals
        self.current_timestep = 0


    def step(self):
        """
        Executes a single timestep.
        Section 3 of spec (Modified Event Loop).
        """
        # 1. Researchers Act: Conduct studies
        self._researchers_act()
        
        # 2. Peer Review: Publish or File Drawer
        self._handle_peer_review()
        
        # 3. Career Updates: Every N steps
        if self.current_timestep > 0 and self.current_timestep % config.timesteps_per_career_step == 0:
            self._handle_career_updates()
            
    def _researchers_act(self):
        """
        Logic for researchers to conduct studies.
        """
        active_researchers = self.researchers
        published_studies = self.published_studies
        
        # Identify ready researchers
        ready_researchers = [r for r in active_researchers if r.timestep_next_paper <= self.current_timestep]
        
        # Published effect IDs set for fast lookup
        published_effect_ids = {s.effect_id for s in published_studies}
        
        # Pre-calculate valid replication candidates if limit exists
        valid_replication_candidates = []
        if published_studies:
            if config.max_replications_per_effect is not None:
                # Count current replications
                # We need to count PUBLISHED replications.
                from collections import Counter
                repl_counts = Counter(s.effect_id for s in published_studies if s.study_type == StudyType.REPLICATION)
                
                # Filter effects
                # We want effect_ids that have appeared in ANY published study (so they are "published"),
                # BUT have fewer than MAX replications.
                # published_effect_ids contains all effects that have at least one study (original or replication).
                
                valid_replication_candidates = [
                    eid for eid in published_effect_ids 
                    if repl_counts[eid] < config.max_replications_per_effect
                ]
            else:
                # Unlimited: candidates are all published effect IDs.
                # Weighted by number of publications? "candidates = [s.effect_id for s in published_studies]" was weighted.
                # If an effect has 10 papers, it appears 10 times in list -> 10x chance.
                # The user didn't ask to change this weighting, so let's preserve it.
                valid_replication_candidates = [s.effect_id for s in published_studies]
        
        for researcher in ready_researchers:
            # Determine Study Type (7.1)
            is_replication = random.random() < researcher.replication_probability
            
            target_effect = None
            study_type = StudyType.ORIGINAL
            
            if is_replication:
                # 7.2.2 Replication: requires published studies
                if published_studies:
                    # Count replications per effect if limit is set
                    # Optimization: Do this ONCE per timestep or just filter candidates
                    # Since candidates are chosen randomly, we can filter lazily? 
                    # No, we need valid list. But constructing list of all 1000s studies each researcher... performance?
                    # Let's count once at start of function? But publications don't change within a timestep until `_handle_peer_review` updates them?
                    # The `published_studies` list DOES NOT change within `_researchers_act`! Researchers conduct studies, but they go to `pending_studies`.
                    # Peer review happens AFTER `_researchers_act`.
                    # So we can calculate replication counts ONCE at the start of `_researchers_act`.
                    
                    # This logic is moved outside the loop for performance, see below.
                    # Using global `valid_replication_candidates` computed at start.
                    
                    if valid_replication_candidates:
                        target_effect_id = random.choice(valid_replication_candidates)
                        target_effect = self.effects[target_effect_id]
                        study_type = StudyType.REPLICATION
                    else:
                        is_replication = False
                else:
                    is_replication = False
            
            if not is_replication: # Original
                # 7.2.1 Original: novel effects
                # Naive implementation: sample until finding one not published
                while True:
                    candidate_id = random.randint(0, config.number_of_effects - 1)
                    if candidate_id not in published_effect_ids:
                        target_effect = self.effects[candidate_id]
                        break
                study_type = StudyType.ORIGINAL
            
            # Create Study
            self.study_counter += 1
            new_study = Study(
                study_id=self.study_counter,
                researcher_id=researcher.researcher_id,
                effect_id=target_effect.effect_id,
                study_type=study_type,
                publication_status=PublicationStatus.FILE_DRAWER, # Default
                timestep_completed=0, # Placeholder
                sample_size=0,
                estimated_mean=0.0,
                estimated_se=0.0,
                p_value=0.0,
                novelty_contribution=0.0,
                truth_contribution=0.0,
                publishing_journal=None
            )
            
            # Calculate Sample Size (7.3)
            reference_effect_size = 0.5 # Default burn-in
            is_two_sided = (study_type == StudyType.ORIGINAL)
            
            # Refine reference effect size
            if study_type == StudyType.REPLICATION:
                prior_studies = [s for s in published_studies if s.effect_id == target_effect.effect_id]
                if prior_studies:
                    original = prior_studies[0]
                    if original.p_value < 0.05:
                        reference_effect_size = abs(original.estimated_mean)
                    else:
                        reference_effect_size = 0.5
            else:
                 # Original: "After burn-in, reference effect is mean of all published effect sizes"
                 if self.current_timestep > config.timesteps_per_career_step and published_studies:
                      mean_pub = sum(abs(s.estimated_mean) for s in published_studies) / len(published_studies)
                      reference_effect_size = mean_pub

            sample_size = Study.calculate_sample_size(researcher.target_power, reference_effect_size, is_two_sided)
            new_study.sample_size = sample_size
            
            # Calculate Duration (7.4)
            duration = Study.calculate_duration(study_type, sample_size)
            researcher.timestep_next_paper = self.current_timestep + duration
            new_study.timestep_completed = self.current_timestep + duration
            
            # Generate Results (7.5)
            true_d = target_effect.true_effect_size
            
            from .formulas import simulate_study_result, calculate_p_value, update_belief_posterior, calculate_kl_divergence
            
            d_obs, se_d, t_obs, df = simulate_study_result(sample_size, true_d)
            
            # p-value
            if new_study.study_type == StudyType.ORIGINAL:
                 p_val = calculate_p_value(t_obs, df, StudyType.ORIGINAL)
            else:
                # One-sided in direction of original
                prior_studies = [s for s in published_studies if s.effect_id == target_effect.effect_id]
                original_direction = 1.0 
                if prior_studies:
                    if prior_studies[0].estimated_mean < 0:
                        original_direction = -1.0
                
                p_val = calculate_p_value(t_obs, df, StudyType.REPLICATION, original_direction)
            
            new_study.estimated_mean = d_obs
            new_study.estimated_se = se_d
            new_study.p_value = p_val
            
            # Contribution Metrics (7.7)
            # Calculated relative to CURRENT beliefs (before update).
            curr_mean = target_effect.posterior_effect_size
            curr_var = target_effect.posterior_effect_variance
            
            post_mean, post_var = update_belief_posterior(curr_mean, curr_var, d_obs, se_d)
            
            # Novelty: KL(Post || Prior)
            novelty = calculate_kl_divergence(post_mean, post_var, curr_mean, curr_var)
            
            # Truth: D_KL(True || Prior) - D_KL(True || Post)
            true_var = 0.01
            kl_true_prior = calculate_kl_divergence(true_d, true_var, curr_mean, curr_var)
            kl_true_post = calculate_kl_divergence(true_d, true_var, post_mean, post_var)
            
            truth_contrib = kl_true_prior - kl_true_post
            
            new_study.novelty_contribution = novelty
            new_study.truth_contribution = truth_contrib
            
            self.all_studies.append(new_study)
            self.pending_studies.append(new_study)


    def _handle_peer_review(self):
        """
        Moves studies from pending to published if approved by ANY journal.
        "Shopping Around" logic.
        """
        items_to_process = list(self.pending_studies)
        self.pending_studies.clear()
        
        for study in items_to_process:
            is_published = False
            publishing_journal_name = None
            
            # Shopping Around: Random order of journals
            available_journals = list(self.journals)
            random.shuffle(available_journals)
            
            for journal in available_journals:
                if self._check_journal_acceptance(journal, study):
                    is_published = True
                    publishing_journal_name = journal.name
                    break
            
            if is_published:
                study.publication_status = PublicationStatus.PUBLISHED
                study.publishing_journal = publishing_journal_name
                
                # Update beliefs
                target_effect = self.effects[study.effect_id]
                target_effect.update_belief(study.estimated_mean, study.estimated_se, study.study_id)
                self.published_studies.append(study)
            else:
                study.publication_status = PublicationStatus.FILE_DRAWER
            
            # Collect stats
            self.stats.collect_study(study)

    def _check_journal_acceptance(self, journal, study: Study) -> bool:
        """
        Checks if a specific journal accepts the study.
        """
        # 1. Check Filters
        if "replication_only" in journal.filters:
            if study.study_type != StudyType.REPLICATION:
                return False
                
        # 2. Check Bias (Significance/Novelty)
        from .formulas import calculate_publication_probability
        
        is_sig = study.p_value < 0.05
        novelty = study.novelty_contribution
        bias_level = journal.bias
        
        prob = calculate_publication_probability(is_sig, novelty, bias_level)
        return random.random() < prob


    def _handle_career_updates(self):
        """
        Handles tenure review (firing) and recruitment (hiring).
        """
        # 1. Rank Researchers
        # Sort desc or asc? _get_researcher_career_score returns higher is better.
        # sorted() is ascending by default. So bottom ones are at start.
        # But simulation needs to remove bottom %.
        
        current_roster = list(self.researchers)
        if not current_roster:
            return

        # Calculate scores
        roster_with_scores = []
        for r in current_roster:
            score = self._get_researcher_career_score(r)
            roster_with_scores.append((r, score))
            
        # Sort by score (Lowest first)
        roster_with_scores.sort(key=lambda x: x[1])
        
        # 2. Fire Bottom %
        n_remove = int(len(current_roster) * config.career_turnover_selection_rate)
        
        survivors = []
        removed_count = 0
        
        for i, (r, score) in enumerate(roster_with_scores):
            if i < n_remove:
                # Fire
                r.timestep_inactive = self.current_timestep
                r.activity_status = ResearcherActivityStatus.INACTIVE
                removed_count += 1
            else:
                # Keep
                survivors.append(r)
        
        self.researchers = survivors
        
        # 3. Hire Replacements (Offspring)
        n_needed = config.number_of_researchers - len(self.researchers)
        if n_needed > 0:
            new_hires = self._create_new_researchers(n_needed)
            self.researchers.extend(new_hires)
            
    def _get_researcher_career_score(self, researcher: Researcher) -> float:
        """
        Calculates the career score.
        """
        selection_condition = config.initial_selection_condition
        phase_start = self.current_timestep - config.timesteps_per_career_step
        
        # Optimize: iterating all studies is slow. But standard method.
        # In full sim, mapping study -> researcher would be faster.
        score = 0.0
        relevant_studies = [s for s in self.all_studies 
                            if s.researcher_id == researcher.researcher_id
                            and s.timestep_completed > phase_start 
                            and s.timestep_completed <= self.current_timestep]
                            
        for study in relevant_studies:
            if selection_condition == SelectionStrategy.TRUTH: 
                score += study.truth_contribution
            else: # Novelty
                if study.publication_status == PublicationStatus.PUBLISHED:
                    score += study.novelty_contribution
        return score

    def _create_new_researchers(self, n_needed: int) -> List[Researcher]:
        """
        Creates new researchers mutated from survivors.
        """
        survivors = self.researchers
        new_researchers = []
        
        if not hasattr(self, 'researcher_id_counter'):
             self.researcher_id_counter = config.number_of_researchers - 1
             
        for _ in range(n_needed):
            self.researcher_id_counter += 1
            next_id = self.researcher_id_counter
            
            if survivors:
                parent = random.choice(survivors)
                
                # Mutate
                new_repl = parent.replication_probability + random.normalvariate(0, config.innovation_sd)
                new_repl = max(0.0, min(1.0, new_repl))
                
                new_power = parent.target_power + random.normalvariate(0, config.innovation_sd)
                new_power = max(0.01, min(0.99, new_power))
            else:
                new_repl = 0.5
                new_power = 0.8
            
            new_r = Researcher(
                researcher_id=next_id,
                replication_probability=new_repl,
                target_power=new_power,
                timestep_active=self.current_timestep,
                timestep_next_paper=self.current_timestep,
                timestep_inactive=None,
                activity_status=ResearcherActivityStatus.ACTIVE
            )
            new_researchers.append(new_r)
        return new_researchers

    def run(self, on_step_callback: Callable = None):
        """
        Runs the simulation.
        """
        for t in range(1, config.timesteps_max + 1):
            self.current_timestep = t
            self.step()
            self.stats.collect_step(self)
            
            if on_step_callback:
                on_step_callback(self)
            
            if t % 10 == 0:
                print(f"Timestep {t}/{config.timesteps_max}: "
                      f"Researchers={len(self.researchers)}, "
                      f"Published={len(self.published_studies)}")
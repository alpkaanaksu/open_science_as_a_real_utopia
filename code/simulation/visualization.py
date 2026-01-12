try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from .simulation import Simulation
from . import config
from .enums import SelectionStrategy, PublicationBias

class Visualizer:
    def __init__(self):
        if not HAS_MATPLOTLIB:
            print("Error: matplotlib not installed. Visualization disabled.")
            return

        self.fig, ((self.ax1, self.ax3, self.ax5), (self.ax2, self.ax4, self.ax6)) = plt.subplots(2, 3, figsize=(18, 10))
        plt.ion() # Interactive mode
        self.fig.tight_layout(pad=4.0)
        
        # Display Configuration
        sel_strat = config.initial_selection_condition.name.title()
        bias_level = config.publication_bias.name.title()
        
        config_text = (
            f"Researchers: {config.number_of_researchers} | "
            f"Effects: {config.number_of_effects} | "
            f"Bias: {bias_level}\n"
            f"Selection: {sel_strat} | "
            f"Career Steps: {config.timesteps_per_career_step} steps"
        )
        self.fig.text(0.5, 0.96, "Academia in Silico", ha='center', fontsize=16, fontweight='bold')
        self.fig.text(0.5, 0.93, config_text, ha='center', fontsize=11)
        self.fig.subplots_adjust(top=0.88, hspace=0.3, wspace=0.3)
        
        # Data storage - Separate X/Y for each series to allow filtered updates
        self.data_repl = {'x': [], 'y': []}
        self.data_power = {'x': [], 'y': []}
        self.data_kl = {'x': [], 'y': []}
        self.data_ratio = {'x': [], 'y': []}
        
        # Plot 1: Traits (Top Left)
        self.ax1.set_title("Researcher Traits Evolution")
        self.ax1.set_xlabel("Timestep")
        self.ax1.set_ylabel("Trait Value")
        self.ax1.set_ylim(0, 1)
        self.line_repl, = self.ax1.plot([], [], label="Mean Replication Prob", color="blue", marker='o', markersize=2)
        self.line_power, = self.ax1.plot([], [], label="Mean Target Power", color="red", marker='o', markersize=2)
        self.ax1.legend()
        
        # Plot 2: Belief Accuracy (Bottom Left)
        self.ax2.set_title("Mean KL Divergence (True || Posterior)")
        self.ax2.set_xlabel("Timestep")
        self.ax2.set_ylabel("D_KL")
        self.line_error, = self.ax2.plot([], [], label="Mean KL", color="orange", marker='o', markersize=2)
        self.ax2.legend()
        
        # Plot 3: Replication Ratio (Top Right)
        self.ax3.set_title("Replication / Original Ratio (Published)")
        self.ax3.set_xlabel("Timestep")
        self.ax3.set_ylabel("Ratio (R/O)")
        self.line_ratio, = self.ax3.plot([], [], label="R/O Ratio", color="purple", marker='o', markersize=2)
        self.ax3.legend()

        # Plot 5: Publications per Journal (Top Far Right)
        self.ax5.set_title("Publications by Journal")
        self.ax5.set_xlabel("Timestep")
        self.ax5.set_ylabel("Count")
        
        # Initialize dictionary for journal lines
        self.journal_lines = {}
        colors = ['cyan', 'magenta', 'lime', 'pink', 'brown', 'gray'] # Simple color cycle
        
        # Deduplicate journals by name for plotting
        unique_journals = {}
        for j in config.journals:
            if j.name not in unique_journals:
                unique_journals[j.name] = j
        
        sorted_names = sorted(unique_journals.keys())
        self.data_journals = {name: {'x': [], 'y': []} for name in sorted_names}

        for i, name in enumerate(sorted_names):
             c = colors[i % len(colors)]
             line, = self.ax5.plot([], [], label=name, color=c, marker='x', markersize=2)
             self.journal_lines[name] = line
             
        self.ax5.legend()
        
        # Plot 6: Statistics (Bottom Far Right or somewhere else)
        # Assuming layout is:
        # 1(Traits)  3(Ratio)   5(Journals)
        # 2(KL)      4(Empty?)  6(Stats)
        
        # Original ax4 was stats. Let's make ax6 stats.
        self.ax6.axis("off")
        self.stats_text = self.ax6.text(0.1, 0.5, "Collecting data...", fontsize=12, verticalalignment='center')
        
        # Plot 4: Empty (Previously MSE)
        self.ax4.axis("off")
        
        # Plot 4: Statistics (Bottom Right)

        
        # Track max timestep for global scaling
        self.max_timestep = 0

        print("Visualizer initialized. Window should appear.")

    def _update_series(self, series_dict: dict, t: int, value: float):
        """Helper to append data point only if value changes (avoids stairs)."""
        # Always add first point
        if not series_dict['y']:
            series_dict['x'].append(t)
            series_dict['y'].append(value)
            return

        # Check change
        last_val = series_dict['y'][-1]
        if value != last_val:
            series_dict['x'].append(t)
            series_dict['y'].append(value)

    def update(self, sim: Simulation):
        if not HAS_MATPLOTLIB:
            return

        # Append new data from the last step stats
        if not sim.stats.step_data:
            return
            
        latest = sim.stats.step_data[-1]
        t = latest["timestep"]
        self.max_timestep = max(self.max_timestep, t)
        
        # Update Series with filtering
        self._update_series(self.data_repl, t, latest["mean_replication_prob"])
        self._update_series(self.data_power, t, latest["mean_target_power"])
        
        kl_div = latest.get("mean_kl_divergence", 0.0)
        self._update_series(self.data_kl, t, kl_div)


        
        # Calculate ratio and update series
        n_repl = latest.get("n_published_replication", 0)
        n_orig = latest.get("n_published_original", 0)
        ratio = n_repl / n_orig if n_orig > 0 else 0.0
        self._update_series(self.data_ratio, t, ratio)
        
        # Update Journal Series
        for j_name, series in self.data_journals.items():
            key = f"pub_journal_{j_name}"
            val = latest.get(key, 0)
            self._update_series(series, t, val)
        
        # Update plots
        max_t = self.max_timestep
        
        # Plot 1
        self.line_repl.set_data(self.data_repl['x'], self.data_repl['y'])
        self.line_power.set_data(self.data_power['x'], self.data_power['y'])
        self.ax1.set_xlim(0, max_t + 10)
        
        # Plot 2: Belief Error
        self.line_error.set_data(self.data_kl['x'], self.data_kl['y'])
        self.ax2.set_xlim(0, max_t + 10)
        
        # Dynamic Y limits
        all_kl = self.data_kl['y']
        max_kl = max(all_kl) if all_kl else 1.0
        self.ax2.set_ylim(0, max(max_kl * 1.1, 0.1)) # Changed from + 0.01 to max(..., 0.1)
        

        
        # Plot 3
        self.line_ratio.set_data(self.data_ratio['x'], self.data_ratio['y'])
        self.ax3.set_xlim(0, max_t + 10)
        all_ratios = self.data_ratio['y']
        max_ratio = max(all_ratios) if all_ratios else 0
        self.ax3.set_ylim(0, max(1.0, max_ratio * 1.1)) # At least 1.0 for view
        self.ax3.relim()
        self.ax3.autoscale_view()
        
        # Plot 5: Journals
        max_j_val = 0
        for j_name, line in self.journal_lines.items():
            series = self.data_journals[j_name]
            line.set_data(series['x'], series['y'])
            if series['y']:
                max_j_val = max(max_j_val, max(series['y']))
                
        self.ax5.set_xlim(0, max_t + 10)
        self.ax5.set_ylim(0, max_j_val * 1.1 + 1)

        n_tot = latest.get("n_total_studies", 0)
        n_repl_tot = latest.get("n_total_replications", 0)
        n_pub = latest.get("n_published", 0)
        n_pub_orig = latest.get("n_published_original", 0)
        n_pub_repl = latest.get("n_published_replication", 0)
        n_explored = latest.get("n_explored_effects", 0)
        avg_studies = latest.get("avg_studies_per_effect", 0.0)
        mean_kl = latest.get("mean_kl_divergence", 0.0)
        
        pub_rate = (n_pub / n_tot * 100) if n_tot > 0 else 0.0
        
        stats_msg = (
            f"TIMESTEP: {latest['timestep']}\n\n"
            f"Total Studies: {n_tot}\n"
            f"  - Original: {n_tot - n_repl_tot}\n"
            f"  - Replication: {n_repl_tot}\n\n"
            f"Published Studies: {n_pub}\n"
            f"  - Publication Rate: {pub_rate:.1f}%\n"
            f"  - Ratio (R/O): {ratio:.2f}\n\n"
            f"Scientific Knowledge:\n"
            f"  - Explored Effects: {n_explored}\n"
            f"  - Avg Studies/Effect: {avg_studies:.2f}\n"
            f"  - Mean KL Divergence: {mean_kl:.3f}\n"
            f"  - Mean KL Divergence: {mean_kl:.3f}\n"
        )
        self.stats_text.set_text(stats_msg)
        
        # Debug: Confirm data is flowing
        if t % 10 == 0:
            print(f"Visualizer: Plotting to T={max_t}")
        
        # Draw
        self.fig.canvas.flush_events()
        self.fig.canvas.draw()
        plt.pause(0.01) # Slightly shorter pause is usually fine with flush

    def save_plot(self, filepath: str):
        """Saves the current figure to a file."""
        if HAS_MATPLOTLIB:
            self.fig.savefig(filepath)
            print(f"Visualization saved to {filepath}")

    def close(self):
        if HAS_MATPLOTLIB:
            plt.ioff()
            # plt.show() # Keep window open until closed by user -> Handled by main.py logic now

    def show_blocking(self):
        """Blocks execution until plot window is closed."""
        if HAS_MATPLOTLIB:
            plt.show()

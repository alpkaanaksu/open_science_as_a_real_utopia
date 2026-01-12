import argparse
import sys
import os

# Ensure the current directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation import config
from simulation.enums import SelectionStrategy, PublicationBias
from simulation.simulation import Simulation

def main():
    parser = argparse.ArgumentParser(description="Run the Scientific Community Simulation.")
    
    # Population
    parser.add_argument("--researchers", type=int, default=config.number_of_researchers, help="Number of researchers")
    parser.add_argument("--effects", type=int, default=config.number_of_effects, help="Number of effects")
    
    # Temporal
    parser.add_argument("--timesteps", type=int, default=config.timesteps_max, help="Max timesteps")
    parser.add_argument("--career_steps", type=int, default=config.timesteps_per_career_step, help="Timesteps per career step")
    
    # Bias & Selection
    parser.add_argument("--bias", type=int, default=config.publication_bias, help="Publication bias (0=none, 1=weak, 2=strong)")
    parser.add_argument("--selection", type=int, default=config.initial_selection_condition, help="Selection strategy (0=truth, 1=novelty)")
    parser.add_argument("--max_replications", type=int, default=None, help="Max replications per effect (default: unlimited)")
    parser.add_argument("--replication_journal", type=int, default=int(config.replication_journal), help="Include replication journal (1=Yes, 0=No)")
    
    # Output
    parser.add_argument("--output", type=str, default="simulation_output", help="Prefix for output CSV files")
    
    # Visualization
    parser.add_argument("--visualize", action="store_true", help="Enable real-time visualization")
    
    args = parser.parse_args()
    
    # Update config
    config.number_of_researchers = args.researchers
    config.number_of_effects = args.effects
    config.timesteps_max = args.timesteps
    config.timesteps_per_career_step = args.career_steps
    config.publication_bias = PublicationBias(args.bias)
    config.initial_selection_condition = SelectionStrategy(args.selection)
    if args.max_replications is not None:
        config.max_replications_per_effect = args.max_replications
    config.replication_journal = bool(args.replication_journal)
    
    print("="*40)
    print("SCIENTIFIC COMMUNITY SIMULATION")
    print("="*40)
    print(f"Configuration:")
    print(f"  Researchers:      {config.number_of_researchers}")
    print(f"  Effects:          {config.number_of_effects}")
    print(f"  Max Timesteps:    {config.timesteps_max}")
    print(f"  Publication Bias: {config.publication_bias.name.title()}")
    print(f"  Selection Strat:  {config.initial_selection_condition.name.title()}")
    print(f"  Selection Strat:  {config.initial_selection_condition.name.title()}")
    print(f"  Max Replications: {config.max_replications_per_effect}")
    print(f"  Repl. Journal:    {config.replication_journal}")
    print(f"  Output Prefix:    {args.output}")
    print(f"  Visualization:    {args.visualize}")
    print("-" * 40)
    
    # Initialize Visualizer if requested
    viz = None
    if args.visualize:
        from simulation.visualization import Visualizer
        viz = Visualizer()
    
    print("Initializing simulation...")
    sim = Simulation()
    print("Starting run...")
    
    # Pass callback if visualizer exists
    callback = viz.update if viz else None
    sim.run(on_step_callback=callback)
    
    if viz:
        viz.close()
    
    print("Saving statistics...")
    
    # Ensure output directory exists
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to output directory
    output_path = os.path.join(output_dir, args.output)
    sim.stats.save(output_path)
    print(f"Data saved to {output_path}_steps.csv and {output_path}_studies.csv")
    
    print("Simulation complete.")

if __name__ == "__main__":
    main()

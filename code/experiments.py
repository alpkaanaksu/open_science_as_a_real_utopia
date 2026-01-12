import subprocess
import os
import sys
import argparse

# Define your experiments here (add/remove lines as needed)
# Format: {"name": "experiment_name", "flags": "flags_string"}
experiments = [
    {
        "name": "baseline",
        "flags": "--selection=0 --bias=1 --replication_journal=0 --effects=10000  --visualize"
    },
    {
        "name": "limit_replications",
        "flags": "--selection=0 --bias=1 --max_replications=2 --replication_journal=0 --effects=10000  --visualize"
    },
    {
        "name": "replication_journal",
        "flags": "--selection=0 --bias=1 --replication_journal=1 --effects=10000  --visualize"
    },
    {
        "name": "replication_journal_with_limits",
        "flags": "--selection=0 --bias=1 --max_replications=2 --replication_journal=1 --effects=10000  --visualize"
    }
]

def run_experiments():
    parser = argparse.ArgumentParser(description="Run batch simulation experiments.")
    parser.add_argument("--output", type=str, default="experiments_output", help="Base directory for experiment outputs")
    args = parser.parse_args()
    
    base_output_dir = args.output
    
    # Ensure base output directory exists
    os.makedirs(base_output_dir, exist_ok=True)
    
    print(f"Found {len(experiments)} experiments to run.")
    print(f"Output directory: {base_output_dir}")
    
    for i, exp in enumerate(experiments):
        exp_name = exp.get("name", f"experiment_{i+1}")
        flags = exp.get("flags", "")
        
        # Create subfolder for this experiment
        exp_subdir = os.path.join(base_output_dir, exp_name)
        os.makedirs(exp_subdir, exist_ok=True)
        
        print(f"\n[{i+1}/{len(experiments)}] Running Experiment: {exp_name}")
        print(f"   -> Saving to {exp_subdir}")
        
        # specific output filenames within the subfolder
        plot_filename = os.path.join(exp_subdir, "plot.png")
        data_prefix = os.path.join(exp_subdir, "data") # resulting in data_steps.csv, etc.
        
        # Construct command
        # Always add visualize params
        cmd = [sys.executable, "main.py"] + flags.split() + [
            "--visualize",
            "--no_show",
            f"--save_plot={plot_filename}",
            f"--output={data_prefix}"
        ]
        
        try:
            # Run the command
            subprocess.run(cmd, check=True)
            print(f"✅ Experiment '{exp_name}' completed.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Experiment '{exp_name}' failed with exit code {e.returncode}")
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user.")
            break

if __name__ == "__main__":
    run_experiments()

# Academia in Silico

An agent-based model (ABM) of the scientific community, designed to simulate the production, verification (replication), and selection of scientific knowledge. This project explores how institutional incentives (selection for novelty vs. truth) and publication biases affect the reliability of the scientific record.

## Project Structure

- **`code/`**: Contains the Python source code for the simulation.
    - `main.py`: The primary entry point for running single simulations.
    - `experiments.py`: A script for running batch experiments with custom configurations.
    - `simulation/`: The core logic package (agents, environment, peer review).
- **`text/`**: Contains the Quarto source files for the accompanying thesis.
    - `text.qmd`: The main manuscript.

## Installation

The simulation requires Python 3. It depends on `scipy` for statistical distributions and `matplotlib` for visualization.

It is recommended to use the provided virtual environment or create a new one:

```bash
cd code
python3 -m venv venv
source venv/bin/activate
pip install scipy matplotlib
```

## Running the Simulation

You can run a single simulation instance using `main.py`. This is useful for testing specific parameters or watching the system evolve in real-time.

```bash
cd code
# Run via the virtual environment
./venv/bin/python main.py --visualize
```

### Key Configuration Flags

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--researchers` | Number of active agents | `500` |
| `--effects` | Number of discoverable effects | `100000` |
| `--timesteps` | Duration of simulation | `300` |
| `--selection` | Selection Pressure (`0`=Truth, `1`=Novelty) | `1` |
| `--bias` | Publication Bias (`0`=None, `1`=Weak, `2`=Strong) | `1` |
| `--replication_journal` | Enable specialized replication journal (`0`=No, `1`=Yes) | `1` |
| `--max_replications` | Hard limit on replications per effect | `None` |
| `--visualize` | Enable real-time dashboard | `False` |

**Example:**
Run a "Truth-Seeking" community with no publication bias for 500 steps:
```bash
./venv/bin/python main.py --selection=0 --bias=0 --timesteps=500 --visualize
```

## Running Experiments

To run multiple conditions consecutively (e.g., to reproduce the results in the paper), use `experiments.py`.

1.  Open `code/experiments.py` and define your experiments in the `experiments` list:
    ```python
    experiments = [
        {
            "name": "baseline_novelty",
            "flags": "--selection=1 --bias=1 --timesteps=300"
        },
        {
            "name": "intervention_truth",
            "flags": "--selection=0 --bias=1 --timesteps=300"
        }
    ]
    ```
2.  Run the script:

    ```bash
    ./venv/bin/python experiments.py --output=my_results
    ```

Results (CSV data and plot images) will be saved in subdirectories under `my_results/` (e.g., `my_results/baseline_novelty/`).

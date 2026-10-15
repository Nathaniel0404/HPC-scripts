
from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = BASE_DIR / "experiments"
BUILDS_DIR = BASE_DIR / "builds"

ACCOUNT = "tc079-brunels"
QOS = "short"
PARTITION = "standard"

# Gets a unique experiment id
def get_next_experiment_id():
    existing = []

    for path in EXPERIMENTS_DIR.glob("exp_*"):
        if path.is_dir():
            try:
                number = int(path.name.split("_")[1])
                existing.append(number)
            except ValueError:
                pass

    next_number = max(existing, default=0) + 1
    return f"exp_{next_number:03d}"

# Generate a new run directory for each experiment
def create_new_experiment_dir():
    exp_id_str = get_next_experiment_id()
    exp_dir = EXPERIMENTS_DIR /exp_id_str
    exp_dir.mkdir(parents=True, exist_ok=False)

    return exp_dir

# Generate a hpcg.dat file in the corresponding experiment dir
def write_hpcg_dat(local_n, run_time, exp_dir_path):
    content = f"""HPCG benchmark input file
Sandia National Laboratories; University of Tennessee, Knoxville
{local_n} {local_n} {local_n}
{run_time}
"""
    hpcg_dat_path = exp_dir_path / "hpcg.dat"
    with open(hpcg_dat_path, "w") as f:
        f.write(content)

# Generates a slurm script to run experiment
def write_slurm_script(nodes, n_tasks_per_node, n_threads_per_task, time_limit, build_id, exp_dir_path):
    slurm_path = exp_dir_path / "run_hpcg.slurm"
    xhpcg_path = BUILDS_DIR / build_id / "xhpcg"

    if not xhpcg_path.is_file():
        raise FileNotFoundError(f"Build executable not found: {xhpcg_path}")
    
    content = f"""#!/bin/bash
#SBATCH --job-name=hpcg_auto
#SBATCH --output=hpcg_%j.out
#SBATCH --time={time_limit}
#SBATCH --nodes={nodes}
#SBATCH --ntasks-per-node={n_tasks_per_node}
#SBATCH --cpus-per-task={n_threads_per_task}
#SBATCH --account={ACCOUNT}
#SBATCH --qos={QOS}
#SBATCH --exclusive
#SBATCH --partition={PARTITION}
module restore

export OMP_NUM_THREADS={n_threads_per_task}
cd $SLURM_SUBMIT_DIR
srun {xhpcg_path}
"""
    with open(slurm_path, "w") as f:
        f.write(content)

def write_config(exp, exp_dir_path):
    config_path = exp_dir_path / "config.json"

    with open(config_path, "x") as f:
        json.dump(exp, f, indent=4)


# ==================== MAIN EXECUTION LOOP ====================
if __name__ == "__main__":
    experiments = [
        {"nodes": 1, "ntasks": 288, "nthreads": 1,  "local_n": 104, "time": "00:05:00", "run_time": 60, "build_id": "build_001_gcc_O3"},

    ]

    for exp in experiments:
        exp_path = create_new_experiment_dir()
        write_hpcg_dat(exp["local_n"], exp["run_time"], exp_path)
        write_slurm_script(exp["nodes"], exp["ntasks"], exp["nthreads"], exp["time"], exp["build_id"], exp_path)
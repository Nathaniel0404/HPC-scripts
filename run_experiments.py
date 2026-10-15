from pathlib import Path
import subprocess
import time

BASE_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = BASE_DIR / "experiments"

def submit_experiment(exp_dir):
    result = subprocess.run(
        ["sbatch", "run_hpcg.slurm"],
        cwd=exp_dir,
        capture_output=True,
        text=True,
        check=True
    )

    job_id = result.stdout.strip().split()[-1]

    return job_id

def wait_for_job(job_id):
    while True:
        result = subprocess.run(
            ["squeue", "-j", job_id],
            capture_output=True,
            text=True,
            check=True
        )

        if job_id not in result.stdout:
            break

        time.sleep(10)

def get_job_accounting(job_id):
    result = subprocess.run(
        [
            "sacct",
            "-j", job_id,
            "--format=JobID,State,ExitCode,Elapsed,ConsumedEnergy",
            "-P"
        ],
        capture_output=True,
        text=True,
        check=True
    )

    return result.stdout

def save_accounting(exp_dir, accounting_output):
    path = exp_dir / "sacct.txt"

    with open(path, "x") as f:
        f.write(accounting_output)

def save_job_id(exp_dir, job_id):
    with open(exp_dir / "job_id.txt", "x") as f:
        f.write(job_id + "\n")

def get_pending_experiments():
    experiments = []

    for path in EXPERIMENTS_DIR.glob("exp_*"):
        if not path.is_dir():
            continue

        if (path / "job_id.txt").exists():
            continue

        experiments.append(path)

    return sorted(experiments)

if __name__ == "__main__":
    experiments = get_pending_experiments()

    for exp_dir in experiments:
        print(f"Running {exp_dir.name}")

        job_id = submit_experiment(exp_dir)
        print(f"Submitted job {job_id}")

        save_job_id(exp_dir, job_id)

        wait_for_job(job_id)

        accounting = get_job_accounting(job_id)
        save_accounting(exp_dir, accounting)

        print(f"Finished {exp_dir.name}")
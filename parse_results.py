from pathlib import Path
import json
import csv

BASE_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = BASE_DIR / "experiments"
RESULTS_DIR = BASE_DIR / "results"

RESULTS_FILE = RESULTS_DIR / "results.csv"

def read_config(exp_dir):
    config_path = exp_dir / "config.json"

    with open(config_path, "r") as f:
        return json.load(f)

def find_hpcg_result(exp_dir):
    files = list(exp_dir.glob("HPCG-Benchmark*.txt"))

    if len(files) == 0:
        return None

    if len(files) > 1:
        raise RuntimeError(
            f"Multiple HPCG result files found in {exp_dir}"
        )

    return files[0]

def parse_hpcg_result(result_path):
    validated = False
    gflops_per_s = None
    global_x = None
    global_y = None
    global_z = None

    with open(result_path, "r") as f:
        for line in f:
            line = line.strip()

            if "HPCG result is VALID" in line:
                validated = True

            if (
                "GFLOP/s Summary::Total with convergence "
                "and optimization phase overhead"
                in line
            ):
                try:
                    gflops_per_s = float(line.split("=")[1].strip())
                except (IndexError, ValueError):
                    pass

            if "Global Problem Dimensions::Global nx=" in line:
                global_x = int(line.split("=")[1].strip())

            elif "Global Problem Dimensions::Global ny=" in line:
                global_y = int(line.split("=")[1].strip())

            elif "Global Problem Dimensions::Global nz=" in line:
                global_z = int(line.split("=")[1].strip())

    return {
        "validated": validated,
        "gflops_per_s": gflops_per_s,
        "global_x": global_x,
        "global_y": global_y,
        "global_z": global_z
    }

def parse_sacct(exp_dir):
    job_id_path = exp_dir / "job_id.txt"
    sacct_path = exp_dir / "sacct.txt"

    with open(job_id_path, "r") as f:
        job_id = f.read().strip()

    with open(sacct_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        parts = line.split("|")

        if parts[0] != job_id:
            continue

        return {
            "job_id": parts[0],
            "state": parts[1],
            "exit_code": parts[2],
            "elapsed": parts[3],
            "energy": parts[4]
        }

    return None

def parse_energy(raw_energy):
    if not raw_energy:
        return None

    if raw_energy.endswith("K"):
        return float(raw_energy[:-1]) * 1_000

    if raw_energy.endswith("M"):
        return float(raw_energy[:-1]) * 1_000_000

    return float(raw_energy)

def elapsed_to_seconds(elapsed):
    parts = elapsed.split(":")

    if len(parts) != 3:
        return None

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])

    return hours * 3600 + minutes * 60 + seconds

def parse_experiment(exp_dir):
    config = read_config(exp_dir)

    hpcg_file = find_hpcg_result(exp_dir)

    if hpcg_file is None:
        hpcg = {
            "validated": False,
            "gflops_per_s": None,
            "global_x": None,
            "global_y": None,
            "global_z": None
        }
    else:
        hpcg = parse_hpcg_result(hpcg_file)

    sacct = parse_sacct(exp_dir)

    energy_joules = None
    elapsed_seconds = None
    gflops_per_watt = None

    if sacct is not None:
        energy_joules = parse_energy(sacct["energy"])
        elapsed_seconds = elapsed_to_seconds(
            sacct["elapsed"]
        )

    if (
        energy_joules is not None
        and elapsed_seconds is not None
        and energy_joules > 0
        and hpcg["gflops_per_s"] is not None
    ):
        average_watts = (
            energy_joules / elapsed_seconds
        )

        gflops_per_watt = (
            hpcg["gflops_per_s"] / average_watts
        )

    return {
        "experiment_id": exp_dir.name,
        "build_id": config["build_id"],
        "nodes": config["nodes"],
        "tasks_per_node": config["ntasks"],
        "threads_per_task": config["nthreads"],
        "local_n": config["local_n"],
        "global_x": hpcg["global_x"],
        "global_y": hpcg["global_y"],
        "global_z": hpcg["global_z"],
        "global_grid_points": (
            hpcg["global_x"] * hpcg["global_y"] * hpcg["global_z"]
            if all(hpcg[k] is not None for k in ("global_x", "global_y", "global_z"))
            else None
        ),
        "run_time": config["run_time"],

        "job_id": sacct["job_id"] if sacct else None,
        "job_state": sacct["state"] if sacct else None,
        "exit_code": sacct["exit_code"] if sacct else None,

        "validated": hpcg["validated"],
        "gflops_per_s": hpcg["gflops_per_s"],

        "elapsed_seconds": elapsed_seconds,
        "energy_joules": energy_joules,
        "gflops_per_watt": gflops_per_watt
    }

def write_results(results):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not results:
        return

    fieldnames = results[0].keys()

    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    results = []

    for exp_dir in sorted(
        EXPERIMENTS_DIR.glob("exp_*")
    ):
        if not exp_dir.is_dir():
            continue

        try:
            result = parse_experiment(exp_dir)
            results.append(result)

        except Exception as e:
            print(
                f"Failed to parse {exp_dir.name}: {e}"
            )

    write_results(results)

    print(
        f"Wrote {len(results)} experiments "
        f"to {RESULTS_FILE}"
    )
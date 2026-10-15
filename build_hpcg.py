from pathlib import Path
import subprocess
import shutil
import json


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

HPCG_SRC_DIR = PROJECT_DIR / "hpcg"
BUILDS_DIR = BASE_DIR / "builds"

MAKE_FILE = HPCG_SRC_DIR / "setup" / "Make.Cirrus"


def get_next_build_id(compiler, opt_name):
    existing = []

    for path in BUILDS_DIR.glob("build_*"):
        if path.is_dir():
            try:
                number = int(path.name.split("_")[1])
                existing.append(number)
            except (ValueError, IndexError):
                pass

    next_number = max(existing, default=0) + 1

    return f"build_{next_number:03d}_{compiler}_{opt_name}"


def create_build_dir(build_id):
    build_dir = BUILDS_DIR / build_id
    build_dir.mkdir(parents=True, exist_ok=False)

    return build_dir


def update_make_cirrus(compiler_flags):
    """
    Updates only the CXXFLAGS line in Make.Cirrus.
    """

    with open(MAKE_FILE, "r") as f:
        lines = f.readlines()

    with open(MAKE_FILE, "w") as f:
        for line in lines:
            if line.startswith("CXXFLAGS"):
                f.write(
                    f"CXXFLAGS = $(HPCG_DEFS) {compiler_flags} -fopenmp\n"
                )
            else:
                f.write(line)


def compile_hpcg():
    subprocess.run(
        ["make", "clean"],
        cwd=HPCG_SRC_DIR,
        check=True
    )

    subprocess.run(
        ["make", "arch=Cirrus"],
        cwd=HPCG_SRC_DIR,
        check=True
    )


def copy_binary(build_dir):
    source = HPCG_SRC_DIR / "bin" / "xhpcg"
    destination = build_dir / "xhpcg"

    if not source.is_file():
        raise FileNotFoundError(
            f"Compiled xhpcg not found at {source}"
        )

    shutil.copy2(source, destination)


def write_build_config(build, build_id, build_dir):
    config = {
        "build_id": build_id,
        "compiler": build["compiler"],
        "compiler_flags": build["compiler_flags"]
    }

    config_path = build_dir / "build_config.json"

    with open(config_path, "x") as f:
        json.dump(config, f, indent=4)


if __name__ == "__main__":

    builds = [
        {
            "compiler": "gcc",
            "opt_name": "O3",
            "compiler_flags": "-O3"
        }
    ]

    for build in builds:

        build_id = get_next_build_id(
            build["compiler"],
            build["opt_name"]
        )

        print(f"Creating {build_id}")

        build_dir = create_build_dir(build_id)

        update_make_cirrus(build["compiler_flags"])

        compile_hpcg()

        copy_binary(build_dir)

        write_build_config(
            build,
            build_id,
            build_dir
        )

        print(f"Created build: {build_dir}")
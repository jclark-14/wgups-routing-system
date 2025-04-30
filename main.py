# WGUPS Routing Program | Student_ID: 012501128

import sys
from wgups.cli import run_program
from wgups.optimizer_core import NN2OptOptimizer

def main():
    """
    Entry point for the WGUPS package delivery system.

    - Supports optional command-line arguments:
        --single-run      → Run a one-shot simulation (no planning)
        --n=<int>         → Number of iterations for planning phase (default: 20)

    Uses NN2OptOptimizer as the delivery route strategy.
    """
    single_run = "--single-run" in sys.argv
    iterations = 20

    # Optional override for iteration count -> --n=50
    for arg in sys.argv:
        if arg.startswith("--n="):
            try:
                iterations = int(arg.split("=")[1])
            except ValueError:
                pass  # fallback to default

    optimizer = NN2OptOptimizer()
    run_program(optimizer, single_run, iterations)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        print("Please check your input files and try again.")
        sys.exit(1)

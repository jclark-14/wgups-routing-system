# WGUPS Routing Program Student_ID: 012501128

import sys
from wgups.cli import run_program
from wgups.optimizer_core import NN2OptOptimizer

def main():
    """
    Entry point for WGUPS package delivery system.
    Parses command line arguments and initializes the program.
    """
    # Parse command line arguments
    single_run = "--single-run" in sys.argv
    iterations = 20  # Default iterations for planning approach
    
    # Check if specific iteration count was provided
    for arg in sys.argv:
        if arg.startswith("--n="):
            try:
                iterations = int(arg.split("=")[1])
            except ValueError:
                pass
    
    # Initialize optimizer
    optimizer = NN2OptOptimizer()
    
    # Run the program with the selected configuration
    run_program(optimizer, single_run, iterations)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error during execution: {e}")
        print("Please check your input files and try again.")
        sys.exit(1)
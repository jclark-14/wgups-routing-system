# WGUPS Routing Program STUDENT_ID: 

import sys
from wgups.simulation import run_simulation, run_simulation_with_planning, constraints_satisfied
from wgups.optimizers import NN2OptOptimizer
from wgups.reporting import run_cli

if __name__ == "__main__":
    # Print welcome message
    print("="*80)
    print(f"{'WGUPS PACKAGE DELIVERY SYSTEM':^80}")
    print("="*80)
    
    try:
        # Use the Enhanced optimization algorithm
        optimizer = NN2OptOptimizer()
        
        # Check for command line arguments
        if "--single-run" in sys.argv:
            # Run standard single simulation
            print("Initializing simulation with Enhanced Optimization algorithm...")
            packages, trucks = run_simulation(optimizer)
            
            print("\nSimulation completed successfully!")
            print("Starting interactive command-line interface...")
            run_cli(packages, trucks)
        else:
            # Default: Use the planning approach with 20 iterations
            n = 20  
            # Check if a specific N was provided
            for arg in sys.argv:
                if arg.startswith("--n="):
                    try:
                        n = int(arg.split("=")[1])
                    except ValueError:
                        pass
            
            packages, trucks = run_simulation_with_planning(optimizer, n)
            
            print("\nSimulation completed with optimal result!")
            print("Starting interactive command-line interface...")
            run_cli(packages, trucks)
    
    except Exception as e:
        print(f"Error during simulation: {e}")
        print("Please check your input files and try again.")
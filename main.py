# WGUPS Routing Program - Student ID: 

from wgups.simulation import run_simulation
from wgups.optimizers import NN2OptOptimizer
from wgups.reporting import run_cli

if __name__ == "__main__":
    # Print welcome message
    print("="*80)
    print(f"{'WGUPS PACKAGE DELIVERY SYSTEM':^80}")
    print("="*80)
    print("Initializing simulation with Enhanced Optimization algorithm...")
    
    try:
        # Use the Enhanced optimization algorithm
        optimizer = NN2OptOptimizer()
        
        # Run the simulation and get package and truck objects
        packages, trucks = run_simulation(optimizer)
        
        print("\nSimulation completed successfully!")
        print("Starting interactive command-line interface...")
        
        # # Start the CLI interface with the simulation results
        # run_cli(packages, trucks)
        
    except Exception as e:
        print(f"Error during simulation: {e}")
        print("Please check your input files and try again.")
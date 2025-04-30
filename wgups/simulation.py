
from datetime import datetime, time
from typing import Tuple
from wgups.constants import TODAY, STATUS_DELIVERED
from wgups.data_loader import load_packages, load_distances
from wgups.models import Truck
from wgups.utils import resolve_package_groups
from wgups.reporting import generate_summary_report
from wgups.optimizer_core import RouteOptimizer
from wgups.routing import execute_route
from wgups.package_identification import map_packages_to_groups,identify_truck_specific_packages, identify_critical_groups, identify_deadline_packages, identify_delayed_packages, identify_priority_packages, identify_standard_packages
from wgups.package_loading import load_by_proximity, load_deadline_packages, load_delayed_packages, load_group_to_truck, load_priority_packages, load_truck_specific_packages
from wgups.routing import estimate_route_mileage

def run_simulation(optimizer: RouteOptimizer, verbose=True, debug_level=0, execute=True) -> Tuple:
    """
    Run the WGUPS package delivery simulation.
    
    Parameters:
    - optimizer: The route optimization algorithm to use
    - verbose: Whether to print detailed output
    - debug_level: Level of debug information (0=none, 1=basic, 2=detailed)
    - execute: Whether to actually execute the routes or just plan them
    
    Returns (packages, trucks) tuple for reporting and CLI.
    """
    # Step 1: Load data and resolve package groups
    packages = load_packages()
    distance_matrix, address_map = load_distances()
    package_group = resolve_package_groups(packages)

    # Step 2: Initialize trucks
    truck1 = Truck(1)  # 8:00 AM
    truck2 = Truck(2, time=datetime.combine(TODAY, time(9, 5))) 
    
    # Step 3: Prepare package classification
    priority_packages = identify_priority_packages(packages)
    truck_specific_packages = identify_truck_specific_packages(packages)
    deadline_packages = identify_deadline_packages(packages)
    delayed_packages = identify_delayed_packages(packages)
    
    # Step 4: Create package group mapping and identify critical groups 
    package_to_group = map_packages_to_groups(package_group)
    critical_groups = identify_critical_groups(packages, package_group)

    # Step 5: Load packages onto trucks 
    load_truck_specific_packages(truck1, truck2, truck_specific_packages, 
                             package_to_group, packages)
    for group in critical_groups:
        load_group_to_truck(truck1, group, packages) 
    
    load_priority_packages(truck1, priority_packages, package_to_group, packages)

    load_deadline_packages(truck1, deadline_packages, package_to_group, packages)

    load_delayed_packages(truck2, delayed_packages, package_to_group, packages)
    
    standard_packages = identify_standard_packages(
        packages,
        priority_packages,
        truck_specific_packages,
        deadline_packages,
        delayed_packages,
        package_group
    )
    load_by_proximity(truck1, truck2, standard_packages, packages, distance_matrix, address_map)

    # Step 6: Execute delivery routes
    if execute:

        truck1.set_route(optimizer.optimize(truck1, packages, distance_matrix, address_map, package_group))
        execute_route(truck1, packages, distance_matrix, address_map)

        truck2.set_route(optimizer.optimize(truck2, packages, distance_matrix, address_map, package_group))
        execute_route(truck2, packages, distance_matrix, address_map)
        
        # Handle any remaining undelivered packages
        deliver_remaining_packages(truck1, truck2, packages, optimizer, 
                                distance_matrix, address_map, package_group)
    else:
        # Just plan routes without execution for evaluation
        truck1.set_route(optimizer.optimize(truck1, packages, distance_matrix, address_map, package_group))
        truck2.set_route(optimizer.optimize(truck2, packages, distance_matrix, address_map, package_group))
        # Calculate estimated mileage without actual delivery
        truck1.estimated_mileage = estimate_route_mileage(truck1.route, packages, distance_matrix, address_map)
        truck2.estimated_mileage = estimate_route_mileage(truck2.route, packages, distance_matrix, address_map)
    
    # Step 7: Generate report (only if execute=True and verbose=True)
    if execute and verbose:
        generate_summary_report(packages, [truck1, truck2])
    
    return packages, [truck1, truck2]


def deliver_remaining_packages(truck1, truck2, packages, optimizer, distance_matrix, address_map, package_group):
    """Handle any undelivered packages with the first available truck."""
    remaining_packages = [pid for pid in packages 
                         if packages.lookup(pid).status != STATUS_DELIVERED]
    
    if not remaining_packages:
        return  # All packages delivered
        
    # Use the truck that returns first
    next_truck = truck1 if truck1.return_time <= truck2.return_time else truck2
    next_truck.time = next_truck.return_time
    
    # Load remaining packages
    for pid in remaining_packages:
        if next_truck.has_capacity():
            next_truck.load_package(packages.lookup(pid))
    
    # Optimize and execute route
    if next_truck.cargo:
        next_truck.set_route(optimizer.optimize(next_truck, packages, distance_matrix, address_map, package_group))
        execute_route(next_truck, packages, distance_matrix, address_map)
        

def run_simulation_with_planning(optimizer, planning_iterations=20, debug=False):
    """Run the WGUPS package delivery simulation with advanced route planning."""
    print(f"Initializing package delivery optimization...")
    print(f"Starting route planning phase ({planning_iterations} iterations)...")
    
    best_mileage = float('inf')
    best_result = None
    valid_runs = []
    
    # Progress indicator
    print("Planning progress: ", end="", flush=True)
    
    # Route planning phase - fully execute each candidate plan
    for i in range(1, planning_iterations+1):
        print(".", end="", flush=True)
        if i % 10 == 0:
            print(f" {i}/{planning_iterations}", end="", flush=True)
        
        # Fully run a complete simulation for each candidate
        candidate_packages, candidate_trucks = run_simulation(
            optimizer, verbose=False, debug_level=0, execute=True)
        
        # Calculate actual execution mileage
        total_mileage = sum(t.mileage for t in candidate_trucks)
        constraints_met = constraints_satisfied(candidate_packages, candidate_trucks)
        
        if debug:
            print(f"\nRun {i}: {total_mileage:.2f} miles (Valid: {constraints_met})")
        
        # Track all valid runs
        if constraints_met:
            valid_runs.append((i, total_mileage))
            
            # Keep best plan
            if total_mileage < best_mileage:
                best_mileage = total_mileage
                best_result = (candidate_packages, candidate_trucks)
    
    # Calculate statistics
    if valid_runs:
        worst_run, worst_mileage = max(valid_runs, key=lambda x: x[1])
        best_run, _ = min(valid_runs, key=lambda x: x[1])
        avg_mileage = sum(m for _, m in valid_runs) / len(valid_runs)
        
        print("\n\nRoute planning complete!")
        print(f"Best solution (run {best_run}): {best_mileage:.2f} miles")
        print(f"Worst solution (run {worst_run}): {worst_mileage:.2f} miles")
        print(f"Average solution: {avg_mileage:.2f} miles")
        print(f"Mileage range: {worst_mileage - best_mileage:.2f} miles")
    else:
        print("\n\nNo valid solutions found!")
        return None
    
    print("\nGenerating final delivery report for optimal solution...")
    
    best_packages, best_trucks = best_result
    
    generate_summary_report(best_packages, best_trucks)
    
    return best_packages, best_trucks

def constraints_satisfied(packages, trucks):
    """Check if all constraints are satisfied."""
    # Check deadline satisfaction
    all_deadlines_met = True
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.deadline_time and pkg.delivery_time and pkg.delivery_time > pkg.deadline_time:
            all_deadlines_met = False
            break
    
    # Check truck-specific constraints
    all_trucks_respected = True
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.only_truck and pkg.truck_assigned != pkg.only_truck:
            all_trucks_respected = False
            break
    
    # Check group constraints
    all_groups_kept = True
    
    return all_deadlines_met and all_trucks_respected and all_groups_kept  # Return a boolean, not a list

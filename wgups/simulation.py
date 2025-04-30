import copy
from datetime import datetime, time
from typing import Tuple, List, Dict, Set
from wgups.constants import TODAY, STATUS_DELIVERED, START_TIME, EARLY_DEADLINE_CUTOFF, STATUS_AT_HUB
from wgups.data_loader import load_packages, load_distances
from wgups.models import Truck
from wgups.utils import resolve_package_groups, get_distance
from wgups.reporting import generate_summary_report
from wgups.optimizers import RouteOptimizer
from wgups.routing import execute_route

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
    
    if debug_level > 0:
        print("Loading packages and distances...")
    # Step 1: Load data and resolve package groups
    packages = load_packages()
    distance_matrix, address_map = load_distances()
    package_group = resolve_package_groups(packages)

    if debug_level > 0:
        print("Initializing trucks...")
    # Step 2: Initialize trucks
    truck1 = Truck(1)  # 8:00 AM
    truck2 = Truck(2, time=datetime.combine(TODAY, time(9, 5))) 
    

    if debug_level > 0:
        print("Classifying packages...")
    # Step 3: Prepare package classification
    priority_packages = identify_priority_packages(packages)
    truck_specific_packages = identify_truck_specific_packages(packages)
    deadline_packages = identify_deadline_packages(packages)
    delayed_packages = identify_delayed_packages(packages)
    
    if debug_level > 0:
        print("group mapping and critical groups...")
    # Step 4: Create package group mapping and identify critical groups 
    package_to_group = map_packages_to_groups(package_group)
    critical_groups = identify_critical_groups(packages, package_group)
    
    if debug_level > 0:
        print("loading trucks...")
    # Step 5: Load packages onto trucks - IMPROVED LOADING STRATEGY
    # First load truck-specific packages
    load_truck_specific_packages(truck1, truck2, truck_specific_packages, 
                               package_to_group, packages)
    # Then load critical groups (groups with deadline packages) to truck 1
    for group in critical_groups:
        load_group_to_truck(truck1, group, packages) 
    
    # Load priority packages that aren't part of critical groups
    load_priority_packages(truck1, priority_packages, package_to_group, packages)

    # Then load other deadline packages
    load_deadline_packages(truck1, deadline_packages, package_to_group, packages)

    # Load delayed packages to truck 2
    load_delayed_packages(truck2, delayed_packages, package_to_group, packages)
    
    # Balance remaining packages
    standard_packages = identify_standard_packages(
        packages,
        priority_packages,
        truck_specific_packages,
        deadline_packages,
        delayed_packages,
        package_group
    )
    load_by_proximity(truck1, truck2, standard_packages, packages, distance_matrix, address_map)

    if debug_level > 0:
        print("execute run...")
    # Step 6: Execute delivery routes (conditionally)
    if execute:
        # Execute truck1 route
        truck1.set_route(optimizer.optimize(truck1, packages, distance_matrix, address_map, package_group))
        execute_route(truck1, packages, distance_matrix, address_map)

        # Execute truck2 route
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

def identify_priority_packages(packages) -> List[int]:
    """Identify packages that need special priority (critical deadlines)."""
    # Anything with a deadline at or before EARLY_DEADLINE_CUTOFF (9:15 AM)
    urgent = []
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.deadline_time and pkg.deadline_time.time() <= EARLY_DEADLINE_CUTOFF:
            urgent.append(pid)
    return urgent

def identify_truck_specific_packages(packages) -> Dict[int, List[int]]:
    """Identify packages that must be on specific trucks."""
    truck_specific = {1: [], 2: []}
    
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.only_truck in [1, 2]:
            truck_specific[pkg.only_truck].append(pid)
            
    return truck_specific

def identify_deadline_packages(packages) -> List[int]:
    """Identify packages with early deadlines."""
    deadline_pkgs = []
    
    for pid in packages:
        pkg = packages.lookup(pid)
        if (pkg.deadline_time and 
            pkg.deadline_time.time() <= time(10, 30) and
            pkg.available_time == START_TIME and
            not pkg.only_truck):
            deadline_pkgs.append(pid)
            
    return deadline_pkgs

def identify_delayed_packages(packages) -> List[int]:
    """Identify packages with delayed availability."""
    delayed_pkgs = []
    
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.available_time > START_TIME:
            delayed_pkgs.append(pid)
            
    return delayed_pkgs

def identify_standard_packages(packages, priority_pkgs, truck_specific_pkgs, 
                             deadline_pkgs, delayed_pkgs,
                             package_groups) -> List[int]:
    """Identify packages with no special constraints."""
    standard_pkgs = []
    
    # Create a set of all constrained packages *plus* every grouped package
    constrained = set(priority_pkgs)
    constrained.update(truck_specific_pkgs[1])
    constrained.update(truck_specific_pkgs[2])
    constrained.update(deadline_pkgs)
    constrained.update(delayed_pkgs)
    # Exclude any package that belongs to *any* group
    for group in package_groups:
        constrained.update(group)
    
    # Add packages not in constrained set
    for pid in packages:
        if pid not in constrained:
            standard_pkgs.append(pid)
            
    return standard_pkgs

def map_packages_to_groups(package_group) -> Dict[int, int]:
    """Create mapping from package ID to its group ID."""
    package_to_group = {}
    
    for group in package_group:
        group_id = min(group)  # Use smallest ID as group identifier
        for pid in group:
            package_to_group[pid] = group_id
    
    return package_to_group

def identify_critical_groups(packages, package_groups) -> List[Set[int]]:
    """Identify package groups with deadline packages."""
    critical_groups = []
    
    for group in package_groups:
        # Count packages with deadlines in this group
        deadline_count = sum(1 for pid in group 
                           if packages.lookup(pid) and 
                           packages.lookup(pid).deadline_time)
        
        # If this group has deadline packages, consider it critical
        if deadline_count > 0:
            critical_groups.append(group)
            
    return critical_groups

def load_group_to_truck(truck, group, packages, verbose=True):
    # Only load if truck has enough capacity
    if len(truck.cargo) + len(group) <= truck.capacity:
        for pid in group:
            if pid not in truck.cargo:
                pkg = packages.lookup(pid)
                if pkg:
                    truck.load_package(pkg)

def load_truck_specific_packages(truck1, truck2, truck_specific_pkgs, 
                               package_to_group, packages):
    """Load packages that must go on specific trucks."""
    # Load truck 1 specific packages
    for pid in truck_specific_pkgs[1]:
        if pid in package_to_group:
            # Load entire group
            group_id = package_to_group[pid]
            group_members = [p for p in packages if p in package_to_group 
                            and package_to_group[p] == group_id]
            load_group_to_truck(truck1, group_members, packages)
        else:
            if truck1.has_capacity():
                truck1.load_package(packages.lookup(pid))
    
    # Load truck 2 specific packages
    for pid in truck_specific_pkgs[2]:
        if pid in package_to_group:
            # Load entire group
            group_id = package_to_group[pid]
            group_members = [p for p in packages if p in package_to_group 
                            and package_to_group[p] == group_id]
            load_group_to_truck(truck2, group_members, packages)
        else:
            if truck2.has_capacity():
                truck2.load_package(packages.lookup(pid))

def load_priority_packages(truck, priority_pkgs, package_to_group, packages):
    """Load high-priority packages onto truck."""
    for pid in priority_pkgs:
        if pid in truck.cargo:
            continue  # Already loaded
            
        if truck.has_capacity():
            if pid in package_to_group:
                # Load entire group if possible
                group_id = package_to_group[pid]
                group_members = [p for p in packages if p in package_to_group 
                               and package_to_group[p] == group_id]
                
                if len(truck.cargo) + len(group_members) <= truck.capacity:
                    load_group_to_truck(truck, group_members, packages)
                else:
                    # If can't fit group, try just the priority package
                    truck.load_package(packages.lookup(pid))
            else:
                truck.load_package(packages.lookup(pid))

def load_deadline_packages(truck, deadline_pkgs, package_to_group, packages):
    """Load deadline packages onto truck."""
    # Sort by deadline time (earliest first)
    sorted_pkgs = sorted(deadline_pkgs, 
                        key=lambda p: packages.lookup(p).deadline_time or datetime.max)
    
    for pid in sorted_pkgs:
        if pid in truck.cargo:
            continue  # Already loaded
            
        if pid in package_to_group:
            # Check if we can fit the entire group
            group_id = package_to_group[pid]
            group_members = [p for p in packages if p in package_to_group 
                           and package_to_group[p] == group_id 
                           and p not in truck.cargo]
            
            if group_members:  # Only try to load if there are unloaded members
                load_group_to_truck(truck, group_members, packages)
        else:
            if truck.has_capacity():
                truck.load_package(packages.lookup(pid))

def load_delayed_packages(truck, delayed_pkgs, package_to_group, packages):
    """Load delayed packages onto truck."""
    for pid in delayed_pkgs:
        if pid in truck.cargo:
            continue  # Already loaded
            
        if truck.has_capacity():
            truck.load_package(packages.lookup(pid))

def load_remaining_packages(truck1, truck2, standard_pkgs, package_to_group, packages):
    """Load remaining standard packages with balanced distribution."""
    # Group remaining packages by their groups
    remaining_groups = {}
    for pid in standard_pkgs:
        if pid in package_to_group:
            group_id = package_to_group[pid]
            if group_id not in remaining_groups:
                remaining_groups[group_id] = []
            remaining_groups[group_id].append(pid)
    
    # Distribute remaining grouped packages
    for group_id, pids in remaining_groups.items():
        # Get the list of all packages in this group
        group_members = [p for p in packages if p in package_to_group 
                       and package_to_group[p] == group_id]
        
        # Choose truck with more space
        truck1_space = truck1.capacity - len(truck1.cargo)
        truck2_space = truck2.capacity - len(truck2.cargo)
        
        target_truck = truck1 if truck1_space >= truck2_space and truck1_space >= len(group_members) else truck2
        
        if len(target_truck.cargo) + len(group_members) <= target_truck.capacity:
            load_group_to_truck(target_truck, group_members, packages)
            # Remove from standard packages list
            for pid in group_members:
                if pid in standard_pkgs:
                    standard_pkgs.remove(pid)
    
    # Distribute remaining individual packages
    remaining_packages = [pid for pid in standard_pkgs if pid not in truck1.cargo and pid not in truck2.cargo]
    
    for pid in remaining_packages:
        # Choose truck with more remaining capacity
        target_truck = truck1 if truck1.capacity - len(truck1.cargo) >= truck2.capacity - len(truck2.cargo) else truck2
        
        if target_truck.has_capacity():
            target_truck.load_package(packages.lookup(pid))

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
        
def load_by_proximity(truck1, truck2, standard_pkgs, packages, distance_matrix, address_map):
    """Load remaining packages based on geographical proximity."""
    # Skip if no standard packages
    if not standard_pkgs:
        return
    
    # Calculate distances from hub for each package
    hub_distances = {}
    for pid in standard_pkgs:
        pkg = packages.lookup(pid)
        if pkg:
            hub_distances[pid] = get_distance("hub", pkg.address, distance_matrix, address_map)
    
    # Calculate center points for current cargo of each truck
    truck1_center = calculate_center(truck1.cargo, packages)
    truck2_center = calculate_center(truck2.cargo, packages)
    
    # For each remaining package, calculate distance to each truck's center
    for pid in standard_pkgs:
        if pid in truck1.cargo or pid in truck2.cargo:
            continue
            
        pkg = packages.lookup(pid)
        if not pkg:
            continue
            
        # Calculate distances to each truck's center
        dist_to_truck1 = get_distance(pkg.address, truck1_center, distance_matrix, address_map) if truck1_center else float('inf')
        dist_to_truck2 = get_distance(pkg.address, truck2_center, distance_matrix, address_map) if truck2_center else float('inf')
        
        # Assign to closest truck if it has capacity
        if dist_to_truck1 <= dist_to_truck2 and truck1.has_capacity():
            truck1.load_package(pkg)
        elif dist_to_truck2 < dist_to_truck1 and truck2.has_capacity():
            truck2.load_package(pkg)
        else:
            # If preferred truck is full, try the other one
            if truck1.has_capacity():
                truck1.load_package(pkg)
            elif truck2.has_capacity():
                truck2.load_package(pkg)

def calculate_center(cargo_ids, packages):
    """Calculate the geographical center of a set of packages."""
    if not cargo_ids:
        return None
        
    # For simplicity, return the address of a random package in cargo
    # A more sophisticated approach would calculate a true center
    import random
    return packages.lookup(random.choice(cargo_ids)).address

def estimate_route_mileage(route, packages, distance_matrix, address_map):
    """Estimate the mileage for a route without actually executing it."""
    total = 0.0
    loc = 'hub'
    for pid in route:
        pkg = packages.lookup(pid)
        dist = get_distance(loc, pkg.address, distance_matrix, address_map)
        total += dist
        loc = pkg.address
    # Return trip
    total += get_distance(loc, 'hub', distance_matrix, address_map)
    return total

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
        # But only generate summary report for the best one
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
    
    # Get the best packages and trucks
    best_packages, best_trucks = best_result
    
    # Generate the summary report for the best solution
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
    # This is a simplified check - you'd need to implement a more thorough check
    
    return all_deadlines_met and all_trucks_respected and all_groups_kept  # Return a boolean, not a list

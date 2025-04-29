import copy
from datetime import datetime, time
from typing import Tuple, List, Dict, Set
from wgups.constants import TODAY, STATUS_DELIVERED, START_TIME, EARLY_DEADLINE_CUTOFF, STATUS_AT_HUB
from wgups.data_loader import load_packages, load_distances
from wgups.models import Truck
from wgups.utils import resolve_package_groups, get_distance
from wgups.reporting import generate_summary_report
from wgups.optimizers import RouteOptimizer

def execute_route(truck, packages, distance_matrix, address_map):
    """
    Execute a truck's delivery route with proper handling of address corrections.
    """
    location = "hub"
    i = 0
    
    while i < len(truck.route):
        pid = truck.route[i]
        pkg = packages.lookup(pid)
        
        # Skip non-existent packages
        if not pkg:
            i += 1
            continue
        
        # Handle packages with future address corrections
        if pkg.correction_time and truck.time < pkg.correction_time:
            time_to_correction = (pkg.correction_time - truck.time).total_seconds() / 3600
            
            if time_to_correction < 0.5:  # Within 30 minutes
                # Wait until correction time
                truck._log_event(f"Waiting for address correction for Package {pid}")
                truck.time = pkg.correction_time
            else:
                # Move package to end of route
                truck.route.pop(i)
                truck.route.append(pid)
                truck._log_event(f"Deferring Package {pid} until address correction at {pkg.correction_time.strftime('%H:%M')}")
                continue  # Don't increment i
        
        # Deliver the package
        distance = get_distance(location, pkg.get_address(truck.time), distance_matrix, address_map)
        truck.deliver(pkg, distance)
        location = pkg.get_address(truck.time)
        i += 1
    
    # Return to hub
    return_distance = get_distance(location, "hub", distance_matrix, address_map)
    truck.drive(return_distance)
    truck.return_to_hub()

def run_simulation(optimizer: RouteOptimizer) -> Tuple:
    """
    Run the WGUPS package delivery simulation.
    Returns (packages, trucks) tuple for reporting and CLI.
    """
    # Step 1: Load data and resolve package groups
    packages = load_packages()
    distance_matrix, address_map = load_distances()
    package_group = resolve_package_groups(packages)
    print(f"Resolved package groups: {package_group}")

    # Step 2: Initialize trucks
    truck1 = Truck(1)  # 8:00 AM
    truck2 = Truck(2, time=datetime.combine(TODAY, time(9, 5)))  # 9:05 AM

    # Step 3: Prepare package classification
    priority_packages = identify_priority_packages(packages)
    truck_specific_packages = identify_truck_specific_packages(packages)
    deadline_packages = identify_deadline_packages(packages)
    delayed_packages = identify_delayed_packages(packages)
    
    # Step 4: Create package group mapping and identify critical groups !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! redundant
    package_to_group = map_packages_to_groups(package_group)
    print(f"package to group: {package_to_group}")
    critical_groups = identify_critical_groups(packages, package_group)
    print(f"critical_groups: {critical_groups}")

    
    # Step 5: Load packages onto trucks - IMPROVED LOADING STRATEGY
    # First load truck-specific packages
    load_truck_specific_packages(truck1, truck2, truck_specific_packages, 
                               package_to_group, packages)
    print(f"after truck specific loading -> truck1: {truck1}, truck2: {truck2}") #----> WORKING
    
    # Then load critical groups (groups with deadline packages) to truck 1
    # This is the key change - load ALL critical groups to truck 1
    for group in critical_groups:
        load_group_to_truck(truck1, group, packages) # ----> WORKING
    
    # Load priority packages that aren't part of critical groups
    load_priority_packages(truck1, priority_packages, package_to_group, packages) # ----> WORKING. 

    # Then load other deadline packages
    load_deadline_packages(truck1, deadline_packages, package_to_group, packages)

    # Load delayed packages to truck 2
    load_delayed_packages(truck2, delayed_packages, package_to_group, packages)
    print(f"status after loading of delayed packages: {truck2} cargo: {truck2.cargo}")
    
    # Balance remaining packages
    standard_packages = identify_standard_packages(
        packages,
        priority_packages,
        truck_specific_packages,
        deadline_packages,
        delayed_packages,
        package_group
    )
    load_remaining_packages(truck1, truck2, standard_packages, package_to_group, packages)
    print(f"truck1 cargo: {truck1.cargo}, truck2 cargo: {truck2.cargo}")
    
    # Step 6: Execute delivery routes
    # First truck route (8:00 AM)
    truck1.set_route(optimizer.optimize(truck1, packages, distance_matrix, address_map, package_group))

    execute_route(truck1, packages, distance_matrix, address_map)

    
    # Second truck route (9:05 AM)
    truck2.set_route(optimizer.optimize(truck2, packages, distance_matrix, address_map, package_group))
    execute_route(truck2, packages, distance_matrix, address_map)
    
    # Handle any remaining undelivered packages
    deliver_remaining_packages(truck1, truck2, packages, optimizer, 
                             distance_matrix, address_map, package_group)
    
    # Step 7: Generate report
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
    print(f"urgent: {urgent}")
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

def load_group_to_truck(truck, group, packages):
    """Load an entire group of packages to a truck."""
    # Only load if truck has enough capacity
    if len(truck.cargo) + len(group) <= truck.capacity:
        for pid in group:
            if pid not in truck.cargo:
                pkg = packages.lookup(pid)
                if pkg:
                    truck.load_package(pkg)
        print(f"Loaded entire group {group} to Truck {truck.truck_id}")
    else:
        print(f"Warning: Cannot fit entire group {group} on Truck {truck.truck_id}. "
                    f"Group size: {len(group)}; Available capacity: {truck.capacity - len(truck.cargo)}")

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
        

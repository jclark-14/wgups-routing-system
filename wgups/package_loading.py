from datetime import datetime
from wgups.utils import get_distance, calculate_center

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
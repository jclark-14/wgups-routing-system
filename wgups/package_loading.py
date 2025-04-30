from datetime import datetime
from wgups.utils import get_distance, calculate_center

def load_group_to_truck(truck, group, packages, verbose=True):
    """
    Load a full package group to the truck if capacity allows.
    Skips loading if the group would exceed the truck's capacity.
    """
    if len(truck.cargo) + len(group) <= truck.capacity:
        for pid in group:
            if pid not in truck.cargo:
                pkg = packages.lookup(pid)
                if pkg:
                    truck.load_package(pkg)

def load_truck_specific_packages(truck1, truck2, truck_specific_pkgs, package_to_group, packages):
    """
    Assign packages that are restricted to specific trucks.
    Group constraints are respected where applicable.
    """
    for pid in truck_specific_pkgs[1]:
        if pid in package_to_group:
            group_id = package_to_group[pid]
            group_members = [p for p in packages if package_to_group.get(p) == group_id]
            load_group_to_truck(truck1, group_members, packages)
        else:
            if truck1.has_capacity():
                truck1.load_package(packages.lookup(pid))

    for pid in truck_specific_pkgs[2]:
        if pid in package_to_group:
            group_id = package_to_group[pid]
            group_members = [p for p in packages if package_to_group.get(p) == group_id]
            load_group_to_truck(truck2, group_members, packages)
        else:
            if truck2.has_capacity():
                truck2.load_package(packages.lookup(pid))

def load_priority_packages(truck, priority_pkgs, package_to_group, packages):
    """
    Load high-priority packages, honoring group constraints if space allows.
    Falls back to individual package if group doesn't fit.
    """
    for pid in priority_pkgs:
        if pid in truck.cargo:
            continue
            
        if truck.has_capacity():
            if pid in package_to_group:
                group_id = package_to_group[pid]
                group_members = [p for p in packages if package_to_group.get(p) == group_id]
                
                if len(truck.cargo) + len(group_members) <= truck.capacity:
                    load_group_to_truck(truck, group_members, packages)
                else:
                    truck.load_package(packages.lookup(pid))
            else:
                truck.load_package(packages.lookup(pid))

def load_deadline_packages(truck, deadline_pkgs, package_to_group, packages):
    """
    Load all remaining packages with early deadlines (≤10:30 AM).
    Sorted by earliest deadline first. Honors group constraints.
    """
    sorted_pkgs = sorted(
        deadline_pkgs,
        key=lambda p: packages.lookup(p).deadline_time or datetime.max
    )

    for pid in sorted_pkgs:
        if pid in truck.cargo:
            continue

        if pid in package_to_group:
            group_id = package_to_group[pid]
            group_members = [
                p for p in packages
                if package_to_group.get(p) == group_id and p not in truck.cargo
            ]
            if group_members:
                load_group_to_truck(truck, group_members, packages)
        else:
            if truck.has_capacity():
                truck.load_package(packages.lookup(pid))

def load_delayed_packages(truck, delayed_pkgs, package_to_group, packages):
    """
    Load packages that became available later in the day due to delay notes.
    Assumes truck departure time is after availability.
    """
    for pid in delayed_pkgs:
        if pid in truck.cargo:
            continue
        if truck.has_capacity():
            truck.load_package(packages.lookup(pid))

def load_by_proximity(truck1, truck2, standard_pkgs, packages, distance_matrix, address_map):
    """
    Assign remaining unconstrained packages based on proximity to existing cargo clusters.
    Each truck is treated as having a geographic 'center'.
    """
    if not standard_pkgs:
        return

    # Calculate center addresses for current cargo
    truck1_center = calculate_center(truck1.cargo, packages)
    truck2_center = calculate_center(truck2.cargo, packages)

    for pid in standard_pkgs:
        if pid in truck1.cargo or pid in truck2.cargo:
            continue

        pkg = packages.lookup(pid)
        if not pkg:
            continue

        # Compare distance from package to each truck's delivery center
        dist_to_truck1 = get_distance(pkg.address, truck1_center, distance_matrix, address_map) if truck1_center else float('inf')
        dist_to_truck2 = get_distance(pkg.address, truck2_center, distance_matrix, address_map) if truck2_center else float('inf')

        # Prefer closer truck if it has space
        if dist_to_truck1 <= dist_to_truck2 and truck1.has_capacity():
            truck1.load_package(pkg)
        elif dist_to_truck2 < dist_to_truck1 and truck2.has_capacity():
            truck2.load_package(pkg)
        else:
            # Try the other if preferred is full
            if truck1.has_capacity():
                truck1.load_package(pkg)
            elif truck2.has_capacity():
                truck2.load_package(pkg)

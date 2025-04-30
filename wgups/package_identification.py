from datetime import time
from typing import List, Dict, Set
from wgups.constants import EARLY_DEADLINE_CUTOFF, START_TIME

def identify_priority_packages(packages) -> List[int]:
    """
    Identify packages that require special priority due to critical deadlines.
    
    Returns:
        List of package IDs with deadlines before or at EARLY_DEADLINE_CUTOFF (e.g., 9:15 AM).
    """
    urgent = []
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.deadline_time and pkg.deadline_time.time() <= EARLY_DEADLINE_CUTOFF:
            urgent.append(pid)
    return urgent

def identify_truck_specific_packages(packages) -> Dict[int, List[int]]:
    """
    Identify packages that are restricted to specific trucks (Truck 1 or 2).
    
    Returns:
        Dictionary mapping truck number to a list of package IDs.
    """
    truck_specific = {1: [], 2: []}
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.only_truck in [1, 2]:
            truck_specific[pkg.only_truck].append(pid)
    return truck_specific

def identify_deadline_packages(packages) -> List[int]:
    """
    Identify early-deadline packages that are unrestricted and available at start time.
    
    Returns:
        List of package IDs.
    """
    deadline_pkgs = []
    for pid in packages:
        pkg = packages.lookup(pid)
        if (
            pkg.deadline_time and 
            pkg.deadline_time.time() <= time(10, 30) and
            pkg.available_time == START_TIME and
            not pkg.only_truck
        ):
            deadline_pkgs.append(pid)
    return deadline_pkgs

def identify_delayed_packages(packages) -> List[int]:
    """
    Identify packages that are not available for loading at 8:00 AM.
    
    Returns:
        List of package IDs with delayed availability.
    """
    delayed_pkgs = []
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.available_time > START_TIME:
            delayed_pkgs.append(pid)
    return delayed_pkgs

def identify_standard_packages(
    packages,
    priority_pkgs,
    truck_specific_pkgs,
    deadline_pkgs,
    delayed_pkgs,
    package_groups
) -> List[int]:
    """
    Identify packages with no delivery constraints or grouping requirements.
    
    Returns:
        List of unconstrained package IDs.
    """
    standard_pkgs = []

    # Aggregate all constrained packages (including grouped packages)
    constrained = set(priority_pkgs)
    constrained.update(truck_specific_pkgs[1])
    constrained.update(truck_specific_pkgs[2])
    constrained.update(deadline_pkgs)
    constrained.update(delayed_pkgs)
    for group in package_groups:
        constrained.update(group)

    # Filter out constrained packages
    for pid in packages:
        if pid not in constrained:
            standard_pkgs.append(pid)

    return standard_pkgs

def map_packages_to_groups(package_group) -> Dict[int, int]:
    """
    Generate a reverse lookup: package ID -> group ID.
    Group ID is chosen as the smallest ID in each group for stability.
    
    Returns:
        Dictionary mapping each package ID to its group representative.
    """
    package_to_group = {}
    for group in package_group:
        group_id = min(group)  # Use smallest ID in group as identifier
        for pid in group:
            package_to_group[pid] = group_id
    return package_to_group

def identify_critical_groups(packages, package_groups) -> List[Set[int]]:
    """
    Identify delivery groups that include at least one deadline package.
    These groups require special routing consideration.
    
    Returns:
        List of critical group sets.
    """
    critical_groups = []

    for group in package_groups:
        deadline_count = sum(
            1 for pid in group 
            if packages.lookup(pid) and packages.lookup(pid).deadline_time
        )
        if deadline_count > 0:
            critical_groups.append(group)

    return critical_groups

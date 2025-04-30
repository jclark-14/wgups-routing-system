from datetime import time
from typing import List, Dict, Set
from wgups.constants import EARLY_DEADLINE_CUTOFF, START_TIME

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
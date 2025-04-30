from datetime import datetime
from typing import Optional, List, Set
from wgups.constants import TIME_RE, TRUCK_RE, DIRECTION_MAP, START_TIME

def time_from_str(note: str) -> datetime | None:
    """Extract datetime from a string using regex."""
    match = TIME_RE.search(note)
    if not match:
        return None
        
    hh_mm, ampm = match.groups()
    format_time = "%I:%M %p" if ampm else "%H:%M"
    return datetime.combine(datetime.today().date(),
                          datetime.strptime(f"{hh_mm} {ampm or ''}".strip(), format_time).time())

def truck_from_note(note: str) -> Optional[int]:
    """Extract truck number from a note."""
    match = TRUCK_RE.search(note)
    return int(match.group(1)) if match else None

def normalize_address(address: str) -> str:
    """Normalize address format for consistent lookup."""
    if not address:
        return "hub"
    
    address = address.replace("\n", " ").replace(".", "").lower().strip()
    address = address.split("(")[0].strip()
    words = address.split()
    normalized_words = [DIRECTION_MAP.get(word, word) for word in words]
    normalized = " ".join(normalized_words)
    
    # Special case for hub
    if normalized in ["hub", "wgu", "wgups"]:
        return "hub"
        
    return normalized

def get_distance(from_addr: str, to_addr: str, distance_matrix, address_map) -> float:
    """Get distance between two addresses using the distance matrix."""
    # Normalize addresses
    from_norm = normalize_address(from_addr)
    to_norm = normalize_address(to_addr)
    
    # Handle addresses not in map
    if from_norm not in address_map:
        print(f"Warning: Address not in map: '{from_norm}' (original: '{from_addr}')")
        from_norm = "hub"
    
    if to_norm not in address_map:
        print(f"Warning: Address not in map: '{to_norm}' (original: '{to_addr}')")
        to_norm = "hub"
    
    # Get indices and lookup distance
    idx1 = address_map[from_norm]
    idx2 = address_map[to_norm]
    
    return distance_matrix[idx1][idx2]

def resolve_package_groups(packages) -> List[Set[int]]:
    """
    Resolve package groups with proper handling of transitive relationships.
    """
    # Build a graph of direct relationships
    direct_relationships = {}
    
    for pid in packages:
        pkg = packages.lookup(pid)
        if not pkg or not pkg.group_with:
            continue
            
        # Initialize sets for both the package and its group members
        direct_relationships.setdefault(pid, set())
        
        # Add bidirectional connections
        for related_pid in pkg.group_with:
            direct_relationships.setdefault(related_pid, set())
            direct_relationships[pid].add(related_pid)
            direct_relationships[related_pid].add(pid)
    
    # Find connected components (transitive groups)
    visited = set()
    group = []
    
    for pid in direct_relationships:
        if pid in visited:
            continue
            
        # Start a new group
        group_set = set()
        queue = [pid]
        
        # BFS to find all connected nodes
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
                
            visited.add(current)
            group_set.add(current)
            
            # Add all connected nodes
            queue.extend([p for p in direct_relationships.get(current, set()) 
                         if p not in visited])
        
    if group_set:
        group.append(group_set)
    return group

def calculate_center(cargo_ids, packages):
    """Calculate the geographical center of a set of packages."""
    if not cargo_ids:
        return None
        
    # For simplicity, return the address of a random package in cargo
    # A more sophisticated approach would calculate a true center
    import random
    return packages.lookup(random.choice(cargo_ids)).address
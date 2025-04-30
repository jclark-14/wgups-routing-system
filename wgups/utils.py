from datetime import datetime
from typing import Optional, List, Set
from wgups.constants import TIME_RE, TRUCK_RE, DIRECTION_MAP


def time_from_str(note: str) -> datetime | None:
    """
    Extract a datetime from a string using regex.

    Supports formats like '9:05 AM' or '14:30'.
    Returns None if no time is found.
    """
    match = TIME_RE.search(note)
    if not match:
        return None

    hh_mm, ampm = match.groups()
    format_time = "%I:%M %p" if ampm else "%H:%M"
    return datetime.combine(datetime.today().date(),
                            datetime.strptime(f"{hh_mm} {ampm or ''}".strip(), format_time).time())


def truck_from_note(note: str) -> Optional[int]:
    """
    Extract the truck number from a note string -> 'Truck 2'
    """
    match = TRUCK_RE.search(note)
    return int(match.group(1)) if match else None


def normalize_address(address: str) -> str:
    """
    Normalize address strings for consistent lookup.

    - Converts to lowercase
    - Removes punctuation and parenthetical notes
    - Maps directional terms like 'South' to 's'
    - Converts common variations of 'hub' to 'hub'
    """
    if not address:
        return "hub"

    address = address.replace("\n", " ").replace(".", "").lower().strip()
    address = address.split("(")[0].strip()
    words = address.split()
    normalized_words = [DIRECTION_MAP.get(word, word) for word in words]
    normalized = " ".join(normalized_words)

    if normalized in ["hub", "wgu", "wgups"]:
        return "hub"

    return normalized


def get_distance(from_addr: str, to_addr: str, distance_matrix, address_map) -> float:
    """
    Get the distance between two addresses using the distance matrix.

    Falls back to 'hub' if either address is not recognized.
    """
    from_norm = normalize_address(from_addr)
    to_norm = normalize_address(to_addr)

    if from_norm not in address_map:
        print(f"Warning: Address not in map: '{from_norm}' (original: '{from_addr}')")
        from_norm = "hub"

    if to_norm not in address_map:
        print(f"Warning: Address not in map: '{to_norm}' (original: '{to_addr}')")
        to_norm = "hub"

    idx1 = address_map[from_norm]
    idx2 = address_map[to_norm]

    return distance_matrix[idx1][idx2]


def resolve_package_groups(packages) -> List[Set[int]]:
    """
    Resolve transitive package groups using package notes.

    Returns:
        List of sets, where each set contains a group of interdependent package IDs.
    """
    direct_relationships = {}

    # Build bidirectional relationship map
    for pid in packages:
        pkg = packages.lookup(pid)
        if not pkg or not pkg.group_with:
            continue

        direct_relationships.setdefault(pid, set())
        for related_pid in pkg.group_with:
            direct_relationships.setdefault(related_pid, set())
            direct_relationships[pid].add(related_pid)
            direct_relationships[related_pid].add(pid)

    # BFS to resolve transitive groupings
    visited = set()
    groups = []

    for pid in direct_relationships:
        if pid in visited:
            continue

        group_set = set()
        queue = [pid]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue

            visited.add(current)
            group_set.add(current)
            queue.extend([p for p in direct_relationships.get(current, set()) if p not in visited])

        if group_set:
            groups.append(group_set)

    return groups


def calculate_center(cargo_ids, packages):
    """
    Return a representative address from the list of cargo package IDs.

    For simplicity, returns a random package address from the list.
    """
    if not cargo_ids:
        return None

    import random
    return packages.lookup(random.choice(cargo_ids)).address

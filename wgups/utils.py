from datetime import datetime
from typing import Optional
from wgups.constants import _TRUCK_RE, TIME_RE, DIRECTION_MAP


def time_from_str(note: str) -> datetime | None:
    """Extract datetime from note using regex or returns None"""
    m = TIME_RE.search(note)
    if not m:
        return None
    hh_mm, ampm = m.groups()
    format_time = "%I:%M %p" if ampm else "%H:%M"
    return datetime.combine(datetime.today().date(),
                            datetime.strptime(f"{hh_mm} {ampm or ''}".strip(), format_time).time())

def truck_from_note(note: str) -> Optional[int]:
    """Grab X in “truck X”, return X as int, or None if otherwise."""
    m = _TRUCK_RE.search(note)
    return int(m.group(1)) if m else None

def normalize(address: str) -> str:
    # Normalize address string
    address = address.replace("\n", " ").replace(".", "").lower().strip()
    address = address.split("(")[0].strip()
    words = address.split()
    normalized_words = [DIRECTION_MAP.get(word, word) for word in words]
    return " ".join(normalized_words)

def get_distance(from_addr: str, to_addr: str, distance_matrix, address_map) -> float:
    idx1 = address_map[from_addr]
    idx2 = address_map[to_addr]
    return distance_matrix[idx1][idx2]

def resolve_package_groups(packages):
    group_map = {pid: packages.lookup(pid).group_with for pid in range(1, len(packages) + 1)}

    visited = set()
    resolved_groups = []

    for pkg_id in group_map:
        if pkg_id in visited:
            continue
        stack = [pkg_id]
        group = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            group.add(current)
            stack.extend(group_map.get(current, []))
        if len(group) > 1:
            resolved_groups.append(group)

    return resolved_groups

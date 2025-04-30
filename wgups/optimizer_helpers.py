from typing import List
from datetime import time, timedelta
import itertools
from wgups.entities import Truck
from wgups.data_structures import HashTable
from wgups.utils import get_distance
from wgups.constants import STRICT_DEADLINE_CUTOFF

def handle_address_corrections(truck: Truck, packages: HashTable):
    """
    Separates packages that cannot yet be delivered due to pending address corrections.
    
    Returns:
        Tuple[List[int], List[int]]: (deliverable package IDs, deferred package IDs)
    """
    current = []
    deferred = []

    for pid in truck.cargo:
        pkg = packages.lookup(pid)
        if pkg and pkg.correction_time and pkg.correction_time > truck.time:
            deferred.append(pid)
        else:
            current.append(pid)

    return current, deferred

def categorize_packages(pids: List[int], packages: HashTable):
    """
    Split a list of package IDs into early deadline vs. non-deadline categories.
    
    Returns:
        Tuple[List[int], List[int]]: (deadline package IDs, other package IDs)
    """
    deadlines = []
    others = []

    for pid in pids:
        pkg = packages.lookup(pid)
        if pkg and pkg.deadline_time and pkg.deadline_time.time() <= time(10, 30):
            deadlines.append(pid)
        else:
            others.append(pid)

    return deadlines, others

def optimize_with_permutations(
    deadlines: List[int], others: List[int], deferred: List[int],
    packages: HashTable, distance_matrix, address_map, truck: Truck
) -> List[int]:
    """
    Brute-force route optimization for small sets of deadline packages.
    Ensures all deadlines are met and tries to minimize total mileage.
    """
    best, best_score = None, float('inf')

    for perm in itertools.permutations(deadlines):
        time_cursor = truck.time
        loc = 'hub'
        total_dist = 0.0
        on_time = True

        for pid in perm:
            pkg = packages.lookup(pid)
            dist = get_distance(loc, pkg.get_address(time_cursor), distance_matrix, address_map)
            total_dist += dist
            time_cursor += timedelta(hours=dist / truck.speed)

            if pkg.deadline_time and time_cursor > pkg.deadline_time:
                on_time = False
                break

            loc = pkg.get_address(time_cursor)

        if on_time and total_dist < best_score:
            best, best_score = list(perm), total_dist

    if not best:
        return None

    # Fill in remaining route using Nearest Neighbor for non-deadline packages
    route = best.copy()
    remaining = set(others)
    loc = packages.lookup(route[-1]).get_address(truck.time) if route else 'hub'

    while remaining:
        nxt, min_d = None, float('inf')
        for pid in list(remaining):
            pkg = packages.lookup(pid)
            dist = get_distance(loc, pkg.get_address(truck.time), distance_matrix, address_map)
            if dist < min_d:
                min_d, nxt = dist, pid
        if nxt is None:
            break
        route.append(nxt)
        remaining.remove(nxt)
        loc = packages.lookup(nxt).get_address(truck.time)

    return route

def nearest_neighbor(
    pids: List[int], packages: HashTable, distance_matrix, address_map
) -> List[int]:
    """
    Generate a route using Nearest Neighbor with early deadline prioritization.
    """
    route = []
    remaining = set(pids)
    loc = 'hub'

    # Step 1: Prioritize packages with early deadlines
    early = [
        (pid, packages.lookup(pid).deadline_time)
        for pid in remaining
        if packages.lookup(pid) and packages.lookup(pid).deadline_time
           and packages.lookup(pid).deadline_time.time() <= time(10, 00)
    ]
    early.sort(key=lambda x: x[1])

    for pid, _ in early:
        if pid in remaining:
            route.append(pid)
            remaining.remove(pid)
            loc = packages.lookup(pid).get_address(packages.truck.time)

    # Step 2: Greedy selection by nearest distance (with deadline weighting)
    while remaining:
        nxt, min_d = None, float('inf')
        for pid in list(remaining):
            pkg = packages.lookup(pid)
            dist = get_distance(loc, pkg.get_address(packages.truck.time), distance_matrix, address_map)
            weight = 0.9 if pkg.deadline_time else 1.0  # Slight bias toward deadline packages
            if dist * weight < min_d:
                min_d, nxt = dist * weight, pid
        if nxt is None:
            break
        route.append(nxt)
        remaining.remove(nxt)
        loc = packages.lookup(nxt).get_address(packages.truck.time)

    return route

def apply_2opt(route: List[int], packages: HashTable, distance_matrix, address_map) -> List[int]:
    """
    Apply 2-opt route optimization with awareness of deadline constraints.
    """
    if len(route) <= 2:
        return route

    best = route.copy()
    best_dist = calculate_route_distance(best, packages, distance_matrix, address_map)

    # Pre-calculate delivery timeline
    calculate_delivery_times(route, packages, distance_matrix, address_map)

    # Track which packages have early deadlines
    deadline_packages = [
        pid for pid in route
        if (pkg := packages.lookup(pid)) and pkg.deadline_time and pkg.deadline_time.time() <= STRICT_DEADLINE_CUTOFF
    ]

    improved = True
    while improved:
        improved = False
        for i in range(len(best)-1):
            for j in range(i+2, len(best)):
                segment = best[i:j+1]
                reversed_segment = segment[::-1]

                # Skip if this swap delays any deadline package
                if any(
                    pid in segment and reversed_segment.index(pid) > segment.index(pid)
                    for pid in deadline_packages
                ):
                    continue

                new_route = best[:i] + reversed_segment + best[j+1:]
                new_dist = calculate_route_distance(new_route, packages, distance_matrix, address_map)

                if new_dist < best_dist:
                    best, best_dist, improved = new_route, new_dist, True
                    break
            if improved:
                break

    return best

def calculate_route_distance(
    route: List[int], packages: HashTable, distance_matrix, address_map
) -> float:
    """
    Return the total distance for a given route, including return to hub.
    """
    total = 0.0
    loc = 'hub'
    for pid in route:
        pkg = packages.lookup(pid)
        dist = get_distance(loc, pkg.get_address(packages.truck.time), distance_matrix, address_map)
        total += dist
        loc = pkg.get_address(packages.truck.time)
    total += get_distance(loc, 'hub', distance_matrix, address_map)
    return total

def calculate_delivery_times(route, packages, distance_matrix, address_map):
    """
    Calculate the projected delivery times of a route based on distance and truck speed.
    Returns a dict of package ID → delivery time.
    """
    delivery_times = {}
    loc = 'hub'
    current_time = packages.truck.time

    for pid in route:
        pkg = packages.lookup(pid)
        dist = get_distance(loc, pkg.get_address(current_time), distance_matrix, address_map)
        travel_time = timedelta(hours=dist / packages.truck.speed)
        current_time += travel_time
        delivery_times[pid] = current_time
        loc = pkg.get_address(current_time)

    return delivery_times

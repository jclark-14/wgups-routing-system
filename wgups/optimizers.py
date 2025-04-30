from typing import List
from datetime import datetime, time, timedelta
import itertools
from wgups.models import Truck
from wgups.data_structures import HashTable
from wgups.utils import get_distance
from wgups.constants import STRICT_DEADLINE_CUTOFF

class RouteOptimizer:
    """Base class for route optimization algorithms."""
    def optimize(self, truck: Truck, packages: HashTable, distance_matrix, address_map, group) -> List[int]:
        """Optimize delivery route for a truck."""
        raise NotImplementedError

class NN2OptOptimizer(RouteOptimizer):
    """
    Enhanced route optimizer that combines:
    1. Special handling for deadline packages (<= 10:30 AM)
    2. Nearest neighbor heuristic with deadline prioritization
    3. 2-Opt route refinement
    4. Permutation-based optimization for small deadline sets
    """
    def optimize(self, truck: Truck, packages: HashTable, distance_matrix, address_map, group) -> List[int]:
        if not truck.cargo:
            return []
        # Make truck available to helper methods
        packages.truck = truck

        # Extract packages requiring address corrections
        current_cargo, deferred = self._handle_address_corrections(truck, packages)
        
        # Split into deadline (<=10:30) and other packages
        deadlines, others = self._categorize_packages(current_cargo, packages)
        # For small deadline sets, try all permutations to meet deadlines
        if deadlines and len(deadlines) <= 5:

            perm_route = self._optimize_with_permutations(
                deadlines, others, deferred,
                packages, distance_matrix, address_map, truck
            )
            if perm_route:
                return perm_route

        # nearest neighbor, then refine with 2-opt
        route = self._nearest_neighbor(current_cargo, packages, distance_matrix, address_map)
        optimized = self._apply_2opt(route, packages, distance_matrix, address_map)

        # Append any deferred (address‐correction) packages at end
        return optimized + deferred

    def _handle_address_corrections(self, truck: Truck, packages: HashTable):
        current = []
        deferred = []
        for pid in truck.cargo:
            pkg = packages.lookup(pid)
            if pkg and pkg.correction_time and pkg.correction_time > truck.time:
                deferred.append(pid)
            else:
                current.append(pid)
        return current, deferred

    def _categorize_packages(self, pids: List[int], packages: HashTable):
        deadlines = []
        others = []
        for pid in pids:
            pkg = packages.lookup(pid)
            if pkg and pkg.deadline_time and pkg.deadline_time.time() <= time(10, 30):
                deadlines.append(pid)
            else:
                others.append(pid)
        return deadlines, others

    def _optimize_with_permutations(
        self, deadlines: List[int], others: List[int], deferred: List[int],
        packages: HashTable, distance_matrix, address_map, truck: Truck
    ) -> List[int]:
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
        # fill route: best deadlines + nearest neighbor for others
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
    

    def _nearest_neighbor(
        self, pids: List[int], packages: HashTable, distance_matrix, address_map
    ) -> List[int]:
        route = []
        remaining = set(pids)
        loc = 'hub'
        # pick all early deadlines first
        early = [(pid, packages.lookup(pid).deadline_time)
                 for pid in remaining
                 if packages.lookup(pid) and packages.lookup(pid).deadline_time
                 and packages.lookup(pid).deadline_time.time() <= time(10, 00)]
        early.sort(key=lambda x: x[1])
        for pid, _ in early:
            if pid in remaining:
                route.append(pid)
                remaining.remove(pid)
                loc = packages.lookup(pid).get_address(packages.truck.time)
   
        # then nearest neighbor for rest
        while remaining:
            nxt, min_d = None, float('inf')
            for pid in list(remaining):
                pkg = packages.lookup(pid)
                dist = get_distance(loc, pkg.get_address(packages.truck.time), distance_matrix, address_map)
                weight = 0.9 if pkg.deadline_time else 1.0
                if dist * weight < min_d:
                    min_d, nxt = dist * weight, pid
            if nxt is None:
                break
            route.append(nxt)
            remaining.remove(nxt)
            loc = packages.lookup(nxt).get_address(packages.truck.time)
        return route

    def _apply_2opt(self, route: List[int], packages: HashTable, distance_matrix, address_map) -> List[int]:
        if len(route) <= 2:
            return route
        
        best = route.copy()
        best_dist = self._calculate_route_distance(best, packages, distance_matrix, address_map)
        
        # Calculate delivery times for the initial route
        initial_delivery_times = self._calculate_delivery_times(route, packages, distance_matrix, address_map)
    
    
        
        # Identify deadline-sensitive packages (before 10:30)
        deadline_packages = []
        for pid in route:
            pkg = packages.lookup(pid)
            if pkg and pkg.deadline_time and pkg.deadline_time.time() <= STRICT_DEADLINE_CUTOFF:
                deadline_packages.append(pid)
        
        # Store original positions of deadline packages
        improved = True
        while improved:
            improved = False
            for i in range(len(best)-1):
                for j in range(i+2, len(best)):
                    # Check if this swap would negatively affect deadline packages
                    segment = best[i:j+1]
                    reversed_segment = segment[::-1]
                    
                    # Skip this swap if it would delay any deadline package
                    will_delay_deadline = False
                    for pid in deadline_packages:
                        if pid in segment:
                            old_idx = i + segment.index(pid)
                            new_idx = i + reversed_segment.index(pid)
                            if new_idx > old_idx:  # Package would be moved later in route
                                will_delay_deadline = True
                                break
                    
                    if will_delay_deadline:
                        continue
                    
                    # If we get here, this swap is safe for deadline packages
                    new_route = best[:i] + reversed_segment + best[j+1:]
                    new_dist = self._calculate_route_distance(new_route, packages, distance_matrix, address_map)
                    
                    if new_dist < best_dist:
                        best, best_dist, improved = new_route, new_dist, True
                        break
                if improved:
                    break
        
        return best

    def _calculate_route_distance(
        self, route: List[int], packages: HashTable, distance_matrix, address_map
    ) -> float:
        total = 0.0
        loc = 'hub'
        for pid in route:
            pkg = packages.lookup(pid)
            dist = get_distance(loc, pkg.get_address(packages.truck.time), distance_matrix, address_map)
            total += dist
            loc = pkg.get_address(packages.truck.time)
        # return trip
        total += get_distance(loc, 'hub', distance_matrix, address_map)
        return total

    def _calculate_delivery_times(self, route, packages, distance_matrix, address_map):
        """Calculate the estimated delivery time for each package in the route."""
        delivery_times = {}
        loc = 'hub'
        current_time = packages.truck.time  # Start time from truck
        
        for pid in route:
            pkg = packages.lookup(pid)
            dist = get_distance(loc, pkg.get_address(current_time), distance_matrix, address_map)
            travel_time = timedelta(hours=dist / packages.truck.speed)
            current_time += travel_time
            delivery_times[pid] = current_time
            loc = pkg.get_address(current_time)
        
        return delivery_times
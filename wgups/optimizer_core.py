from typing import List
from wgups.entities import Truck
from wgups.data_structures import HashTable
from wgups.optimizer_helpers import (
    handle_address_corrections,
    categorize_packages,
    optimize_with_permutations,
    nearest_neighbor,
    apply_2opt,
    calculate_route_distance
)

class RouteOptimizer:
    """
    Abstract base class for route optimization strategies.
    All subclasses must implement the `optimize` method.
    """
    def optimize(self, truck: Truck, packages: HashTable, distance_matrix, address_map, group) -> List[int]:
        """Generate an optimized delivery route."""
        raise NotImplementedError


class NN2OptOptimizer(RouteOptimizer):
    """
    Enhanced route optimizer that combines multiple strategies:
    
    1. Address correction awareness (delayed delivery)
    2. Deadline-aware categorization (<= 10:30 AM)
    3. Permutation-based brute-force search for small deadline sets
    4. Nearest Neighbor heuristic for fast baseline
    5. 2-Opt algorithm for route refinement
    """
    
    def optimize(self, truck: Truck, packages: HashTable, distance_matrix, address_map, group) -> List[int]:
       
        if not truck.cargo:
            return []

        packages.truck = truck

        # Step 1: Separate packages that require address correction
        current_cargo, deferred = handle_address_corrections(truck, packages)

        # Check if current_cargo is empty
        if not current_cargo:
            return deferred

        # Step 2: Split packages into deadlines vs non-deadlines
        deadlines, others = categorize_packages(current_cargo, packages)

        # Step 3: Use brute-force search if deadline set is small
        if deadlines and len(deadlines) <= 5:
            perm_route = optimize_with_permutations(
                deadlines, others, deferred,
                packages, distance_matrix, address_map, truck
            )
            if perm_route: 
                # Use the deliverable packages for baseline calculations
                if current_cargo:
                    nn_route = nearest_neighbor(current_cargo, packages, distance_matrix, address_map)
                    opt_route = apply_2opt(nn_route, packages, distance_matrix, address_map)
                    
                    truck.nn_miles = calculate_route_distance(nn_route, packages, distance_matrix, address_map)
                    truck.opt_miles = calculate_route_distance(opt_route, packages, distance_matrix, address_map)
                    
                return perm_route

        # Step 4: Run nearest neighbor for route baseline
        route = nearest_neighbor(current_cargo, packages, distance_matrix, address_map)

        # Step 5: Refine route using 2-opt
        optimized = apply_2opt(route, packages, distance_matrix, address_map)
        
        # Store distances between algorithms for BOTH trucks
        nn_dist = calculate_route_distance(route, packages, distance_matrix, address_map)
        opt_dist = calculate_route_distance(optimized, packages, distance_matrix, address_map)

        truck.nn_miles = nn_dist
        truck.opt_miles = opt_dist

        return optimized + deferred
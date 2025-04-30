from typing import List
from wgups.models import Truck
from wgups.data_structures import HashTable
from wgups.optimizer_helpers import handle_address_corrections, categorize_packages, optimize_with_permutations, nearest_neighbor, apply_2opt



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
        current_cargo, deferred = handle_address_corrections(truck, packages)
        
        # Split into deadline (<=10:30) and other packages
        deadlines, others = categorize_packages(current_cargo, packages)
        # For small deadline sets, try all permutations to meet deadlines
        if deadlines and len(deadlines) <= 5:

            perm_route = optimize_with_permutations(
                deadlines, others, deferred,
                packages, distance_matrix, address_map, truck
            )
            if perm_route:
                return perm_route

        # nearest neighbor, then refine with 2-opt
        route = nearest_neighbor(current_cargo, packages, distance_matrix, address_map)
        optimized = apply_2opt(route, packages, distance_matrix, address_map)

        # Append any deferred (address‐correction) packages at end
        return optimized + deferred
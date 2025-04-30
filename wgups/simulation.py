from datetime import datetime, time
from typing import Tuple
from wgups.constants import TODAY, STATUS_DELIVERED
from wgups.data_loader import load_packages, load_distances
from wgups.entities import Truck
from wgups.utils import resolve_package_groups
from wgups.reporting import generate_summary_report
from wgups.optimizer_core import RouteOptimizer
from wgups.routing import execute_route, estimate_route_mileage
from wgups.package_identification import (
    map_packages_to_groups,
    identify_truck_specific_packages,
    identify_critical_groups,
    identify_deadline_packages,
    identify_delayed_packages,
    identify_priority_packages,
    identify_standard_packages
)
from wgups.package_loading import (
    load_by_proximity,
    load_deadline_packages,
    load_delayed_packages,
    load_group_to_truck,
    load_priority_packages,
    load_truck_specific_packages
)


def run_simulation(optimizer: RouteOptimizer, execute=True) -> Tuple:
    """
    Run a single WGUPS delivery simulation.

    Args:
        optimizer: The route optimization strategy to apply.
        execute: Whether to run the delivery routes or just plan them.

    Returns:
        Tuple of (packages, trucks)
    """
    packages = load_packages()
    distance_matrix, address_map = load_distances()
    package_group = resolve_package_groups(packages)

    truck1 = Truck(1)  # departs at 8:00 AM
    truck2 = Truck(2, time=datetime.combine(TODAY, time(9, 5)))  # delayed truck

    # Classify and assign packages
    priority_packages = identify_priority_packages(packages)
    truck_specific_packages = identify_truck_specific_packages(packages)
    deadline_packages = identify_deadline_packages(packages)
    delayed_packages = identify_delayed_packages(packages)
    package_to_group = map_packages_to_groups(package_group)
    critical_groups = identify_critical_groups(packages, package_group)

    # Load known constraints first
    load_truck_specific_packages(truck1, truck2, truck_specific_packages, package_to_group, packages)
    for group in critical_groups:
        load_group_to_truck(truck1, group, packages)

    load_priority_packages(truck1, priority_packages, package_to_group, packages)
    load_deadline_packages(truck1, deadline_packages, package_to_group, packages)
    load_delayed_packages(truck2, delayed_packages, package_to_group, packages)

    # Load unconstrained packages by proximity to current truck centers
    standard_packages = identify_standard_packages(
        packages,
        priority_packages,
        truck_specific_packages,
        deadline_packages,
        delayed_packages,
        package_group
    )
    load_by_proximity(truck1, truck2, standard_packages, packages, distance_matrix, address_map)

    # Execute or simulate routes
    if execute:
        truck1.set_route(optimizer.optimize(truck1, packages, distance_matrix, address_map, package_group))
        execute_route(truck1, packages, distance_matrix, address_map)

        truck2.set_route(optimizer.optimize(truck2, packages, distance_matrix, address_map, package_group))
        execute_route(truck2, packages, distance_matrix, address_map)

        # Handle undelivered packages (e.g., address correction)
        deliver_remaining_packages(truck1, truck2, packages, optimizer, distance_matrix, address_map, package_group)
    else:
        # Just plan routes and estimate mileage
        truck1.set_route(optimizer.optimize(truck1, packages, distance_matrix, address_map, package_group))
        truck2.set_route(optimizer.optimize(truck2, packages, distance_matrix, address_map, package_group))
        truck1.estimated_mileage = estimate_route_mileage(truck1.route, packages, distance_matrix, address_map)
        truck2.estimated_mileage = estimate_route_mileage(truck2.route, packages, distance_matrix, address_map)


    return packages, [truck1, truck2]


def deliver_remaining_packages(truck1, truck2, packages, optimizer, distance_matrix, address_map, package_group):
    """
    Handle remaining packages that were deferred or unavailable earlier.

    Use the truck that returned to the hub first, resets its time,
    and attempts to deliver remaining packages.
    """
    remaining_packages = [
        pid for pid in packages
        if packages.lookup(pid).status != STATUS_DELIVERED
    ]

    if not remaining_packages:
        return

    next_truck = truck1 if truck1.return_time <= truck2.return_time else truck2
    next_truck.time = next_truck.return_time

    for pid in remaining_packages:
        if next_truck.has_capacity():
            next_truck.load_package(packages.lookup(pid))

    if next_truck.cargo:
        next_truck.set_route(optimizer.optimize(next_truck, packages, distance_matrix, address_map, package_group))
        execute_route(next_truck, packages, distance_matrix, address_map)


def run_simulation_with_planning(optimizer, planning_iterations=20):
    """
    Run multiple simulations to find the lowest-mileage solution.

    Args:
        optimizer: Route optimization strategy to evaluate.
        planning_iterations: How many times to run simulations.

    Returns:
        Tuple of (best_packages, best_trucks) from the best run.
    """

    best_mileage = float("inf")
    best_result = None
    valid_runs = []

    for i in range(1, planning_iterations + 1):

        candidate_packages, candidate_trucks = run_simulation(
            optimizer, execute=True)

        total_mileage = sum(t.mileage for t in candidate_trucks)
        constraints_met = constraints_satisfied(candidate_packages, candidate_trucks)

        if constraints_met:
            valid_runs.append((i, total_mileage))

            if total_mileage < best_mileage:
                best_mileage = total_mileage
                best_result = (candidate_packages, candidate_trucks)

    if valid_runs:
        worst_run, worst_mileage = max(valid_runs, key=lambda x: x[1])
        best_run, _ = min(valid_runs, key=lambda x: x[1])
        avg_mileage = sum(m for _, m in valid_runs) / len(valid_runs)

        print("\n\nRoute planning complete!")
        print(f"Best solution (run {best_run}): {best_mileage:.2f} miles")
        print(f"Worst solution (run {worst_run}): {worst_mileage:.2f} miles")
        print(f"Average solution: {avg_mileage:.2f} miles")
        print(f"Mileage range: {worst_mileage - best_mileage:.2f} miles")
    else:
        print("\n\nNo valid solutions found!")
        return None

    print("\nGenerating final delivery report for optimal solution...")

    best_packages, best_trucks = best_result
    generate_summary_report(best_packages, best_trucks)

    return best_packages, best_trucks


def constraints_satisfied(packages, trucks):
    """
    Evaluate whether a simulation run met all constraints:
    - Deadline compliance
    - Truck-specific delivery

    Returns:
        bool: True if constraints passed.
    """
    all_deadlines_met = True
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.deadline_time and pkg.delivery_time and pkg.delivery_time > pkg.deadline_time:
            all_deadlines_met = False
            break

    all_trucks_respected = True
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.only_truck and pkg.truck_assigned != pkg.only_truck:
            all_trucks_respected = False
            break

    return all_deadlines_met and all_trucks_respected 

from wgups.utils import get_distance


def execute_route(truck, packages, distance_matrix, address_map, max_iterations=1000):
    """
    Execute the truck's delivery route, handling address corrections and deferrals.
    """
    location = "hub"
    i = 0

    while i < len(truck.route):
        pid = truck.route[i]
        pkg = packages.lookup(pid)

        if not pkg:
            i += 1
            continue

        # Wait for address correction if needed and it's soon
        if pkg.correction_time and truck.time < pkg.correction_time:
            time_to_correction = (pkg.correction_time - truck.time).total_seconds() / 3600
            if time_to_correction < 0.5:  # Less than 30 minutes
                truck._log_event(f"Waiting for address correction for Package {pid}")
                truck.time = pkg.correction_time

        # Deliver package (using corrected address if available)
        distance = get_distance(location, pkg.get_address(truck.time), distance_matrix, address_map)
        truck.deliver(pkg, distance)
        location = pkg.get_address(truck.time)
        i += 1

    # Return to hub after all deliveries
    return_distance = get_distance(location, "hub", distance_matrix, address_map)
    truck.drive(return_distance)
    truck.return_to_hub()


def estimate_route_mileage(route, packages, distance_matrix, address_map):
    """
    Estimate the total mileage of a delivery route without executing it.

    Args:
        route: List of package IDs
        packages: HashTable of Package objects
        distance_matrix: 2D list of distances between addresses
        address_map: Mapping of address string to index

    Returns:
        float: Total estimated miles including return to hub
    """
    total = 0.0
    loc = 'hub'
    for pid in route:
        pkg = packages.lookup(pid)
        dist = get_distance(loc, pkg.address, distance_matrix, address_map)
        total += dist
        loc = pkg.address
    total += get_distance(loc, 'hub', distance_matrix, address_map)
    return total

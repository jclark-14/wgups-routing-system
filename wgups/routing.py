from wgups.utils import get_distance

def execute_route(truck, packages, distance_matrix, address_map, max_iterations=1000):
    """
    Execute the truck's delivery route, handling address corrections and deferrals.

    Steps:
    - If a package has a corrected address not yet available, defer its delivery.
    - If the correction time is soon (<30 min), wait instead of deferring.
    - Avoid infinite loops by limiting the number of deferrals per package.
    - Deliver all packages, then return to the hub.

    Args:
        truck: Truck object with assigned route
        packages: HashTable of Package objects
        distance_matrix: 2D list of distances between addresses
        address_map: Mapping of address string to index
        max_iterations: Safety limit to prevent infinite loops

    Returns:
        None (updates truck mileage, time, and logs in-place)
    """
    location = "hub"
    i = 0
    iteration_count = 0

    while i < len(truck.route) and iteration_count < max_iterations:
        iteration_count += 1
        pid = truck.route[i]
        pkg = packages.lookup(pid)

        if not pkg:
            # Skip unknown packages
            i += 1
            continue

        # If address correction hasn't occurred yet
        if pkg.correction_time and truck.time < pkg.correction_time:
            time_to_correction = (pkg.correction_time - truck.time).total_seconds() / 3600

            if time_to_correction < 0.5:
                # Wait if correction is imminent (<30 min)
                truck._log_event(f"Waiting for address correction for Package {pid}")
                truck.time = pkg.correction_time
            else:
                # Defer this package by moving it to the end of the route
                pkg.defer_count = getattr(pkg, 'defer_count', 0) + 1
                if pkg.defer_count > 10:
                    # Prevent infinite loops by forcing delivery
                    truck._log_event(f"Force delivering Package {pid} after multiple deferrals")
                    i += 1
                else:
                    truck.route.pop(i)
                    truck.route.append(pid)
                    truck._log_event(
                        f"Deferring Package {pid} until address correction at {pkg.correction_time.strftime('%H:%M')}"
                    )
                    continue  # Skip increment to re-evaluate next package
        else:
            # Normal delivery
            distance = get_distance(location, pkg.get_address(truck.time), distance_matrix, address_map)
            truck.deliver(pkg, distance)
            location = pkg.get_address(truck.time)
            i += 1

    if iteration_count >= max_iterations:
        print(f"WARNING: Maximum iterations reached in execute_route for Truck {truck.truck_id}.")

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

from wgups.utils import get_distance

def execute_route(truck, packages, distance_matrix, address_map, max_iterations=1000):
    """Execute a truck's delivery route with proper handling of address corrections."""
    location = "hub"
    i = 0
    iteration_count = 0
    
    while i < len(truck.route) and iteration_count < max_iterations:
        iteration_count += 1
        pid = truck.route[i]
        pkg = packages.lookup(pid)
        
        # Skip non-existent packages
        if not pkg:
            i += 1
            continue
        
        # Handle packages with future address corrections
        if pkg.correction_time and truck.time < pkg.correction_time:
            time_to_correction = (pkg.correction_time - truck.time).total_seconds() / 3600
            
            if time_to_correction < 0.5:  # Within 30 minutes
                # Wait until correction time
                truck._log_event(f"Waiting for address correction for Package {pid}")
                truck.time = pkg.correction_time
            else:
                # Add safety counter to prevent infinite loops
                pkg.defer_count = getattr(pkg, 'defer_count', 0) + 1
                
                if pkg.defer_count > 10:  # Limit deferrals to prevent infinite loops
                    truck._log_event(f"Force delivering Package {pid} after multiple deferrals")
                    i += 1  # Process next package
                else:
                    truck.route.pop(i)
                    truck.route.append(pid)
                    truck._log_event(f"Deferring Package {pid} until address correction at {pkg.correction_time.strftime('%H:%M')}")
                    continue  # Don't increment i
        
        # Deliver the package
        distance = get_distance(location, pkg.get_address(truck.time), distance_matrix, address_map)
        truck.deliver(pkg, distance)
        location = pkg.get_address(truck.time)
        i += 1
    
    # Check if we hit max iterations
    if iteration_count >= max_iterations:
        print(f"WARNING: Maximum iterations reached in execute_route for Truck {truck.truck_id}.")
    
    # Return to hub
    return_distance = get_distance(location, "hub", distance_matrix, address_map)
    truck.drive(return_distance)
    truck.return_to_hub()
    
    
def estimate_route_mileage(route, packages, distance_matrix, address_map):
    """Estimate the mileage for a route without actually executing it."""
    total = 0.0
    loc = 'hub'
    for pid in route:
        pkg = packages.lookup(pid)
        dist = get_distance(loc, pkg.address, distance_matrix, address_map)
        total += dist
        loc = pkg.address
    # Return trip
    total += get_distance(loc, 'hub', distance_matrix, address_map)
    return total
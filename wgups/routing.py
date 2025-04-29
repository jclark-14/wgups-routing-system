from datetime import timedelta
from wgups.utils import get_distance

def execute_route(truck, packages, distance_matrix, address_map):
    """
    Execute a truck's delivery route with proper handling of address corrections.
    """
    location = "hub"
    i = 0
    
    while i < len(truck.route):
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
                # Move package to end of route
                truck.route.pop(i)
                truck.route.append(pid)
                truck._log_event(f"Deferring Package {pid} until address correction at {pkg.correction_time.strftime('%H:%M')}")
                continue  # Don't increment i
        
        # Deliver the package
        distance = get_distance(location, pkg.get_address(truck.time), distance_matrix, address_map)
        truck.deliver(pkg, distance)
        location = pkg.get_address(truck.time)
        i += 1
    
    # Return to hub
    return_distance = get_distance(location, "hub", distance_matrix, address_map)
    truck.drive(return_distance)
    truck.return_to_hub()
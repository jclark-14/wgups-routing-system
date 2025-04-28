from wgups.load_data import load_packages, load_distances
from wgups.models import Truck
from wgups.constraint_loader import ConstraintLoader
from wgups.routing_algorithms import random_route
from wgups.utils import get_distance, resolve_package_groups
from wgups.routing_utils import reorder_truck_route
from wgups.constants import STATUS_DELIVERED, START_TIME, DELAY_TRUCK_ID

def run_simulation(algorithm="random"):
    # Step 1: Load Data
    packages = load_packages()
    groups = resolve_package_groups(packages)
    distance_matrix, address_map = load_distances()
    trucks = [Truck(1), Truck(2), Truck(3)]

    # Step 2: Apply Constraints & Assign Packages
    loader = ConstraintLoader(packages, trucks, groups)
    loader.apply_hard_constraints()
    loader.set_delay_truck_departure()
    assignments = loader.get_initial_assignments()

    # Step 3: Route Optimization & Delivery Simulation
    for truck in trucks:
        if truck.truck_id != DELAY_TRUCK_ID:
            # Load available packages for Truck 1 & 2
            for pid in assignments[truck.truck_id]:
                pkg = packages.lookup(pid)
                if pkg.available_time <= truck.time:
                    truck.load_package(pkg)
        else:
            # Truck waits for delayed/corrected packages
            latest_time = max(
                [START_TIME] + [
                    max(pkg.available_time, pkg.correction_time or START_TIME)
                    for pid in assignments[truck.truck_id]
                    for pkg in [packages.lookup(pid)]
                ]
            )
            if truck.time < latest_time:
                print(f"\u23F3 Truck 3 waiting until {latest_time.strftime('%H:%M')} for delayed/corrected packages.")
                truck.time = latest_time

            for pid in assignments[truck.truck_id]:
                truck.load_package(packages.lookup(pid))

        # Route Planning
        random_route(truck, packages, distance_matrix, address_map)
        reorder_truck_route(truck, packages)

        # Delivery Simulation
        current_location = "hub"
        for package_id in truck.route:
            package = packages.lookup(package_id)
            next_address = package.get_address(truck.time)
            distance = get_distance(current_location, next_address, distance_matrix, address_map)
            truck.drive(distance)
            truck.deliver(package)
            current_location = next_address

        return_distance = get_distance(current_location, "hub", distance_matrix, address_map)
        truck.drive(return_distance)
        truck.return_to_hub()

    # Step 4: Generate Reports
    loader.generate_post_delivery_report()

    total_miles = sum(t.mileage for t in trucks)
    print(f"\nSimulation Complete!")
    for t in trucks:
        print(t)
    delivered = sum(1 for pkg_id in packages if packages.lookup(pkg_id).status == STATUS_DELIVERED)
    undelivered = len(packages) - delivered
    print(f"Total Mileage: {total_miles:.2f} miles")
    print(f"\nPackages Delivered: {delivered}")
    print(f"Packages Undelivered: {undelivered}")
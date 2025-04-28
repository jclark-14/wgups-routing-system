from datetime import timedelta, datetime
from wgups.utils import get_distance
from wgups.constants import START_TIME, EARLY_DEADLINE_CUTOFF, DELAY_TRUCK_ID

def simulate_delivery_time(truck, route, packages, distance_matrix, address_map):
    current_time = truck.time
    current_location = "hub"
    for pid in route:
        package = packages.lookup(pid)
        next_address = package.get_address(current_time)
        distance = get_distance(current_location, next_address, distance_matrix, address_map)
        travel_time_hours = distance / truck.speed
        current_time += timedelta(hours=travel_time_hours)
        current_location = next_address
    return current_time

def prioritize_delayed_deadlines(truck, packages):
    reorder_by_condition(
        truck,
        packages,
        condition=lambda pkg: pkg.available_time > START_TIME and pkg.deadline_time,
        label="🚨 Prioritized delayed deadlines"
    )

def handle_address_corrections(truck, packages):
    reorder_by_condition(
        truck,
        packages,
        condition=lambda pkg: pkg.correction_time is not None,
        label="🚨 Deferred address corrections",
        insert_front=False 
    )

def force_early_deadlines(truck, packages):
    reorder_by_condition(
        truck,
        packages,
        condition=lambda pkg: pkg.deadline_time and pkg.deadline_time.time() <= EARLY_DEADLINE_CUTOFF,
        label="🚨 Forced early deadlines to front"
    )
    
def reorder_truck_route(truck, packages):
    if truck.truck_id == DELAY_TRUCK_ID:
        prioritize_delayed_deadlines(truck, packages)
    else:
        force_early_deadlines(truck, packages)

    handle_address_corrections(truck, packages)

def reorder_by_condition(truck, packages, condition, label="", insert_front=True):
    selected = [pid for pid in truck.route if condition(packages.lookup(pid))]
    if not selected:
        return
    truck.route = [pid for pid in truck.route if pid not in selected]
    truck.route = (selected + truck.route) if insert_front else (truck.route + selected)
    truck.set_route(truck.route)
    if label:
        print(f"{label} on Truck {truck.truck_id}: {selected}")

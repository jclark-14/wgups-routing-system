import random
from typing import List
from wgups.models import Package, Truck
from wgups.constants import STATUS_AT_HUB
from wgups.hash_table import HashTable

def random_route(truck: Truck, packages: HashTable, distance_matrix, address_map) -> List[int]:
    delivery_route = truck.cargo.copy()

    # Soft-prioritize deadlines
    deadline_pkgs = [pid for pid in delivery_route if packages.lookup(pid).deadline_time]
    non_deadline_pkgs = [pid for pid in delivery_route if not packages.lookup(pid).deadline_time]

    random.shuffle(deadline_pkgs)
    random.shuffle(non_deadline_pkgs)

    prioritized_route = deadline_pkgs + non_deadline_pkgs
    truck.set_route(prioritized_route)
    return prioritized_route


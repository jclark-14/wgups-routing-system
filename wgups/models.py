import re
from datetime import datetime, timedelta
from typing import List, Optional
from wgups.utils import time_from_str, truck_from_note, normalize
from wgups.constants import STATUS_AT_HUB, STATUS_EN_ROUTE, STATUS_DELIVERED, START_TIME



class Package: 
    """Package object designed to track state as it moves through the program"""

    # Build Package class
    def __init__(
        self,
        package_id: int,
        address: str,
        city: str,
        state: str, 
        zip_code: str,
        deadline: str,
        weight: int, 
        note: str
    ):
        self.package_id = package_id
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.deadline = deadline
        self.weight = weight
        self.note = note.strip()
        # Dynamic state tracking
        self.status = STATUS_AT_HUB
        self.truck_assigned = None
        self.departure_time = None
        self.delivery_time = None
        # Constraint defaults
        self.available_time = START_TIME
        self.only_truck = None
        self.group_with = set()
        self.corrected_address = None
        self.correction_time = None
        # Original address when corrected
        self.original_address = address
        # Normalize deadline to None if EOD or datetime if specified
        if self.deadline.lower() == "eod":
            self.deadline_time = None
        else:
            self.deadline_time = time_from_str(deadline)
        self._parse_note()
        
    def _parse_note(self) -> None:
        note = self.note.lower()
        if "delayed" in note: 
            # Dynamically extract time if delayed, fallback to 9:05
            time = time_from_str(self.note)
            self.available_time = time if time else START_TIME + timedelta(minutes=65)
        if "truck" in note: 
            # Dynamically extract truck number from note
            truck = truck_from_note(self.note)
            if truck is not None:
                self.only_truck = truck
        if "wrong address" in note:
            self.corrected_address = "410 S State St"
            self.correction_time = START_TIME + timedelta(minutes=140)
        if "must be delivered with" in note:
            # Populate group_with with package ID's from note
            self.group_with = set(map(int, re.findall(r'\d+', note)))
            self.group_with.discard(self.package_id)
            
    def deliver(self, time: datetime) -> None:
        """Timestamp package delivery and state update"""
        self.status = STATUS_DELIVERED
        self.delivery_time = time
        
    def pickup(self, time: datetime, truck_id: int) -> None:
        """Update package state: status and truck assigned"""
        self.status = STATUS_EN_ROUTE
        self.truck_assigned = truck_id
        self.departure_time = time

    def get_address(self, time: Optional[datetime] = None) -> str:
        """Return corrected address if applicable, else original address"""
        if self.correction_time and time and time < self.correction_time:
            return normalize(self.original_address)
        return normalize(self.corrected_address) if self.corrected_address else normalize(self.address)
    
    def get_status(self, time: datetime) -> str: 
        """Get package status at given time"""
        if self.delivery_time and time >= self.delivery_time:
            return f"Delivered at {self.delivery_time.strftime('%H:%M')}"
        if self.departure_time and time >= self.departure_time:
            return f"En route on truck {self.truck_assigned}"
        return "At the hub"
    
    def __repr__(self):
        return f"<Package {self.package_id} | Status: {self.status}>"

class Truck:
    """WGUPS Delivery truck model"""
    
    def __init__(self, truck_id: int, time: datetime = START_TIME, capacity: int = 16):
        self.truck_id           = truck_id
        self.time               = time
        self.speed: float       = 18.0
        self.capacity           = capacity
        self.cargo: List[int]   = []
        self.mileage: float     = 0.0
        self.location: str      = "hub"
        self.route: List[int]   = []
        self.status: str        = STATUS_AT_HUB
        
    def load_package(self, package: Package) -> bool:
        """Tries to load a package onto the truck if there is room"""
        if len(self.cargo) >= self.capacity:
            return False
        self.cargo.append(package.package_id)
        package.pickup(self.time, self.truck_id)
        return True
        
    def set_route(self, route: List[int]) -> None:
        """Assigns delivery route to the truck"""
        self.route = route
        self.status = STATUS_EN_ROUTE
        
    def drive(self, distance: float) -> None:
        """Drives the truck a distance, updates mileage and time"""
        self.mileage += distance
        travel_time_hours = distance / self.speed
        self.time += timedelta(hours=travel_time_hours)
        
    def deliver(self, package: Package) -> None:
        """Delivers a package, updates package status"""
        package.deliver(self.time)
        if package.package_id in self.cargo:
            self.cargo.remove(package.package_id)
    
    def return_to_hub(self) -> None:
        """Returns the truck to the hub and updates truck status"""
        self.location = "hub"
        self.status = STATUS_AT_HUB

    def __repr__(self):
        return f"<Truck {self.truck_id} | Status: {self.status} | Mileage: {self.mileage:.1f} mi | Cargo: {len(self.cargo)} pkgs>"

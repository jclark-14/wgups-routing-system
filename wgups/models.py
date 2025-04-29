import re
from datetime import datetime, timedelta
from typing import List, Optional
from wgups.utils import time_from_str, truck_from_note, normalize_address
from wgups.constants import STATUS_AT_HUB, STATUS_EN_ROUTE, STATUS_DELIVERED, START_TIME

class Package:
    """Package object with all delivery data and constraints."""
    
    def __init__(self, package_id, address, city, state, zip_code, deadline, weight, note):
        # Basic package information
        self.package_id = package_id
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.deadline = deadline
        self.weight = weight
        self.note = note.strip()
        
        # Track delivery status
        self.status = STATUS_AT_HUB
        self.truck_assigned = None
        self.departure_time = None
        self.delivery_time = None
        
        # Constraints
        self.available_time = START_TIME  # Default available time
        self.only_truck = None  # Specific truck requirement
        self.group_with = set()  # Must be delivered with these packages
        self.corrected_address = None
        self.correction_time = None
        self.original_address = address
        
        # Parse deadline
        if self.deadline.lower() == "eod":
            self.deadline_time = None
        else:
            self.deadline_time = time_from_str(deadline)
            
        # Parse special instructions from notes
        self._parse_note()
    
    def _parse_note(self) -> None:
        """Parse package notes to extract constraints."""
        note = self.note.lower()
        
        # Handle delayed packages
        if "delayed" in note:
            time = time_from_str(self.note)
            self.available_time = time if time else START_TIME + timedelta(minutes=65)
        
        # Handle truck-specific packages
        if "truck" in note:
            truck = truck_from_note(self.note)
            if truck is not None:
                self.only_truck = truck
        
        # Handle address corrections
        if "wrong address" in note:
            self.corrected_address = "410 S State St"
            self.correction_time = START_TIME + timedelta(minutes=140)  # 10:20 AM
        
        # Handle package groups
        if "must be delivered with" in note:
            self.group_with = set(map(int, re.findall(r'\d+', note)))
            self.group_with.discard(self.package_id)
    
    def deliver(self, time: datetime) -> None:
        """Mark package as delivered at the given time."""
        self.status = STATUS_DELIVERED
        self.delivery_time = time
    
    def pickup(self, time: datetime, truck_id: int) -> None:
        """Mark package as picked up by a truck."""
        self.status = STATUS_EN_ROUTE
        self.truck_assigned = truck_id
        self.departure_time = time
    
    def get_address(self, time: Optional[datetime] = None) -> str:
        """Get correct address based on time (for address correction)."""
        if self.correction_time and time and time < self.correction_time:
            return normalize_address(self.original_address)
        return normalize_address(self.corrected_address or self.address)
    
    def get_status(self, time: datetime) -> str:
        """Get package status at a specific time."""
        if self.delivery_time and time >= self.delivery_time:
            return f"Delivered at {self.delivery_time.strftime('%H:%M')}"
        if self.departure_time and time >= self.departure_time:
            return f"En route on truck {self.truck_assigned}"
        return "At the hub"
    
    def __repr__(self):
        return (f"<Package {self.package_id}: "
                f"{self.get_address()} | "
                f"Deadline: {self.deadline or 'EOD'} | "
                f"Status: {self.status}>")


class Truck:
    """Delivery truck with packages and routing capabilities."""
    
    def __init__(self, truck_id: int, time: datetime = START_TIME, capacity: int = 16):
        self.truck_id = truck_id
        self.time = time
        self.speed = 18.0  # miles per hour
        self.capacity = capacity
        self.cargo = []  # Package IDs currently loaded
        self.mileage = 0.0  # Total miles driven
        self.location = "hub"
        self.route = []  # Planned delivery order
        self.status = STATUS_AT_HUB
        self.return_time = None  # When truck returns to hub
        self.log = []  # Activity log
        
        self._log_event(f"Truck {self.truck_id} initialized at {self.time.strftime('%H:%M')} with capacity {self.capacity}")
    
    def _log_event(self, message: str) -> None:
        """Add an entry to the truck's activity log."""
        if message.startswith("Route assigned"):
            tag = "🗺️ "
        elif "Delivered Package" in message:
            tag = "📦 "
        elif message.startswith("Returned"):
            tag = "🏁 "
        else:
            tag = "— "
        self.log.append(f"[{self.time.strftime('%H:%M')}] {tag}{message}")
    
    def load_package(self, package: 'Package') -> bool:
        """Load a package onto the truck if capacity allows."""
        if len(self.cargo) >= self.capacity:
            self._log_event(f"Failed to load Package {package.package_id}: Capacity full")
            return False
        self.cargo.append(package.package_id)
        package.pickup(self.time, self.truck_id)
        return True
    
    def set_route(self, route: List[int]) -> None:
        """Set the delivery route for this truck."""
        self.route = route
        self.status = STATUS_EN_ROUTE
        self._log_event(f"Route assigned: {route}")
    
    def drive(self, distance: float) -> None:
        """Drive the truck a specified distance."""
        self.mileage += distance
        travel_time_hours = distance / self.speed
        self.time += timedelta(hours=travel_time_hours)
        self._log_event(f"Drove {distance:.2f} miles. Total mileage: {self.mileage:.2f}")
        
    
    def deliver(self, package: 'Package', distance: float) -> None:
        """Drive to a location and deliver a package."""
        self.mileage += distance
        travel_time_hours = distance / self.speed
        self.time += timedelta(hours=travel_time_hours)
        package.deliver(self.time)
        if package.package_id in self.cargo:
            self.cargo.remove(package.package_id)
        self._log_event(f"Drove {distance:.2f} miles, Delivered Package {package.package_id} (Total mileage: {self.mileage:.2f})")
    
    def return_to_hub(self) -> None:
        """Return the truck to the hub."""
        self.location = "hub"
        self.status = STATUS_AT_HUB
        self.return_time = self.time
        self._log_event("Returned to hub")
    
    def has_capacity(self) -> bool:
        """Check if the truck has remaining capacity."""
        return len(self.cargo) < self.capacity
    
    def print_log(self) -> None:
        """Print the truck's activity log."""
        print(f"\n📜 Activity Log for Truck {self.truck_id}:")
        for entry in self.log:
            print(entry)
            
    def __repr__(self):
        return (f"<Truck {self.truck_id}: "
                f"Time {self.time.strftime('%H:%M')}, "
                f"Mileage {self.mileage:.2f} mi, "
                f"Cargo {len(self.cargo)} packages>")

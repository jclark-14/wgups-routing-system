import re
from datetime import datetime, timedelta
from typing import List, Optional
from wgups.utils import time_from_str, truck_from_note, normalize_address
from wgups.constants import STATUS_AT_HUB, STATUS_EN_ROUTE, STATUS_DELIVERED, START_TIME

class Package:
    """
    Represents a single package with delivery metadata, constraints, and dynamic state tracking.
    """

    def __init__(self, package_id, address, city, state, zip_code, deadline, weight, note):
        # Static package info
        self.package_id = package_id
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.deadline = deadline
        self.weight = weight
        self.note = note.strip()

        # Dynamic delivery state
        self.status = STATUS_AT_HUB
        self.truck_assigned = None
        self.departure_time = None
        self.delivery_time = None

        # Constraints
        self.available_time = START_TIME
        self.only_truck = None
        self.group_with = set()
        self.corrected_address = None
        self.correction_time = None
        self.original_address = address

        # Parse delivery deadline
        self.deadline_time = None if deadline.lower() == "eod" else time_from_str(deadline)

        # Extract constraints from special instructions
        self._parse_note()

    def _parse_note(self) -> None:
        """Interpret package note field for delivery constraints."""
        note = self.note.lower()

        if "delayed" in note:
            self.available_time = time_from_str(self.note) or START_TIME + timedelta(minutes=65)

        if "truck" in note:
            self.only_truck = truck_from_note(self.note)

        if "wrong address" in note:
            self.corrected_address = "410 S State St"
            self.correction_time = START_TIME + timedelta(minutes=140)  # 10:20 AM

        if "must be delivered with" in note:
            self.group_with = set(map(int, re.findall(r'\d+', note)))
            self.group_with.discard(self.package_id)

    def deliver(self, time: datetime) -> None:
        """Mark the package as delivered."""
        self.status = STATUS_DELIVERED
        self.delivery_time = time

    def pickup(self, time: datetime, truck_id: int) -> None:
        """Mark the package as picked up by a specific truck."""
        self.status = STATUS_EN_ROUTE
        self.truck_assigned = truck_id
        self.departure_time = time

    def get_address(self, time: Optional[datetime] = None) -> str:
        """
        Return the corrected address if correction time has passed.
        Otherwise, return the original.
        """
        if self.correction_time and time and time < self.correction_time:
            return normalize_address(self.original_address)
        return normalize_address(self.corrected_address or self.address)

    def get_status(self, time: datetime) -> str:
        """Return a human-readable status at a given time."""
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
    """
    Represents a delivery truck responsible for transporting and delivering packages.
    """

    def __init__(self, truck_id: int, time: datetime = START_TIME, capacity: int = 16):
        self.truck_id = truck_id
        self.time = time
        self.speed = 18.0  # mph
        self.capacity = capacity

        self.cargo = []  # Package IDs currently on board
        self.mileage = 0.0
        self.location = "hub"
        self.route = []
        self.status = STATUS_AT_HUB
        self.return_time = None
        self.log = []

        self._log_event(f"Truck {self.truck_id} initialized at {self.time.strftime('%H:%M')} with capacity {self.capacity}")

    def _log_event(self, message: str) -> None:
        """Record a timestamped event in the truck's activity log."""
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
        """Attempt to load a package onto the truck."""
        if len(self.cargo) >= self.capacity:
            self._log_event(f"Failed to load Package {package.package_id}: Capacity full")
            return False

        self.cargo.append(package.package_id)
        package.pickup(self.time, self.truck_id)
        return True

    def set_route(self, route: List[int]) -> None:
        """Assign a delivery route."""
        self.route = route
        self.status = STATUS_EN_ROUTE
        self._log_event(f"Route assigned: {route}")

    def drive(self, distance: float) -> None:
        """Drive a given distance and update truck time and mileage."""
        self.mileage += distance
        travel_time_hours = distance / self.speed
        self.time += timedelta(hours=travel_time_hours)
        self._log_event(f"Drove {distance:.2f} miles. Total mileage: {self.mileage:.2f}")

    def deliver(self, package: 'Package', distance: float) -> None:
        """
        Deliver a package and log the journey.

        This advances time, updates mileage, marks the package as delivered,
        and removes it from cargo.
        """
        self.mileage += distance
        travel_time_hours = distance / self.speed
        self.time += timedelta(hours=travel_time_hours)
        package.deliver(self.time)

        if package.package_id in self.cargo:
            self.cargo.remove(package.package_id)

        self._log_event(f"Drove {distance:.2f} miles, Delivered Package {package.package_id} (Total mileage: {self.mileage:.2f})")

    def return_to_hub(self) -> None:
        """Return the truck to the hub and update status."""
        self.location = "hub"
        self.status = STATUS_AT_HUB
        self.return_time = self.time
        self._log_event("Returned to hub")

    def has_capacity(self) -> bool:
        """Check if there is space remaining for additional packages."""
        return len(self.cargo) < self.capacity

    def print_log(self) -> None:
        """Print a human-readable delivery log."""
        print(f"\n📜 Activity Log for Truck {self.truck_id}:")
        for entry in self.log:
            print(entry)

    def __repr__(self):
        return (f"<Truck {self.truck_id}: "
                f"Time {self.time.strftime('%H:%M')}, "
                f"Mileage {self.mileage:.2f} mi, "
                f"Cargo {len(self.cargo)} packages>")

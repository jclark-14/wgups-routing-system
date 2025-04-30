import unittest
from datetime import timedelta
from wgups.models import Package
from wgups.constants import START_TIME, STATUS_AT_HUB, STATUS_DELIVERED, STATUS_EN_ROUTE
from wgups.utils import normalize_address

class TestPackage(unittest.TestCase):

    def setUp(self):
        self.pkg = Package(
            package_id=1,
            address="123 Main St",
            city="Cityville",
            state="UT",
            zip_code="12345",
            deadline="10:30 AM",
            weight=5,
            note=""
        )

    def test_initial_status(self):
        self.assertEqual(self.pkg.status, STATUS_AT_HUB)

    def test_pickup_updates_status(self):
        pickup_time = START_TIME + timedelta(minutes=30)
        self.pkg.pickup(pickup_time, truck_id=2)
        self.assertEqual(self.pkg.status, STATUS_EN_ROUTE)
        self.assertEqual(self.pkg.truck_assigned, 2)
        self.assertEqual(self.pkg.departure_time, pickup_time)

    def test_deliver_updates_status(self):
        delivery_time = START_TIME + timedelta(hours=1)
        self.pkg.deliver(delivery_time)
        self.assertEqual(self.pkg.status, STATUS_DELIVERED)
        self.assertEqual(self.pkg.delivery_time, delivery_time)

    def test_get_status_logic(self):
            now = START_TIME + timedelta(minutes=20)
            self.assertEqual(self.pkg.get_status(now), "At the hub")

            self.pkg.pickup(now, truck_id=1)
            self.assertEqual(self.pkg.get_status(now + timedelta(minutes=5)), "En route on truck 1")

            delivery_time = now + timedelta(minutes=30)
            self.pkg.deliver(delivery_time)
            self.assertEqual(self.pkg.get_status(delivery_time + timedelta(minutes=1)),
                            f"Delivered at {delivery_time.strftime('%H:%M')}")

    def test_get_address_correction(self):
        # Simulate wrong address
        self.pkg.corrected_address = "410 S State St"
        self.pkg.correction_time = START_TIME + timedelta(hours=2)

        before_correction = START_TIME + timedelta(minutes=30)
        after_correction = START_TIME + timedelta(hours=3)

        self.assertEqual(self.pkg.get_address(before_correction), normalize_address(self.pkg.original_address))
        self.assertEqual(self.pkg.get_address(after_correction), normalize_address("410 S State St"))

if __name__ == '__main__':
    unittest.main()

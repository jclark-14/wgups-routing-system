import unittest
from datetime import timedelta
from wgups.models import Truck, Package
from wgups.utils import STATUS_AT_HUB, STATUS_EN_ROUTE, STATUS_DELIVERED

class TestTruck(unittest.TestCase):

    def setUp(self):
        self.truck = Truck(truck_id=1)
        self.package = Package(
            package_id=1,
            address="123 main st",
            city="Salt Lake City",
            state="UT",
            zip_code="84101",
            deadline="EOD",
            weight=10,
            note=""
        )

    def test_load_package_success(self):
        result = self.truck.load_package(self.package)
        self.assertTrue(result)
        self.assertIn(self.package.package_id, self.truck.cargo)
        self.assertEqual(self.package.status, STATUS_EN_ROUTE)

    def test_load_package_exceeds_capacity(self):
        self.truck.capacity = 1
        self.truck.load_package(self.package)
        pkg2 = Package(2, "addr", "city", "UT", "84101", "EOD", 5, "")
        result = self.truck.load_package(pkg2)
        self.assertFalse(result)

    def test_drive_updates_mileage_and_time(self):
        initial_time = self.truck.time
        self.truck.drive(18.0)
        self.assertAlmostEqual(self.truck.mileage, 18.0)
        self.assertEqual(self.truck.time, initial_time + timedelta(hours=1))

    def test_deliver_package(self):
        self.truck.load_package(self.package)
        self.truck.deliver(self.package)
        self.assertEqual(self.package.status, STATUS_DELIVERED)
        self.assertNotIn(self.package.package_id, self.truck.cargo)

    def test_return_to_hub(self):
        self.truck.status = STATUS_EN_ROUTE
        self.truck.location = "Somewhere"
        self.truck.return_to_hub()
        self.assertEqual(self.truck.status, STATUS_AT_HUB)
        self.assertEqual(self.truck.location, "hub")

    def test_repr(self):
        repr_str = repr(self.truck)
        self.assertIn(f"Truck {self.truck.truck_id}", repr_str)

if __name__ == "__main__":
    unittest.main()

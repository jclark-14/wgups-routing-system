import unittest
from wgups.optimizer_core import nearest_neighbor, apply_2opt
from wgups.entities import Package, Truck
from wgups.data_structures import HashTable

class TestRoutingAlgorithms(unittest.TestCase):
    def setUp(self):
        self.truck = Truck(1)
        self.packages = HashTable()

        # Distance matrix:
        # hub (0), a (1), b (2)
        self.distance_matrix = [
            [0.0, 2.0, 4.0],
            [2.0, 0.0, 1.0],
            [4.0, 1.0, 0.0]
        ]

        self.address_map = {
            "hub": 0,
            "a": 1,
            "b": 2
        }

        # Create two simple packages
        p1 = Package(1, "a", "City", "ST", "00000", "EOD", 1, "")
        p2 = Package(2, "b", "City", "ST", "00000", "EOD", 1, "")

        self.packages.insert(1, p1)
        self.packages.insert(2, p2)

        self.truck.load_package(p1)
        self.truck.load_package(p2)
        self.packages.truck = self.truck

    def test_nearest_neighbor_returns_valid_route(self):
        pids = self.truck.cargo
        route = nearest_neighbor(
            pids, self.packages, self.distance_matrix, self.address_map
        )

        self.assertEqual(set(route), {1, 2})
        self.assertEqual(len(route), 2)

    def test_apply_2opt_does_not_change_short_route(self):
        original_route = [1, 2]
        optimized = apply_2opt(
            original_route.copy(), self.packages, self.distance_matrix, self.address_map
        )
        self.assertEqual(set(optimized), set(original_route))
        self.assertEqual(len(optimized), 2)

if __name__ == "__main__":
    unittest.main()

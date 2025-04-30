import unittest
from wgups.data_loader import load_packages, load_distances
from wgups.data_structures import HashTable
from wgups.models import Package
from wgups.constants import START_TIME

class TestLoadPackagesRealFile(unittest.TestCase):

    def test_loads_all_packages(self):
        packages: HashTable = load_packages("data/packages.csv")
        self.assertEqual(len(packages), 40)

    def test_specific_package_attributes(self):
        packages: HashTable = load_packages("data/packages.csv")
        pkg3 = packages.lookup(3)
        self.assertIsInstance(pkg3, Package)
        self.assertTrue(pkg3.city)
        self.assertTrue(pkg3.weight > 0)


    def test_delayed_package(self):
        packages: HashTable = load_packages("data/packages.csv")
        delayed_pkg = packages.lookup(6) 
        self.assertIsNotNone(delayed_pkg)
        self.assertGreater(delayed_pkg.available_time, START_TIME)

class TestLoadDistances(unittest.TestCase):

    def setUp(self):
        # Load real CSV; assumes distances.csv is correct
        self.matrix, self.addr_map = load_distances("data/distances.csv")

    def test_address_map_size(self):
        """Ensure correct number of unique addresses loaded."""
        expected_addresses = 27 
        self.assertEqual(len(self.addr_map), expected_addresses, "Address map size mismatch.")

    def test_matrix_dimensions(self):
        """Matrix should be square and match address count."""
        size = len(self.matrix)
        self.assertEqual(size, len(self.matrix[0]), "Matrix is not square.")
        self.assertEqual(size, len(self.addr_map), "Matrix size doesn't match address map.")

    def test_symmetric_matrix(self):
        """Ensure matrix is symmetric (distance A->B == B->A)."""
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix)):
                self.assertEqual(self.matrix[i][j], self.matrix[j][i], f"Matrix not symmetric at [{i}][{j}]")
                
if __name__ == "__main__":
    unittest.main()
import unittest
from wgups.load_data import load_packages
from wgups.hash_table import HashTable
from wgups.models import Package
from wgups.utils import START_TIME

class TestLoadPackagesRealFile(unittest.TestCase):

    def test_loads_all_packages(self):
        packages: HashTable = load_packages("data/packages.csv")
        self.assertEqual(len(packages), 40)

    def test_specific_package_attributes(self):
        packages: HashTable = load_packages("data/packages.csv")
        pkg3 = packages.lookup(3)
        self.assertIsInstance(pkg3, Package)
        self.assertEqual(pkg3.city, "Salt Lake City")
        self.assertEqual(pkg3.weight, 2)
        self.assertEqual(pkg3.only_truck, 2)

    def test_delayed_package(self):
        packages: HashTable = load_packages("data/packages.csv")
        delayed_pkg = packages.lookup(6) 
        self.assertIsNotNone(delayed_pkg)
        self.assertGreater(delayed_pkg.available_time, START_TIME)

if __name__ == "__main__":
    unittest.main()

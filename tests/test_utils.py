import unittest
from wgups.utils import normalize_address, time_from_str, truck_from_note, resolve_package_groups
from wgups.entities import Package
from wgups.data_structures import HashTable

class TestNormalizeAddress(unittest.TestCase):

    def test_directional_replacement(self):
        self.assertEqual(normalize_address("410 South State St"), "410 s state st")
        self.assertEqual(normalize_address("5383 South 900 East #104"), "5383 s 900 e #104")
        self.assertEqual(normalize_address("300 North Main St."), "300 n main st")

    def test_removes_newlines_and_parentheses(self):
        raw = "1060 Dalton Ave S\n(84104)"
        self.assertEqual(normalize_address(raw), "1060 dalton ave s")

    def test_handles_extra_spaces(self):
        raw = "  410   South   State   St   "
        self.assertEqual(normalize_address(raw), "410 s state st")
        
    def test_special_case_hub(self):
        self.assertEqual(normalize_address("WGU"), "hub")
        self.assertEqual(normalize_address("Hub"), "hub")
        self.assertEqual(normalize_address("WGUPS"), "hub")
class TestTimeFromStr(unittest.TestCase):

    def test_valid_am_time(self):
        note = "Delayed on flight—will not arrive until 9:05 AM"
        result = time_from_str(note)
        self.assertIsNotNone(result)
        self.assertEqual(result.strftime("%H:%M"), "09:05")

    def test_valid_pm_time(self):
        note = "Delayed until 1:45 PM"
        result = time_from_str(note)
        self.assertIsNotNone(result)
        self.assertEqual(result.strftime("%H:%M"), "13:45")

    def test_24hr_format(self):
        note = "Delayed until 13:30"
        result = time_from_str(note)
        self.assertIsNotNone(result)
        self.assertEqual(result.strftime("%H:%M"), "13:30")

    def test_no_time_found(self):
        note = "On truck 2, no delay"
        self.assertIsNone(time_from_str(note))
        
class TestTruckFromNote(unittest.TestCase):

    def test_truck_2(self):
        note = "Must be delivered on truck 2"
        self.assertEqual(truck_from_note(note), 2)

    def test_truck_1(self):
        note = "Assigned to truck 1"
        self.assertEqual(truck_from_note(note), 1)

    def test_no_truck(self):
        note = "Delayed on flight—no truck assigned"
        self.assertIsNone(truck_from_note(note))
        
class TestResolvePackageGroups(unittest.TestCase):

    def test_transitive_grouping(self):
        packages = HashTable()
        a = Package(1, "A", "City", "ST", "11111", "EOD", 1, "Must be delivered with 2")
        b = Package(2, "B", "City", "ST", "11111", "EOD", 1, "Must be delivered with 3")
        c = Package(3, "C", "City", "ST", "11111", "EOD", 1, "")

        packages.insert(1, a)
        packages.insert(2, b)
        packages.insert(3, c)

        groups = resolve_package_groups(packages)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0], {1, 2, 3})

    def test_disjoint_groups(self):
        packages = HashTable()
        p1 = Package(1, "Addr", "City", "ST", "11111", "EOD", 1, "Must be delivered with 2")
        p2 = Package(2, "Addr", "City", "ST", "11111", "EOD", 1, "")
        p3 = Package(3, "Addr", "City", "ST", "11111", "EOD", 1, "Must be delivered with 4")
        p4 = Package(4, "Addr", "City", "ST", "11111", "EOD", 1, "")

        packages.insert(1, p1)
        packages.insert(2, p2)
        packages.insert(3, p3)
        packages.insert(4, p4)

        groups = resolve_package_groups(packages)
        self.assertEqual(len(groups), 1)
        self.assertTrue({1, 2} in groups or {3, 4} in groups)

if __name__ == "__main__":
    unittest.main()

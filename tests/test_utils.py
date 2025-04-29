import unittest
from wgups.utils import normalize

class TestNormalizeAddress(unittest.TestCase):

    def test_directional_replacement(self):
        self.assertEqual(normalize("410 South State St"), "410 s state st")
        self.assertEqual(normalize("5383 South 900 East #104"), "5383 s 900 e #104")
        self.assertEqual(normalize("300 North Main St."), "300 n main st")

    def test_removes_newlines_and_parentheses(self):
        raw = "1060 Dalton Ave S\n(84104)"
        self.assertEqual(normalize(raw), "1060 dalton ave s")

    def test_handles_extra_spaces(self):
        raw = "  410   South   State   St   "
        self.assertEqual(normalize(raw), "410 s state st")

if __name__ == "__main__":
    unittest.main()

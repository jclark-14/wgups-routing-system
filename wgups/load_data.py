import csv
from datetime import datetime
from wgups.hash_table import HashTable
from wgups.models import Package

def load_packages(filepath: str = "data/packages.csv") -> HashTable:
    """Load package data from file into hash table."""
    packages = HashTable()
    # Extract data from packages.csv
    with open(filepath, encoding="utf-8-sig") as f:
        # Skip empty rows and header row
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            if "Package" in row[0]:
                continue
            # Assign package_id, skip malformed rows
            try:
                package_id = int(row[0])
            except (ValueError, IndexError):
                continue   
            address     = row[1].strip()
            city        = row[2].strip()
            state       = row[3].strip()
            zip_code    = row[4].strip()
            deadline    = row[5].strip()
            weight      = int(row[6].strip())
            note        = row[7].strip() if len(row) > 7 else ""
            # Build package object and Hash table
            package = Package(
                package_id  = int(package_id),
                address     = address,
                city        = city,
                state       = state,
                zip_code    = zip_code,
                deadline    = deadline,
                weight      = int(weight),
                note        = note
            )
            packages.insert(int(package_id), package)
    return packages

# def _normalize(addr: str) -> str:
#         """Normalize address string."""
#         return " ".join(addr.lower().split())
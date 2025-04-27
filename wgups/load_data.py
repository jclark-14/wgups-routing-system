import csv
from datetime import datetime
from typing import List, Tuple, Dict
from wgups.hash_table import HashTable
from wgups.models import Package
from wgups.utils import normalize

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
                address     = normalize(address),
                city        = city,
                state       = state,
                zip_code    = zip_code,
                deadline    = deadline,
                weight      = int(weight),
                note        = note
            )
            packages.insert(int(package_id), package)
    return packages

def load_distances(filepath: str = "data/distances.csv") -> Tuple[List[List[float]], Dict[str, int]]:
    address_map = {}
    matrix = []
    #Build address map and distance_matrix from distances.csv
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            #Skip empty rows
            if not row or not row[0].strip():
                continue
            # Normalize address and build address map
            address = normalize(row[0])
            address_map[address] = idx
            # Build matrix row from csv
            distances= []
            for val in row[1:]:
                try:
                    distances.append(float(val))
                except ValueError:
                    distances.append(0.0)
            # Add distance row to matrix
            matrix.append(distances)
    # Build full symmetric matrix   
    size = len(matrix)
    distance_matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    for i in range(size):
        for j in range(i + 1):
            distance_matrix[i][j] = matrix[i][j]
            distance_matrix[j][i] = matrix[i][j]
    return distance_matrix, address_map
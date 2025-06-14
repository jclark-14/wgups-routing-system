import csv
from typing import Tuple, List, Dict
from wgups.data_structures import HashTable
from wgups.entities import Package
from wgups.utils import normalize_address

def load_packages(filepath: str = "data/packages.csv") -> HashTable:
    """
    Load package data from a CSV file into a hash table.

    Returns:
        HashTable: All packages keyed by their package ID.
    """
    packages = HashTable()
    
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or "Package" in row[0]:
                continue  # Skip headers or empty rows
            
            try:
                package_id = int(row[0])
            except (ValueError, IndexError):
                continue  # Skip rows with bad IDs
            
            # Parse and normalize package fields
            address = row[1].strip()
            city = row[2].strip()
            state = row[3].strip()
            zip_code = row[4].strip()
            deadline = row[5].strip()
            weight = int(row[6].strip())
            note = row[7].strip() if len(row) > 7 else ""
            
            # Construct and store the package
            package = Package(
                package_id=package_id,
                address=normalize_address(address),
                city=city,
                state=state,
                zip_code=zip_code,
                deadline=deadline,
                weight=weight,
                note=note
            )
            packages.insert(package_id, package)
    
    return packages

def load_distances(filepath: str = "data/distances.csv") -> Tuple[List[List[float]], Dict[str, int]]:
    """
    Load distance matrix and address map from CSV.

    Returns:
        Tuple[List[List[float]], Dict[str, int]]:
            - Symmetric distance matrix (2D list)
            - Normalized address-to-index map
    """
    address_map = {}
    distance_rows = []
    
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            if not row or not row[0].strip():
                continue  # Skip empty or malformed rows

            address = normalize_address(row[0])
            address_map[address] = idx

            # Convert distances to float, use 0.0 for blanks
            distances = []
            for val in row[1:]:
                try:
                    distances.append(float(val))
                except ValueError:
                    distances.append(0.0)

            distance_rows.append(distances)
    
    # Build symmetric matrix from upper triangular input
    size = len(distance_rows)
    distance_matrix = [[0.0 for _ in range(size)] for _ in range(size)]

    for i in range(size):
        for j in range(i + 1):
            distance_matrix[i][j] = distance_rows[i][j]
            distance_matrix[j][i] = distance_rows[i][j]  # Fill symmetric half

    return distance_matrix, address_map

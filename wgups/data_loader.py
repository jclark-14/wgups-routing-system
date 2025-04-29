# data_loader.py

import csv
from datetime import datetime
from typing import Tuple, List, Dict
from wgups.data_structures import HashTable
from wgups.models import Package
from wgups.utils import normalize_address

def load_packages(filepath: str = "data/packages.csv") -> HashTable:
    """
    Load package data from CSV file into hash table.
    Returns a HashTable containing all packages.
    """
    packages = HashTable()
    
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip empty or header rows
            if not row or "Package" in row[0]:
                continue
                
            try:
                package_id = int(row[0])
            except (ValueError, IndexError):
                continue
                
            # Extract package data
            address = row[1].strip()
            city = row[2].strip()
            state = row[3].strip()
            zip_code = row[4].strip()
            deadline = row[5].strip()
            weight = int(row[6].strip())
            note = row[7].strip() if len(row) > 7 else ""
            
            # Create package object
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
            
            # Insert into hash table
            packages.insert(package_id, package)
            
    return packages

def load_distances(filepath: str = "data/distances.csv") -> Tuple[List[List[float]], Dict[str, int]]:
    """
    Load distance data from CSV file.
    Returns a tuple (distance_matrix, address_map).
    """
    address_map = {}
    distance_rows = []
    
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            # Skip empty rows
            if not row or not row[0].strip():
                continue
                
            # Map address to index
            address = normalize_address(row[0])
            address_map[address] = idx
            
            # Parse distances
            distances = []
            for val in row[1:]:
                try:
                    distances.append(float(val))
                except ValueError:
                    distances.append(0.0)
                    
            distance_rows.append(distances)
    
    # Build symmetric distance matrix
    size = len(distance_rows)
    distance_matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    
    for i in range(size):
        for j in range(i + 1):
            distance_matrix[i][j] = distance_rows[i][j]
            distance_matrix[j][i] = distance_rows[i][j]  # Make symmetric
            
    return distance_matrix, address_map
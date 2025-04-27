# 📦 WGUPS Package Routing Program

![Python](https://img.shields.io/badge/python-3.x-blue)

**Western Governors University — C950 DSA2 Project**

A command-line based package delivery system that optimizes delivery routes using custom data structures and routing algorithms. This program leverages a hash table for efficient package management and implements Nearest Neighbor with 2-Opt optimization for route planning.

---

## 🚀 Features

- **Custom Hash Table** for O(1) average-time package lookups.
- **Dynamic Package State Tracking** (`At Hub`, `En Route`, `Delivered`).
- **CSV Data Loaders** for packages and distances.
- **Constraint Handling**:
  - Delayed packages.
  - Truck-specific assignments.
  - Group delivery requirements.
  - Address corrections after departure.
- **Routing Optimization**:
  - Nearest Neighbor (NN) algorithm.
  - 2-Opt improvement pass.
- **CLI Interface** for querying package status, total mileage, and more.
- **Unit Tests** for core components (Package model, Data Loaders, Hash Table).

---

## ⚙️ How to Run

> Requires **Python 3.x**  
> No external libraries needed.

1. Clone the repository:
   ```bash
   git clone https://github.com/jclark-14/wgups-routing.git
   cd wgups-routing
   ```
2. Run the program:
   ```bash
   python3 main.py
   ```
3. Use CLI Commands:
   ```
   WGUPS » help
   WGUPS » status all 17:00
   WGUPS » mileage
   WGUPS » quit
   ```

---

## 🧪 Running Tests

> Unit tests for key components

```
  python3 -m wgups.test_package
  python3 -m wgups.test_loaders
  python3 -m wgups.test_utils
  python3 -m wgups.test_truck
```

---

## 📂 Project Structure

```bash
  wgups/
  ├── hash_table.py        # Custom HashTable implementation
  ├── models.py            # Package & Truck classes
  ├── load_data.py         # CSV data loaders
  ├── utils.py             # Helper functions (normalization, time parsing)
  ├── test_package.py      # Unit tests: Package
  ├── test_truck.py        # Unit tests: Truck
  ├── test_loaders.py      # Unit tests: Data loaders
  ├── test_utils.py        # Unit tests: Utilities
  └── main.py              # CLI entry point
  data/
  ├── packages.csv         # Package dataset
  └── distances.csv        # Distance matrix
```

---

## 📈 Optimization Algorithms

- Primary:
  Nearest Neighbor for initial pathfinding.
  2-Opt for route refinement to reduce total mileage.

- Future Enhancements (Post-Submission):

  Modular support for alternative algorithms (e.g., Simulated Annealing, Genetic Algorithms).

  Performance benchmarking between algorithms.

  Web-based UI for visualization.

---

## 📝 Notes

- Built following WGU C950 guidelines.

- Focused on clean, maintainable, and extensible code.

- No external dependencies for maximum portability.

- Data parsing handles irregular CSV formats gracefully.

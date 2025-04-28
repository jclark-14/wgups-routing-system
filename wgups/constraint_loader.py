from datetime import datetime
from typing import List, Dict
from wgups.models import Package, Truck
from wgups.constants import START_TIME, EARLY_DEADLINE_CUTOFF, DELAY_TRUCK_ID

class ConstraintLoader:
    def __init__(self,
                 packages: Dict[int, Package],
                 trucks: List[Truck],
                 resolved_groups):
        self.packages = packages
        self.trucks = {t.truck_id: t for t in trucks}
        self.groups = resolved_groups
        self.preassigned: Dict[int, List[int]] = {t: [] for t in self.trucks}

    def apply_hard_constraints(self) -> None:
        self._assign_only_truck()
        self._assign_early_deadlines()
        self._assign_groups()
        self._force_all_remaining_delays_to_delay_truck()
        self._assign_remaining_packages()

    def _assign_only_truck(self):
        for _, pkg in self.packages.items():
            if pkg.only_truck is not None:
                self._safe_assign(pkg, pkg.only_truck)

    # 🔹 Restored Original _assign_groups Logic
    def _assign_groups(self):
        assigned = set()
        last_truck = max(self.trucks)

        for group in self.groups:
            if group & assigned:
                continue

            # Try to fit group into Truck 1 or 2
            for tid in sorted(self.trucks):
                if tid == last_truck:
                    continue
                if self._remaining_capacity(self.trucks[tid]) >= len(group):
                    for pid in group:
                        self._safe_assign(self.packages.lookup(pid), tid)
                    break
            else:
                # If no truck has space, assign to last truck
                for pid in group:
                    self._safe_assign(self.packages.lookup(pid), last_truck)

            assigned |= group

    def _safe_assign(self, pkg: Package, truck_id: int):
        for pkgs in self.preassigned.values():
            if pkg.package_id in pkgs:
                pkgs.remove(pkg.package_id)
        self.preassigned[truck_id].append(pkg.package_id)

    def _remaining_capacity(self, truck: Truck) -> int:
        return truck.capacity - len(self.preassigned[truck.truck_id])

    def _assign_early_deadlines(self):
        priority_trucks = [tid for tid in sorted(self.trucks) if tid != DELAY_TRUCK_ID]
        for _, pkg in self.packages.items():
            if pkg.deadline_time and pkg.deadline_time.time() <= EARLY_DEADLINE_CUTOFF:
                for tid in priority_trucks:
                    if self._remaining_capacity(self.trucks[tid]) > 0:
                        self._safe_assign(pkg, tid)
                        break

    def _force_all_remaining_delays_to_delay_truck(self):
        for _, pkg in self.packages.items():
            if pkg.available_time > START_TIME:
                for pkgs in self.preassigned.values():
                    if pkg.package_id in pkgs:
                        pkgs.remove(pkg.package_id)
                self._safe_assign(pkg, DELAY_TRUCK_ID)

    def _assign_remaining_packages(self):
        for _, pkg in self.packages.items():
            if any(pkg.package_id in pkgs for pkgs in self.preassigned.values()):
                continue
            for tid in sorted(self.trucks):
                if tid == DELAY_TRUCK_ID:
                    continue
                if self._remaining_capacity(self.trucks[tid]) > 0:
                    self._safe_assign(pkg, tid)
                    break
            else:
                self._safe_assign(pkg, DELAY_TRUCK_ID)

    def set_delay_truck_departure(self):
        delay_truck = self.trucks[DELAY_TRUCK_ID]
        latest_time = START_TIME
        for pid in self.preassigned[DELAY_TRUCK_ID]:
            pkg = self.packages.lookup(pid)
            latest_time = max(latest_time, pkg.available_time or START_TIME)
            if pkg.correction_time:
                latest_time = max(latest_time, pkg.correction_time)
        delay_truck.time = latest_time
        print(f"\n🚚 Truck {DELAY_TRUCK_ID} scheduled to depart at {delay_truck.time.strftime('%H:%M')}")

    def generate_post_delivery_report(self):
        print("\n=== Post-Delivery Report ===")
        total_deadlines = 0
        met_deadlines = 0
        for tid in sorted(self.trucks):
            pkgs = self.preassigned[tid]
            print(f"\nTruck {tid}: {len(pkgs)} packages")
            for pid in pkgs:
                pkg = self.packages.lookup(pid)
                report_parts = []
                if pkg.deadline_time:
                    total_deadlines += 1
                    if pkg.delivery_time:
                        if pkg.delivery_time.time() <= pkg.deadline_time.time():
                            status = "✅"
                            met_deadlines += 1
                        else:
                            status = "❌ Missed Deadline"
                    else:
                        status = "❌ Not Delivered"
                    delivery_time_str = pkg.delivery_time.strftime('%H:%M') if pkg.delivery_time else 'N/A'
                    report_parts.append(f"Deadline {pkg.deadline} - Delivered at {delivery_time_str} {status}")
                if pkg.available_time > START_TIME:
                    pickup_time = pkg.departure_time.strftime('%H:%M') if pkg.departure_time else 'N/A'
                    delivery_time = pkg.delivery_time.strftime('%H:%M') if pkg.delivery_time else 'N/A'
                    report_parts.append(f"Delayed until {pkg.available_time.strftime('%H:%M')} - Picked up at {pickup_time} - Delivered at {delivery_time}")
                elif pkg.correction_time:
                    pickup_time = pkg.departure_time.strftime('%H:%M') if pkg.departure_time else 'N/A'
                    delivery_time = pkg.delivery_time.strftime('%H:%M') if pkg.delivery_time else 'N/A'
                    report_parts.append(f"Address correction @ {pkg.correction_time.strftime('%H:%M')} - Picked up at {pickup_time} - Delivered at {delivery_time}")
                if report_parts:
                    print(f"  • Package {pid}: {' | '.join(report_parts)}")
        if total_deadlines > 0:
            pct = (met_deadlines / total_deadlines) * 100
            print(f"\n=== Deadline Compliance Summary ===")
            print(f"✅ Met Deadlines: {met_deadlines} / {total_deadlines} ({pct:.1f}%)")
            print(f"❌ Missed Deadlines: {total_deadlines - met_deadlines}")

    def get_initial_assignments(self) -> Dict[int, List[int]]:
        return self.preassigned

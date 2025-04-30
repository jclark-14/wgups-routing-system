from wgups.constants import  STATUS_DELIVERED

def generate_summary_report(packages, trucks):
    """
    Generate a comprehensive summary report showing all constraint satisfaction,
    delivery times, and other useful metrics.
    """
    delivered_count = sum(1 for pid in packages if packages.lookup(pid).status == STATUS_DELIVERED)
    total_mileage = sum(t.mileage for t in trucks)
    
    # Header
    print("\n" + "="*80)
    print(f"{'WGUPS DELIVERY REPORT':^80}")
    print("="*80)
    
    #Generate reports
    generate_mileage_report(trucks, total_mileage)
    generate_constraint_report(packages)
    package_relationships = generate_group_constraint_report(packages)
    truck_constraints_met, truck_specific_pkgs = generate_truck_report(packages, trucks)
    deadline_met, deadline_packages = generate_constraint_report(packages)

    # Final status summary
    print("\n" + "="*80)
    print(f"{'FINAL STATUS SUMMARY':^80}")
    print("="*80)
    print(f"{'Packages Delivered:':<40} {delivered_count}/{len(packages)}")
    print(f"{'All Deadlines Met:':<40} {'✅' if len(deadline_met) == len(deadline_packages) else '❌'}")
    print(f"{'All Groups Kept Together:':<40} {'✅' if all(len(trucks_used) <= 1 for trucks_used in [set(packages.lookup(m).truck_assigned for m in members) for members in package_relationships.values()]) else '❌'}")
    print(f"{'All Truck Constraints Respected:':<40} {'✅' if len(truck_constraints_met) == len(truck_specific_pkgs) else '❌'}")
    print(f"{'Total Mileage:':<40} {total_mileage:.2f} miles")
    print(f"{'Mileage Requirement Met:':<40} {'✅' if total_mileage < 140 else '❌'}")
    
    return total_mileage


def generate_mileage_report(trucks, total_mileage):
    # Mileage Summary
    print(f"\n{'MILEAGE SUMMARY':^80}")
    print("-"*80)
    for truck in trucks:
        if truck.mileage > 0: 
            print(f"Truck {truck.truck_id}: {truck.mileage:.2f} miles")
    print(f"{'TOTAL MILEAGE:':<40} {total_mileage:.2f} miles")
    if total_mileage < 140:
        print(f"{'MILEAGE REQUIREMENT MET:':<40} ✅ (Under 140 miles)")
    else:
        print(f"{'MILEAGE REQUIREMENT NOT MET:':<40} ❌ (Over 140 miles)")


def generate_constraint_report(packages):
    print(f"\n{'CONSTRAINT SATISFACTION':^80}")
    print("-"*80)
    
    # Deadline Satisfaction
    deadline_packages = []
    deadline_met = []
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.deadline_time:
            deadline_packages.append(pid)
            if pkg.delivery_time <= pkg.deadline_time:
                deadline_met.append(pid)
    
    deadline_percentage = 100.0 if not deadline_packages else (len(deadline_met) / len(deadline_packages)) * 100
    
    print(f"{'DEADLINE SATISFACTION:':<40} {len(deadline_met)}/{len(deadline_packages)} packages ({deadline_percentage:.1f}%)")
    if len(deadline_met) == len(deadline_packages):
        print(f"{'ALL DEADLINES MET:':<40} ✅")
    else:
        missed = [pid for pid in deadline_packages if pid not in deadline_met]
        print(f"{'MISSED DEADLINES:':<40} ❌ {missed}")
    return deadline_met, deadline_packages
        

def generate_group_constraint_report(packages):
    print(f"\n{'GROUP CONSTRAINTS':^80}")
    print("-"*80)

    # First find all package "must be delivered with" relationships
    package_relationships = {}
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.group_with:
            package_relationships[pid] = pkg.group_with

    if package_relationships:
        print(f"{'PACKAGE GROUP RELATIONSHIPS:':<40}")
        print(f"{'Package ID':<12}{'Must be delivered with':<40}{'Status':<12}")
        print("-"*80)
        
        for pid, group_with in package_relationships.items():
            pkg = packages.lookup(pid)
            # Check if all related packages were delivered by the same truck
            all_same_truck = True
            for related_pid in group_with:
                related_pkg = packages.lookup(related_pid)
                if related_pkg.truck_assigned != pkg.truck_assigned:
                    all_same_truck = False
                    break
            
            status = "✅" if all_same_truck else "❌"
            truck_info = f"Truck {pkg.truck_assigned}" if pkg.truck_assigned else "Not assigned"
            
            # Convert list to string for formatting
            group_str = str(sorted(list(group_with)))
            
            print(f"{pid:<12}{group_str:<40}{status} {truck_info}")
    else:
        print("No package group relationships defined")
    return package_relationships
        

def generate_truck_report(packages, trucks):
    print(f"\n{'TRUCK-SPECIFIC CONSTRAINTS':^80}")
    print("-"*80)
    
    truck_specific_pkgs = []
    truck_constraints_met = []
    
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.only_truck:
            truck_specific_pkgs.append(pid)
            if pkg.truck_assigned == pkg.only_truck:
                truck_constraints_met.append(pid)
    
    print(f"{'TRUCK REQUIREMENTS MET:':<40} {len(truck_constraints_met)}/{len(truck_specific_pkgs)} packages")
    if len(truck_constraints_met) == len(truck_specific_pkgs):
        print(f"{'ALL TRUCK CONSTRAINTS MET:':<40} ✅")
    else:
        violated = [pid for pid in truck_specific_pkgs if pid not in truck_constraints_met]
        print(f"{'VIOLATED TRUCK CONSTRAINTS:':<40} ❌ {violated}")
    
    # Truck and Driver Constraint Verification
    print(f"\n{'TRUCK & DRIVER CONSTRAINTS':^80}")
    print("-"*80)

    # Check truck capacity constraint
    capacity_violations = []
    for truck in trucks:
        max_cargo = 0
        for entry in truck.log:
            if "Route assigned" in entry:
                try:
                    route = eval(entry.split("Route assigned: ")[1])
                    max_cargo = max(max_cargo, len(route))
                except:
                    pass
        
        print(f"Truck {truck.truck_id} maximum cargo: {max_cargo}/16 packages")
        if max_cargo > 16:
            capacity_violations.append(truck.truck_id)
         # Simply check how many trucks are operating in total
    active_trucks = sum(1 for truck in trucks if truck.mileage > 0)
        
    # Report on driver constraint
    print(f"\nTotal active trucks: {active_trucks}/2")
    if active_trucks <= 2:
        print("✅ Driver constraint satisfied: No more than 2 trucks used")
    else:
        print("❌ Driver constraint violated: More than 2 trucks used")

    # Report on capacity constraint
    if not capacity_violations:
        print("✅ Capacity constraint satisfied: No truck exceeds 16 packages")
    else:
        print(f"❌ Capacity constraint violated: Trucks {capacity_violations} exceeded capacity")

    # Show truck activity periods in a simpler format
    print("\nTruck Activity Periods:")
    for truck in trucks:
        if truck.mileage > 0:
            # Find first and last time in log
            try:
                first_entry = truck.log[0]
                first_time = first_entry[1:6]  # Format: [HH:MM]
                
                last_entry = truck.log[-1]
                last_time = last_entry[1:6]  # Format: [HH:MM]
                
                print(f"  Truck {truck.truck_id}: Active from {first_time} to {last_time}")
            except:
                print(f"  Truck {truck.truck_id}: Active (time details unavailable)")
    return truck_constraints_met, truck_specific_pkgs
    
def generate_deadline_report(packages):
    # Special Case Packages
    print(f"\n{'SPECIAL CASE PACKAGES':^80}")
    print("-"*80)
    
    # Address correction packages
    corrected_pkgs = []
    
    for pid in packages:
        pkg = packages.lookup(pid)
        if pkg.correction_time:
            corrected_pkgs.append(pid)
    
    if corrected_pkgs:
        print(f"\n{'ADDRESS CORRECTION PACKAGES:':<30}")
        for pid in sorted(corrected_pkgs):
            pkg = packages.lookup(pid)
            correction_time = pkg.correction_time.strftime("%H:%M") if pkg.correction_time else "N/A"
            delivery_time = pkg.delivery_time.strftime("%H:%M") if pkg.delivery_time else "Not delivered"
            original_addr = pkg.original_address
            corrected_addr = pkg.corrected_address or "No correction"
            
            print(f"  Package {pid:<2}: Corrected @ {correction_time}, Delivered @ {delivery_time}")
            print(f"      Original address: {original_addr}")
            print(f"      Corrected address: {corrected_addr}")
    
    print(f"\n{'PACKAGE DELIVERY TIMELINE':^80}")
    print("-"*80)
    print(f"{'ID':^4}|{'Status':^12}|{'Truck':^7}|{'Delivered At':^15}|{'Deadline':^15}|{'Special Notes':^25}")
    print("-"*80)
from datetime import datetime, time
from wgups.constants import TODAY, STATUS_DELIVERED, START_TIME

def generate_summary_report(packages, trucks):
    """
    Generate a comprehensive summary report showing all constraint satisfaction,
    delivery times, and other useful metrics.
    """
    total_mileage = sum(t.mileage for t in trucks)
    delivered_count = sum(1 for pid in packages if packages.lookup(pid).status == STATUS_DELIVERED)
    
    # Header
    print("\n" + "="*80)
    print(f"{'WGUPS DELIVERY REPORT':^80}")
    print("="*80)
    
    # Mileage Summary
    print(f"\n{'MILEAGE SUMMARY':^80}")
    print("-"*80)
    for truck in trucks:
        if truck.mileage > 0:  # Only show active trucks
            print(f"Truck {truck.truck_id}: {truck.mileage:.2f} miles")
    print(f"{'TOTAL MILEAGE:':<40} {total_mileage:.2f} miles")
    if total_mileage < 140:
        print(f"{'MILEAGE REQUIREMENT MET:':<40} ✅ (Under 140 miles)")
    else:
        print(f"{'MILEAGE REQUIREMENT NOT MET:':<40} ❌ (Over 140 miles)")
    
    # Constraint Satisfaction
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
    
    # Group Constraints
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
    
    # Truck-specific constraints
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
    
    # Special Case Packages
    print(f"\n{'SPECIAL CASE PACKAGES':^80}")
    print("-"*80)
    
    # Delayed packages
    # delayed_pkgs = []
    
    # for pid in packages:
    #     pkg = packages.lookup(pid)
    #     if pkg.available_time > START_TIME:
    #         delayed_pkgs.append(pid)
    
    # # if delayed_pkgs:
    #     print(f"{'DELAYED PACKAGES:':<20}")
    #     for pid in sorted(delayed_pkgs):
    #         pkg = packages.lookup(pid)
    #         delay_time = pkg.available_time.strftime("%H:%M")
    #         pickup_time = pkg.departure_time.strftime("%H:%M") if pkg.departure_time else "Not picked up"
    #         delivery_time = pkg.delivery_time.strftime("%H:%M") if pkg.delivery_time else "Not delivered"
    #         deadline = pkg.deadline_time.strftime("%H:%M") if pkg.deadline_time else "EOD"
    #         status = "✅" if pkg.delivery_time and (not pkg.deadline_time or pkg.delivery_time <= pkg.deadline_time) else "❌"
            
    #         print(f"  Package {pid:<2}: Available @ {delay_time}, Picked up @ {pickup_time}, "
    #               f"Delivered @ {delivery_time}, Deadline: {deadline} {status}")
    
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

    # Sort packages by delivery time
    package_deliveries = []
    for pid in range(1, 41):  # Assuming 40 packages
        pkg = packages.lookup(pid)
        if pkg:
            delivery_time = pkg.delivery_time.strftime("%H:%M") if pkg.delivery_time else "Not delivered"
            deadline = pkg.deadline_time.strftime("%H:%M") if pkg.deadline_time else "EOD"
            status = "✅" if pkg.status == STATUS_DELIVERED and (not pkg.deadline_time or pkg.delivery_time <= pkg.deadline_time) else "❌"
            
            # Special notes
            notes = []
            if pkg.only_truck:
                notes.append(f"Truck {pkg.only_truck} only")
            if pkg.correction_time:
                notes.append(f"Address corrected @{pkg.correction_time.strftime('%H:%M')}")
            if pkg.available_time > START_TIME:
                notes.append(f"Delayed until {pkg.available_time.strftime('%H:%M')}")
            if pkg.group_with:
                notes.append(f"Group with {sorted(pkg.group_with)}")
            
            notes_str = ", ".join(notes)
            
            package_deliveries.append((
                pid, 
                status, 
                pkg.truck_assigned or "-", 
                delivery_time,
                deadline,
                notes_str
            ))

    # # Sort by delivery time (packages with no delivery time go at the end)
    # package_deliveries.sort(key=lambda x: (x[3] == "Not delivered", x[3]))

    # # Print delivery timeline
    # for pid, status, truck, delivery_time, deadline, notes in package_deliveries:
    #     print(f"{pid:^4}|{status:^12}|{truck:^7}|{delivery_time:^15}|{deadline:^15}|{notes[:25]:^25}")
    
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

def run_cli(packages, trucks):
    """
    Run an interactive command-line interface for checking package status and mileage.
    """
    total_mileage = sum(t.mileage for t in trucks if hasattr(t, 'mileage'))
    
    while True:
        print("\n" + "="*80)
        # print(f"{'WGUPS PACKAGE TRACKING SYSTEM':^80}")
        # print("="*80)
        print("\nCommands:")
        print("  1. Check status of a specific package")
        print("  2. Check status of all packages at a specific time")
        print("  3. Show total mileage")
        print("  4. Show status snapshot (time ranges for screenshots)")
        print("  5. Show detailed delivery report")
        print("  q. Quit")
        
        choice = input("\nEnter command (1-5, q): ").strip().lower()
        
        if choice == 'q':
            break
            
        elif choice == '1':
            try:
                pkg_id = int(input("Enter package ID (1-40): ").strip())
                if 1 <= pkg_id <= 40:
                    pkg = packages.lookup(pkg_id)
                    if pkg:
                        _display_package_details(pkg)
                    else:
                        print(f"Package ID {pkg_id} not found")
                else:
                    print("Invalid package ID. Please enter a number between 1 and 40.")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
        elif choice == '2':
            try:
                time_str = input("Enter time (HH:MM): ").strip()
                check_time = datetime.strptime(time_str, "%H:%M").time()
                check_datetime = datetime.combine(TODAY, check_time)
                
                print(f"\nPackage Status at {time_str}:")
                print("-"*80)
                print(f"{'ID':^4}|{'Status':^30}|{'Address':^30}|{'Deadline':^10}|{'Weight':^6}")
                print("-"*80)
                
                for pid in range(1, 41):
                    pkg = packages.lookup(pid)
                    if pkg:
                        status = _get_status_at_time(pkg, check_datetime)
                        deadline = pkg.deadline_time.strftime("%H:%M") if pkg.deadline_time else "EOD"
                        address = _get_address_at_time(pkg, check_datetime)
                        
                        print(f"{pid:^4}|{status:^30}|{address[:30]:^30}|{deadline:^10}|{pkg.weight:^6}")
            except ValueError:
                print("Invalid time format. Please use HH:MM (24-hour format).")
                
        elif choice == '3':
            print(f"\nTotal mileage traveled by all trucks: {total_mileage:.2f} miles")
            for truck in trucks:
                if hasattr(truck, 'mileage') and truck.mileage > 0:
                    print(f"  Truck {truck.truck_id}: {truck.mileage:.2f} miles")
                    
        elif choice == '4':
            print("\nSelect time range for status snapshot:")
            print("  1. Between 8:35 a.m. and 9:25 a.m.")
            print("  2. Between 9:35 a.m. and 10:25 a.m.")
            print("  3. Between 12:03 p.m. and 1:12 p.m.")
            
            snapshot_choice = input("Enter choice (1-3): ").strip()
            if snapshot_choice == '1':
                _show_status_snapshot(packages, trucks, 
                                     datetime.combine(TODAY, time(8, 35)),
                                     datetime.combine(TODAY, time(9, 25)))
            elif snapshot_choice == '2':
                _show_status_snapshot(packages, trucks, 
                                     datetime.combine(TODAY, time(9, 35)),
                                     datetime.combine(TODAY, time(10, 25)))
            elif snapshot_choice == '3':
                _show_status_snapshot(packages, trucks, 
                                     datetime.combine(TODAY, time(12, 3)),
                                     datetime.combine(TODAY, time(13, 12)))
            else:
                print("Invalid choice.")
                
        elif choice == '5':
            generate_summary_report(packages, trucks)
            
        else:
            print("Invalid command. Please try again.")

def _get_status_at_time(package, time):
    """Get the status of a package at a specific time"""
    if time < package.available_time:
        return f"At the hub (available at {package.available_time.strftime('%H:%M')})"
    elif package.delivery_time and time >= package.delivery_time:
        return f"Delivered at {package.delivery_time.strftime('%H:%M')}"
    elif package.departure_time and time >= package.departure_time:
        return f"En route on truck {package.truck_assigned}"
    else:
        return "At the hub"

def _get_address_at_time(package, time):
    """Get the correct address of a package at a specific time"""
    if package.correction_time and time < package.correction_time:
        return package.original_address
    return package.corrected_address if package.corrected_address else package.address

def _display_package_details(package):
    """Display detailed information about a package"""
    print("\nPackage Details:")
    print(f"Package ID: {package.package_id}")
    print(f"Delivery Address: {package.address}")
    print(f"Delivery City: {package.city}")
    print(f"Delivery Zip Code: {package.zip_code}")
    print(f"Package Weight: {package.weight} kilos")
    print(f"Delivery Deadline: {package.deadline}")
    
    # Status information
    print(f"Delivery Status: {package.status}")
    if package.departure_time:
        print(f"Departure Time: {package.departure_time.strftime('%H:%M')}")
    if package.delivery_time:
        print(f"Delivery Time: {package.delivery_time.strftime('%H:%M')}")
    
    # Special notes
    if package.note:
        print(f"Special Notes: {package.note}")
    if package.correction_time:
        print(f"Address Correction: {package.corrected_address} at {package.correction_time.strftime('%H:%M')}")
    if package.only_truck:
        print(f"Must be delivered by Truck {package.only_truck}")
    if package.group_with:
        print(f"Must be delivered with packages: {sorted(package.group_with)}")

def _show_status_snapshot(packages, trucks, start_time, end_time):
    """Show a snapshot of all packages and trucks at a specific time range"""
    check_time = start_time + (end_time - start_time) // 2  # Use middle of range
    
    print(f"\nPackage Status Snapshot ({check_time.strftime('%H:%M')} - between "
          f"{start_time.strftime('%H:%M')} and {end_time.strftime('%H:%M')}):")
    print("-"*80)
    
    # Show truck status
    print("\nTruck Status:")
    for truck in trucks:
        if not hasattr(truck, 'log'):
            continue
            
        # Determine truck status at this time
        status = "Not dispatched"
        location = "Hub"
        cargo = []
        
        for entry in truck.log:
            # Parse time from log entry
            try:
                log_time_str = entry[1:7]  # Format: [HH:MM]
                log_time = datetime.strptime(log_time_str, "%H:%M").time()
                log_datetime = datetime.combine(TODAY, log_time)
                
                if log_datetime <= check_time:
                    if "initialized" in entry:
                        status = "Initialized"
                    elif "Route assigned" in entry:
                        status = "Route assigned"
                        cargo = eval(entry.split("Route assigned: ")[1])  # Extract route
                    elif "Delivered Package" in entry:
                        status = "En route"
                        delivered_pid = int(entry.split("Delivered Package ")[1].split(" ")[0])
                        if delivered_pid in cargo:
                            cargo.remove(delivered_pid)
                    elif "Returned to hub" in entry:
                        status = "At hub"
                        cargo = []
                else:
                    break
            except (ValueError, IndexError):
                pass
                
        print(f"Truck {truck.truck_id}: {status} with {len(cargo)} packages")
        if cargo:
            print(f"  Cargo: {cargo}")
    
    # Show package status
    print("\nPackage Status:")
    print(f"{'ID':^4}|{'Status':^30}|{'Address':^30}|{'Deadline':^10}|{'Weight':^6}")
    print("-"*80)
    
    for pid in range(1, 41):
        pkg = packages.lookup(pid)
        if pkg:
            status = _get_status_at_time(pkg, check_time)
            deadline = pkg.deadline_time.strftime("%H:%M") if pkg.deadline_time else "EOD"
            address = _get_address_at_time(pkg, check_time)
            
            print(f"{pid:^4}|{status:^30}|{address[:30]:^30}|{deadline:^10}|{pkg.weight:^6}")
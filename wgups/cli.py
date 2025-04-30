from datetime import datetime, time
from wgups.simulation import run_simulation, run_simulation_with_planning
from wgups.constants import TODAY
from wgups.optimizer_core import RouteOptimizer

def run_program(optimizer: RouteOptimizer, single_run: bool = False, iterations: int = 20):
    """
    Main program runner. Initializes and executes the WGUPS routing program.
    If single_run is True, bypass the planning phase and runs a one-shot simulation.
    
    """
    
    print("="*80)
    print(f"{'WGUPS PACKAGE DELIVERY SYSTEM':^80}")
    print("="*80)
    
    if single_run:
        print("Initializing simulation with Enhanced Optimization algorithm...")
        packages, trucks = run_simulation(optimizer)
        print("\nSimulation completed!")
    else:
        print(f"Initializing package delivery optimization...")
        print(f"Starting route planning phase ({iterations} iterations)...")
        packages, trucks = run_simulation_with_planning(optimizer, iterations)
        print("\nSimulation complete!")
    
    print("Starting interactive command-line interface...")
    run_cli(packages, trucks)

def run_cli(packages, trucks):
    """
    Run an interactive command-line interface for checking package status and mileage.
    This menu-driven CLI supports real-time queries and generating snapshots for demo screenshots.
    """
    total_mileage = sum(t.mileage for t in trucks if hasattr(t, 'mileage'))
    
    while True:
        print("\n" + "="*80)
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
                        status = _get_status_at_time(pkg, check_datetime)   # Determine package status based on time-relative fields (available, departure, delivery)
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
            # Used to visually inspect truck and package status during key time ranges. Useful for project screenshots or audits.
            _show_status_snapshot_menu(packages, trucks)
                
        elif choice == '5': # Generates full delivery and constraint compliance report
            from wgups.reporting import generate_summary_report
            generate_summary_report(packages, trucks)
            
        else:
            print("Invalid command. Please try again.")

def _show_status_snapshot_menu(packages, trucks):
    """Display menu for status snapshots and handle selection."""
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
    
    print(f"Delivery Status: {package.status}")
    if package.departure_time:
        print(f"Departure Time: {package.departure_time.strftime('%H:%M')}")
    if package.delivery_time:
        print(f"Delivery Time: {package.delivery_time.strftime('%H:%M')}")
    

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
    check_time = start_time + (end_time - start_time) // 2  # Use middle of range for snapshot
    
    print(f"\nPackage Status Snapshot ({check_time.strftime('%H:%M')} - between "
          f"{start_time.strftime('%H:%M')} and {end_time.strftime('%H:%M')}):")
    print("-"*80)
    
    print("\nTruck Status:")
    for truck in trucks:
        if not hasattr(truck, 'log'):
            continue
            
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
                        cargo = eval(entry.split("Route assigned: ")[1])
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
import frappe

def execute():
    # Fetch all employees
    employees = frappe.get_all('ALMS Employee', fields=['name', 'employee_code'])
    
    total = len(employees)
    print(f"Found {total} ALMS Employees to migrate. Starting...")
    frappe.logger().info(f"Found {total} ALMS Employees to migrate. Starting...")
    
    for i, emp in enumerate(employees):
        current_name = emp.name
        new_name = emp.employee_code
        
        # If the name is already the employee code, skip
        if current_name == new_name:
            continue
            
        try:
            # Rename the document
            frappe.rename_doc('ALMS Employee', current_name, new_name, ignore_permissions=True)
            frappe.db.commit()
            
            # Print progress every 100 records
            if (i + 1) % 100 == 0:
                print(f"Progress: [{i + 1}/{total}] Renamed {current_name} to {new_name}")
                frappe.logger().info(f"Progress: [{i + 1}/{total}] Renamed {current_name} to {new_name}")
                
        except Exception as e:
            frappe.db.rollback()
            print(f"Failed to rename {current_name} to {new_name}: {str(e)}")
            frappe.log_error(title=f"Migration Error: {current_name}", message=f"Failed to rename {current_name} to {new_name}: {str(e)}")

    print("Migration completed successfully!")
    frappe.log_error(title="Migration Success", message="Migration completed successfully!")

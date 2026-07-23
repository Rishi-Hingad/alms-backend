import frappe

def execute():
    # Fetch all employees
    employees = frappe.get_all('ALMS Employee', fields=['name', 'employee_code'])
    
    frappe.logger().info(f"Starting ALMS Employee Rename Patch for {len(employees)} records.")
    
    for emp in employees:
        current_name = emp.name
        new_name = emp.employee_code
        
        # If the name is already the employee code, skip
        if current_name == new_name:
            continue
            
        try:
            # Rename the document
            frappe.rename_doc('ALMS Employee', current_name, new_name)
            # We don't commit inside the loop for patches; frappe's patch runner handles commits.
        except Exception as e:
            frappe.log_error(title=f"Migration Error: {current_name}", message=f"Failed to rename {current_name} to {new_name}: {str(e)}")

    frappe.logger().info("ALMS Employee Rename Patch completed successfully!")

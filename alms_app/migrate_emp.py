import frappe

def execute():
    # Fetch all employees
    employees = frappe.get_all('ALMS Employee', fields=['name', 'employee_code'])
    
    # Find employees whose name hasn't been updated to just the code yet
    pending = [emp for emp in employees if emp.name != emp.employee_code]
    
    if not pending:
        frappe.logger().info("ALMS Employee Migration: All records successfully migrated.")
        return
        
    batch_size = 500
    to_process = pending[:batch_size]
    
    frappe.logger().info(f"ALMS Employee Migration: Processing batch of {len(to_process)} records out of {len(pending)} pending.")
    
    for emp in to_process:
        try:
            frappe.rename_doc('ALMS Employee', emp.name, emp.employee_code)
            frappe.db.commit()
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(title=f"Migration Error: {emp.name}", message=f"Failed to rename {emp.name} to {emp.employee_code}: {str(e)}")

    frappe.logger().info(f"ALMS Employee Migration: Batch complete. {len(pending) - len(to_process)} remaining.")

import frappe

def execute():
    # Find a user with the "Finance Team" role
    users = frappe.get_all("Has Role", filters={"role": "Finance Team", "parenttype": "User"}, fields=["parent"])
    if not users:
        print("No user found with role 'Finance Team'")
        return
    test_user = users[0].parent
    print(f"Testing with user: {test_user}")
    
    # Find a pending Invoice Batch
    batches = frappe.get_all("Invoice Batch", filters={"status": ["in", ["Completed", "Partially Completed"]]}, fields=["name"], limit=1)
    if not batches:
        print("No Completed/Partially Completed Invoice Batch found to test.")
        return
    doc_name = batches[0].name
    print(f"Testing with Invoice Batch: {doc_name}")
    
    # Impersonate user
    frappe.set_user(test_user)
    
    # Run logic
    doctype = "Invoice Batch"
    
    frappe.flags.ignore_permissions = True
    try:
        entry_name = frappe.db.get_value("Approval Entry", {
            "applied_to_doctype": doctype,
            "record": doc_name,
            "status": "Pending"
        }, "name")
        print(f"entry_name = {entry_name}")
        
        if not entry_name:
            print("Failed: No entry_name")
            return
            
        entry = frappe.get_doc("Approval Entry", entry_name)
        ledger_table = "approval_ledger" if hasattr(entry, "approval_ledger") else "approval_entry"
        ledger_items = entry.get(ledger_table)
    finally:
        frappe.flags.ignore_permissions = False
        
    if not ledger_items:
        print("Failed: No ledger_items")
        return
        
    target_stage = entry.next_approval_stage
    pending_row = None
    for row in ledger_items:
        if row.next_stage == target_stage:
            pending_row = row
            break
            
    if not pending_row:
        pending_row = ledger_items[-1]
        
    employee = frappe.db.get_value("Employee", {"user_id": test_user}, "name")
    
    allowed_team = getattr(pending_row, "next_approver_team", None)
    allowed_user = getattr(pending_row, "next_approver", None)
    allowed_role = getattr(pending_row, "next_approver_role", None)
    
    print(f"target_stage={target_stage}")
    print(f"pending_row next_stage={getattr(pending_row, 'next_stage', None)}")
    print(f"employee={employee}")
    print(f"allowed_team={allowed_team}")
    print(f"allowed_user={allowed_user}")
    print(f"allowed_role={allowed_role}")
    
    roles = frappe.get_roles(test_user)
    print(f"user roles={roles}")
    
    if allowed_role and allowed_role in roles:
        print("SUCCESS via role")
        return
        
    if allowed_team and employee:
        if frappe.db.exists("Employee", {"department": allowed_team, "name": employee}):
            print("SUCCESS via team")
            return
            
    print("FAILED ALL CHECKS")


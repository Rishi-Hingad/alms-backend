import frappe

def execute():
    # Update the escalation child table's monthly_rent
    escalations = frappe.get_all("Escalation", filters={"parent": "LMS-APR22_MAR27-154"})
    for esc in escalations:
        frappe.db.set_value("Escalation", esc.name, "monthly_rent", 51852.0)
    
    # Ensure calculation rate type is Daily Rate
    frappe.db.set_value("Lease Management", "LMS-APR22_MAR27-154", "calculation_rate_type", "Daily Rate")
    
    frappe.db.commit()
    print("Successfully updated database for LMS-APR22_MAR27-154. monthly_rent is now 51852.0")


import frappe
def run_test():
    frappe.db.set_value("Lease Management", "LMS-APR22_MAR27-154", "calculation_rate_type", "Daily Rate")
    for esc in frappe.get_all("Escalation", filters={"parent": "LMS-APR22_MAR27-154"}):
        frappe.db.set_value("Escalation", esc.name, "monthly_rent", 51852.0)
    frappe.db.commit()
    print("Done setting UAT state")

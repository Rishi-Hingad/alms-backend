import frappe
def run_test():
    val = frappe.db.get_value("Lease Management", "LMS-APR22_MAR27-154", "calculation_rate_type")
    print(f"calculation_rate_type: {val}")

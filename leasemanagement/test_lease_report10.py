import frappe
from leasemanagement.lease_management_system.report.lease_report_monthly_with_escalation.lease_report_monthly_with_escalation import execute
def run_test():
    frappe.db.set_value("Lease Management", "LMS-APR22_MAR27-154", "calculation_rate_type", "Monthly Rate")
    for esc in frappe.get_all("Escalation", filters={"parent": "LMS-APR22_MAR27-154"}):
        frappe.db.set_value("Escalation", esc.name, "monthly_rent", 51852.0)
    frappe.db.commit()

    columns, rows = execute(filters={"docname": "LMS-APR22_MAR27-154"})
    for r in rows:
        if str(r.get("month_start_date")) in ["2024-04-01", "2024-05-01", "2024-06-01"]:
            print(f"Date: {r.get('month_start_date')} -> mlp: {r.get('mlp')}")

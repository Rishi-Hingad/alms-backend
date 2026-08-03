import frappe
from lease_management_system.report.lease_report.lease_report import execute
def run_test():
    for esc in frappe.get_all("Escalation", filters={"parent": "LMS-APR22_MAR27-154"}):
        frappe.db.set_value("Escalation", esc.name, "monthly_rent", 0.0)
    frappe.db.commit()

    columns, rows = execute(filters={"docname": "LMS-APR22_MAR27-154"})
    for r in rows:
        if str(r.get("month_end_date")) == "2026-03-31":
            print(f"2026-03-31 closing_liability: {r.get('closing_liability')}")
        if str(r.get("month_start_date")) == "2026-04-01":
            print(f"2026-04-01 mlp: {r.get('mlp')}, interest: {r.get('interest_cost')}")

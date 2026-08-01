import frappe
from lease_app.lease_management_system.report.lease_report_monthly_with_escalation.lease_report_monthly_with_escalation import execute

def run_test():
    columns, rows = execute(filters={"docname": "LMS-APR22_MAR27-154"})
    for r in rows:
        if str(r.get("month_start_date")) == "2024-04-01":
            print(f"DEBUG 2024-04-01 mlp: {r.get('mlp')}")

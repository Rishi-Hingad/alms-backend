import frappe
from lease_management_system.report.lease_report.lease_report import execute

def run_test():
    columns, rows = execute(filters={"docname": "LMS-APR22_MAR27-154"})
    for r in rows:
        print(f"Date: {r.get('month_start_date')} -> mlp: {r.get('mlp')} n: {r.get('n')}")

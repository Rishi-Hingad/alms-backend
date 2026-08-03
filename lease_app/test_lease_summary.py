import frappe
from lease_management_system.report.lease_summary_report.lease_summary_report import execute
def run_test():
    columns, data = execute(filters={"company_name": "Meril Endosurgery Private Limited", "fin_start_year": "2026", "fin_end_year": "2027"})
    for row in data:
        if row.get("lease_id") == "LMS-APR22_MAR27-154":
            print(f"LMS-APR22_MAR27-154 -> {row}")

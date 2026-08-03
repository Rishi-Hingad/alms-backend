import frappe
from lease_app.lease_management_system.report.lease_summary_report.lease_summary_report import execute
def run_test():
    try:
        # Get a real company from the DB
        company = frappe.db.get_value("Company Master", {})
        print("Testing with company:", company)
        columns, data = execute({"company_name": company, "fin_start_year": 2026, "fin_end_year": 2027})
        print("Got rows:", len(data))
    except Exception as e:
        print("ERROR:", str(e))
run_test()

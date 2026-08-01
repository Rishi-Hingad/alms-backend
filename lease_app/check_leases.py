import frappe
from frappe.desk.query_report import run

def execute():
    leases = frappe.get_all("Lease Management", filters={"vendor": "Easy Asset"}, fields=["name", "calculation_rate_type", "monthly_rent"])
    print("Easy Asset Leases:")
    for l in leases:
        print(l)
        # Check their lease summary report output
        # res = run("Lease Summary Report", filters={})
        
execute()

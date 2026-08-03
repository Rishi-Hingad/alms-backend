import frappe
from frappe.desk.query_report import run

def execute():
    try:
        leases = frappe.get_all("Lease Management", limit=1)
        if not leases:
            print("No leases.")
            return
        company_name = frappe.get_all("Company", limit=1)
        if company_name:
            c = company_name[0].name
        else:
            c = "Dummy Company"
        
        # Mock frappe.get_all inside the report? 
        # Well, the report might fail again if Company doesn't exist but the report requires one.
        # Actually, let's just see if there's any Lease Management and what its Company is
        lease = frappe.get_doc("Lease Management", leases[0].name)
        res = run("Lease Summary Report", filters={"company_name": lease.company, "fin_start_year": "2024", "fin_end_year": "2025"})
        print("Summary Report output length:", len(res.get("result", [])))
        
        # Check first row
        row = res.get("result", [])[0]
        print("First row closing ROU:", row.get("rou_closing"))
    except Exception as e:
        import traceback
        traceback.print_exc()

execute()

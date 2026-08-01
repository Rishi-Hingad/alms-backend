import frappe
from frappe.desk.query_report import run

def execute():
    try:
        # Get one Easy Asset lease
        leases = frappe.get_all("Lease Management", filters={"vendor": "Easy Asset", "docstatus": ["!=", 2]}, limit=1)
        if not leases:
            print("No Easy Asset lease found.")
            return
        lease_name = leases[0].name
        doc = frappe.get_doc("Lease Management", lease_name)
        
        print("TESTING LEASE:", doc.name)
        print("Current Monthly Rent:", doc.monthly_rent)
        print("Calculation Rate Type:", doc.calculation_rate_type)
        print("Type of Report:", doc.type_of_report)
        
        # 1. Test how it runs currently (Monthly Rate, Monthly Rent = X/3)
        lreport_monthly = "Lease Report Monthly (With Escalation)"
        res_monthly = run(lreport_monthly, filters={"docname": doc.name, "sum_modified": None})
        rows_m = res_monthly.get("result", [])
        rent_m = sum(r.get("mlp", 0) for r in rows_m if r.get("mlp"))
        print("--- CURRENT UAT METHOD ---")
        print("Rows generated:", len(rows_m))
        print("Total Rent Paid:", rent_m)
        
        # 2. Test how it ran in PROD (Daily Rate, Quarterly Report, Monthly Rent = X)
        doc.calculation_rate_type = "Daily Rate"
        doc.type_of_report = "Quarterly"
        doc.monthly_rent = doc.monthly_rent * 3
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        lreport_daily = "Lease Report"
        res_daily = run(lreport_daily, filters={"docname": doc.name, "sum_modified": None})
        rows_d = res_daily.get("result", [])
        rent_d = sum(r.get("mlp", 0) for r in rows_d if r.get("mlp"))
        print("--- PROD METHOD ---")
        print("Rows generated:", len(rows_d))
        print("Total Rent Paid:", rent_d)
        
        # Restore
        doc.calculation_rate_type = "Monthly Rate"
        doc.type_of_report = "Quarterly"
        doc.monthly_rent = doc.monthly_rent / 3
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        print("ERROR:", str(e))

execute()

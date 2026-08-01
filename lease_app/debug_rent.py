import frappe
from frappe.desk.query_report import run

def execute():
    print("START")
    leases = frappe.get_all("Lease Management", filters={"vendor": "Easy Asset"}, fields=["name", "monthly_rent", "calculation_rate_type", "type_of_report", "agreement_start_date", "agreement_end_date"], limit=2)
    print("LEASES FOUND:", len(leases))
    for lease in leases:
        print("LEASE:", lease)
        try:
            if lease.calculation_rate_type == "Daily Rate":
                lreport = "Lease Report"
            else:
                lreport = "Lease Report Monthly (With Escalation)"
            
            res = run(lreport, filters={"docname": lease.name, "sum_modified": None})
            rows = res.get("result", [])
            total_rent = 0
            for r in rows:
                if r.get("mlp"):
                    total_rent += r.get("mlp")
            print("Total Rent Paid via", lreport, ":", total_rent)
        except Exception as e:
            print("ERROR", str(e))
    print("END")
execute()

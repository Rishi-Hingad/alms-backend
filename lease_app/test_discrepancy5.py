import frappe
from frappe.desk.query_report import run

def test():
    lease_name = "LMS-APR22_MAR27-154"
    result = run("Lease Report", filters={"docname": lease_name})
    rows = result.get("result", [])
    print(f"Total rows: {len(rows)}")
    for r in rows:
        wdv = r.get("wdv", 0)
        dep = r.get("depreciation", 0)
        print(f"{r.get('month_end_date')} -> wdv: {wdv}, dep: {dep}, mlp: {r.get('mlp')}")

test()

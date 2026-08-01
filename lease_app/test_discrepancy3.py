import frappe
from frappe.desk.query_report import run
from datetime import date
from frappe.utils import getdate

def test():
    lease_name = "LMS-APR22_MAR27-154"
    result = run("Lease Report", filters={"docname": lease_name, "sum_modified": None})
    rows = result.get("result", [])
    msdate = date(2026, 4, 1)
    medate = date(2027, 3, 1)
    
    def parse_date(d):
        if not d: return None
        if isinstance(d, date): return d
        try: return getdate(d)
        except: return None
        
    print("sum_modified=None:")
    for r in rows:
        rmonth_start = parse_date(r.get("month_start_date"))
        if rmonth_start and rmonth_start >= msdate and rmonth_start <= medate:
            print(f"Row {rmonth_start}: mlp={r.get('mlp')} int={r.get('interest_cost')} dep={r.get('depreciation')}")

test()

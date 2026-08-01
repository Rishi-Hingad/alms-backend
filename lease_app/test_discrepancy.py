import frappe
from frappe.desk.query_report import run
from datetime import date
from frappe.utils import getdate

def test():
    lease_name = "LMS-APR22_MAR27-154"
    result = run("Lease Report", filters={"docname": lease_name})
    rows = result.get("result", [])
    sdate = date(2026, 3, 31)
    def parse_date(d):
        if not d: return None
        if isinstance(d, date): return d
        try: return getdate(d)
        except: return None
        
    for r in rows:
        if parse_date(r.get("month_end_date")) == sdate:
            print("Row at sdate:", r)
test()

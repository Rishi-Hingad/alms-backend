import frappe
from alms_app.api.api_utils import get_mlp
from datetime import date

def test():
    lease_name = "LMS-APR22_MAR27-154"
    doc = frappe.get_doc("Lease Management", lease_name)
    
    # Test for a month that is 0
    test_date = date(2026, 4, 1)
    
    # get_mlp signature: get_mlp(doc, current_date, month_end_date)
    # wait, let me check the signature of get_mlp
    
test()

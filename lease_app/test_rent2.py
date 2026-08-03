import frappe
from frappe.desk.query_report import run

def execute():
    try:
        # Check if we have discounting rate
        if not frappe.db.get_list("Discounting Rate"):
            d = frappe.new_doc("Discounting Rate")
            d.discounting_rate = 10
            d.insert(ignore_permissions=True)
            
        doc = frappe.new_doc("Lease Management")
        doc.vendor = "Easy Asset"
        doc.agreement_start_date = "2025-04-01"
        doc.agreement_end_date = "2026-03-31"
        doc.type_of_asset = "Car"
        doc.status = "Active"
        
        # Method A: PROD (Daily Rate, Quarterly, monthly_rent = 12000)
        doc.calculation_rate_type = "Daily Rate"
        doc.type_of_report = "Quarterly"
        doc.monthly_rent = 12000
        doc.lease_period = "Short Term (Less Than 12 Months)"
        doc.insert(ignore_permissions=True)
        
        res_prod = run("Lease Report", filters={"docname": doc.name})
        rows_prod = res_prod.get("result", [])
        rent_prod = sum(r.get("mlp", 0) for r in rows_prod if r.get("mlp"))
        depre_prod = sum(r.get("depreciation", 0) for r in rows_prod if r.get("depreciation"))
        interest_prod = sum(r.get("interest_cost", 0) for r in rows_prod if r.get("interest_cost"))
        
        # Method B: UAT Current Fix (Daily Rate, Quarterly, monthly_rent = 4000)
        doc.monthly_rent = 4000
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        res_uat = run("Lease Report", filters={"docname": doc.name})
        rows_uat = res_uat.get("result", [])
        rent_uat = sum(r.get("mlp", 0) for r in rows_uat if r.get("mlp"))
        depre_uat = sum(r.get("depreciation", 0) for r in rows_uat if r.get("depreciation"))
        interest_uat = sum(r.get("interest_cost", 0) for r in rows_uat if r.get("interest_cost"))
        
        print("--- PROD (12000 in monthly_rent field) ---")
        print("Rent Paid:", rent_prod, "Depre:", depre_prod, "Interest:", interest_prod, "PV:", sum(r.get("pv", 0) for r in rows_prod if r.get("pv")))
        
        print("--- UAT (4000 in monthly_rent field with 3x logic) ---")
        print("Rent Paid:", rent_uat, "Depre:", depre_uat, "Interest:", interest_uat, "PV:", sum(r.get("pv", 0) for r in rows_uat if r.get("pv")))
        
        doc.delete()
        
    except Exception as e:
        import traceback
        traceback.print_exc()

execute()

import frappe

def execute():
    if not frappe.db.table_exists("Purchase Form"):
        return
        
    # Revert all Purchase Forms to docstatus 0
    frappe.db.sql("""
        UPDATE `tabPurchase Form`
        SET docstatus = 0
        WHERE docstatus > 0
    """)
    frappe.db.commit()
    
    # Reload the doctype to ensure cache is updated
    frappe.reload_doc('crms', 'doctype', 'purchase_form')

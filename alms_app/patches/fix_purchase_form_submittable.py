import frappe

def execute():
    # Only execute if Purchase Form exists
    if not frappe.db.exists("DocType", "Purchase Form"):
        return

    # Update all Purchase Form records to docstatus = 0
    # This prevents ValidationError: "Cannot change submittable status of a doctype if documents exist"
    frappe.db.sql("""UPDATE `tabPurchase Form` SET docstatus=0 WHERE docstatus > 0""")
    
    # Update the Doctype to not be submittable
    frappe.db.sql("""UPDATE `tabDocType` SET is_submittable=0 WHERE name='Purchase Form'""")
    
    # Clear cache so Frappe picks up the change
    frappe.clear_cache(doctype='Purchase Form')

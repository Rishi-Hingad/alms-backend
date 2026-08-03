import frappe

def execute():
    # Only execute if Purchase Form exists
    if not frappe.db.table_exists("Purchase Form"):
        return

    # Update all Purchase Form records to docstatus = 0
    # This prevents ValidationError: "Cannot change submittable status of a doctype if documents exist"
    frappe.db.sql("""UPDATE `tabPurchase Form` SET docstatus=0 WHERE docstatus > 0""")
    
    # Update the Doctype to not be submittable
    frappe.db.sql("""UPDATE `tabDocType` SET is_submittable=0 WHERE name='Purchase Form'""")
    
    # If the user checked it via Customize Form, we must delete the Property Setter!
    frappe.db.sql("""DELETE FROM `tabProperty Setter` WHERE doc_type='Purchase Form' AND property='is_submittable'""")
    
    # Clear cache so Frappe picks up the change
    frappe.clear_cache(doctype='Purchase Form')

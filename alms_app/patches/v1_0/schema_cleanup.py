import frappe

def execute():
    # 1. Safely rename the 'Purchase Team form' DocType to 'Purchase Form'
    # This will rename the database table and preserve existing records.
    if frappe.db.exists("DocType", "Purchase Team form"):
        frappe.rename_doc("DocType", "Purchase Team form", "Purchase Form", force=True, ignore_if_exists=True)

    # 2. Completely delete unwanted DocTypes and drop their database tables
    doctypes_to_delete = ["Employee Master", "Management doctype"]
    
    for dt in doctypes_to_delete:
        if frappe.db.exists("DocType", dt):
            # delete_doc handles removing the DocType definition, permissions, and fields
            frappe.delete_doc("DocType", dt, force=1, ignore_missing=True)
            
            # As an extra safety measure to ensure the schema is completely cleaned up on production,
            # we explicitly drop the database table.
            table_name = f"tab{dt}"
            try:
                frappe.db.sql(f"DROP TABLE IF EXISTS `{table_name}`")
            except Exception as e:
                # Table might not exist or already be dropped
                pass

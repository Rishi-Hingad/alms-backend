import frappe
from frappe.installer import add_to_installed_apps

def execute():
    add_to_installed_apps("alms_app", rebuild_website=False)
    print("Added alms_app to installed apps.")
    frappe.db.commit()

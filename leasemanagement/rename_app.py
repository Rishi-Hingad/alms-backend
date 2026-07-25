import frappe
from frappe.installer import add_to_installed_apps, remove_from_installed_apps

def execute():
    installed_apps = frappe.get_installed_apps()
    if "leasemanagement" in installed_apps:
        print("Migrating legacy app name 'leasemanagement' to 'lease_app' in tabInstalled Applications...")
        if "lease_app" not in installed_apps:
            add_to_installed_apps("lease_app", rebuild_website=False)
        remove_from_installed_apps("leasemanagement")
        # Clear cache again to be absolutely sure
        frappe.clear_cache()
        print("Successfully migrated app name to 'lease_app'.")

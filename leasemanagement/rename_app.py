import frappe
from frappe.installer import add_to_installed_apps, remove_from_installed_apps

def execute():
    installed_apps = frappe.get_installed_apps()
    # If leasemanagement is still there (first run)
    if "leasemanagement" in installed_apps:
        print("Migrating legacy app name 'leasemanagement' to 'lease_app' and 'alms_app' in tabInstalled Applications...")
        if "lease_app" not in installed_apps:
            add_to_installed_apps("lease_app", rebuild_website=False)
        if "alms_app" not in installed_apps:
            add_to_installed_apps("alms_app", rebuild_website=False)
        remove_from_installed_apps("leasemanagement")
        frappe.clear_cache()
        print("Successfully migrated app name.")
        return

    # If leasemanagement was already removed in the previous deploy, but alms_app wasn't added
    if "lease_app" in installed_apps and "alms_app" not in installed_apps:
        print("Adding 'alms_app' to tabInstalled Applications...")
        add_to_installed_apps("alms_app", rebuild_website=False)
        frappe.clear_cache()
        print("Successfully added alms_app.")

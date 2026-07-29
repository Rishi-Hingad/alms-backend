import frappe
import json

def run():
    print("Starting cache fix...")
    
    # 1. Update tabDefaultValue
    val = frappe.db.get_value('DefaultValue', {'defkey': 'installed_apps'}, 'defvalue')
    if val:
        val = val.replace('"approval_app"', '"alms_app"').replace('"remittance_app"', '"remittance_tool"')
        frappe.db.sql("UPDATE `tabDefaultValue` SET defvalue = %s WHERE defkey = 'installed_apps'", (val,))
        print("Updated tabDefaultValue.")
        
    # 2. Delete from tabInstalled Application
    frappe.db.sql("DELETE FROM `tabInstalled Application` WHERE name IN ('approval_app', 'remittance_app')")
    print("Deleted from tabInstalled Application.")
    
    # 3. Explicitly clear from cache
    frappe.cache().delete_value("installed_apps")
    frappe.cache().delete_value("global:installed_apps")
    frappe.cache().delete_value("app_hooks")
    frappe.clear_cache()
    print("Cleared Redis caches.")
    
    # 4. Commit
    frappe.db.commit()
    print("Committed database changes.")
    
    print(f"Current installed apps: {frappe.get_installed_apps()}")
    hooks = frappe.get_doc_hooks()
    print(f"Hooks for Patch Log validate: {hooks.get('Patch Log', {}).get('validate', [])}")
    print(f"Global hooks validate: {hooks.get('*', {}).get('validate', [])}")
    print("Fix completed successfully.")

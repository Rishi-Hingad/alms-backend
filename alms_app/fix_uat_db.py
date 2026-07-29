import frappe
import json

def run():
    # Remove old missing apps from Installed Applications
    frappe.db.sql("DELETE FROM `tabInstalled Application` WHERE name IN ('approval_app', 'remittance_app')")
    
    # Update Module Def bindings
    frappe.db.sql("UPDATE `tabModule Def` SET app_name = 'alms_app' WHERE app_name = 'approval_app'")
    frappe.db.sql("UPDATE `tabModule Def` SET app_name = 'remittance_tool' WHERE app_name = 'remittance_app'")
    
    # Update DefaultValue installed_apps JSON
    val = frappe.db.get_value('DefaultValue', {'defkey': 'installed_apps'}, 'defvalue')
    if val:
        val = val.replace('"approval_app"', '"alms_app"').replace('"remittance_app"', '"remittance_tool"')
        frappe.db.sql("UPDATE `tabDefaultValue` SET defvalue = %s WHERE defkey = 'installed_apps'", (val,))
        
    frappe.db.commit()
    print("Successfully removed approval_app and remittance_app from UAT database.")

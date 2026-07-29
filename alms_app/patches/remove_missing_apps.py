import frappe

def execute():
    """Removes old missing apps from the database so bench migrate no longer crashes."""
    frappe.db.sql("DELETE FROM `tabInstalled Application` WHERE name IN ('approval_app', 'remittance_app')")
    
    frappe.db.sql("UPDATE `tabModule Def` SET app_name = 'alms_app' WHERE app_name = 'approval_app'")
    frappe.db.sql("UPDATE `tabModule Def` SET app_name = 'remittance_tool' WHERE app_name = 'remittance_app'")
    
    val = frappe.db.get_value('DefaultValue', {'defkey': 'installed_apps'}, 'defvalue')
    if val:
        val = val.replace('"approval_app"', '"alms_app"').replace('"remittance_app"', '"remittance_tool"')
        frappe.db.sql("UPDATE `tabDefaultValue` SET defvalue = %s WHERE defkey = 'installed_apps'", (val,))

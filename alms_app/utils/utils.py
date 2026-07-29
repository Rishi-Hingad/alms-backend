import frappe
from frappe import _

@frappe.whitelist()
def can_view_alms_doctypes():
    """Check if the current user has the ALMS User role"""
    user = frappe.session.user
    
    if user == "Administrator":
        return True
    
    has_role = frappe.db.exists("Has Role", {
        "parent": user,
        "role": "ALMS User"
    })
    
    return bool(has_role)


@frappe.whitelist()
def get_doctype_module(doctype):
    """Get the module of a specific doctype"""
    try:
        module = frappe.db.get_value("DocType", doctype, "module")
        return module
    except Exception:
        return None
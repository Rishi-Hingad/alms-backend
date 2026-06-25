import frappe

def execute():
    # Clear any dummy.pdf defaults from Custom Field or Property Setter
    cfs = frappe.get_all("Custom Field", filters={"default": ["like", "%dummy%"]})
    for cf in cfs:
        frappe.db.set_value("Custom Field", cf.name, "default", "")

    pss = frappe.get_all("Property Setter", filters={"property": "default", "value": ["like", "%dummy%"]})
    for ps in pss:
        frappe.db.set_value("Property Setter", ps.name, "value", "")

    frappe.db.commit()
    frappe.clear_cache()

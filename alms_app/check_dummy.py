import frappe

def execute():
    frappe.init(site="alms.localhost")
    frappe.connect()
    
    # Check Custom Fields
    cfs = frappe.get_all("Custom Field", filters={"default": ["like", "%dummy%"]}, fields=["name", "dt", "fieldname", "default"])
    for cf in cfs:
        print(f"Custom Field {cf.name} in {cf.dt} has default: {cf.default}")
        
    # Check Property Setters
    pss = frappe.get_all("Property Setter", filters={"property": "default", "value": ["like", "%dummy%"]}, fields=["name", "doc_type", "field_name", "value"])
    for ps in pss:
        print(f"Property Setter {ps.name} in {ps.doc_type} has value: {ps.value}")

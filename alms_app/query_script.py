import frappe
def run():
    frappe.permissions.add_permission('Selected Vendor', 'Finance Team')
    docperm = frappe.get_doc('Custom DocPerm', {'parent': 'Selected Vendor', 'role': 'Finance Team'})
    docperm.read = 1
    docperm.write = 1
    docperm.create = 1
    docperm.save()
    frappe.db.commit()
    print('Granted Create permission to Finance Team on Selected Vendor')

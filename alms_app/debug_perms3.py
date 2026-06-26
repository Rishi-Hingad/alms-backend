import frappe

def run():
    print('Checking Selected Vendor Perms...')
    doc = frappe.get_meta('Selected Vendor')
    for p in doc.permissions:
        print(p.role, p.permlevel, 'read:', p.read, 'write:', p.write, 'create:', p.create)


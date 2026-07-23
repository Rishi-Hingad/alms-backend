import frappe

def run():
    print('Checking Purchase Form Perms for Finance Team...')
    doc = frappe.get_meta('Purchase Form')
    for p in doc.permissions:
        if p.role in ['Finance Team', 'Finance Head']:
            print(p.role, p.permlevel, 'read:', p.read, 'write:', p.write, 'submit:', p.submit, 'amend:', p.amend)


import frappe

def run():
    print('Checking Approval Matrices...')
    matrices = frappe.get_all('Approval Matrix', fields=['name', 'applies_to_doctype'])
    for m in matrices:
        print(m.name, m.applies_to_doctype)


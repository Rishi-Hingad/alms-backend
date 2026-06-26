import frappe

def run():
    print('Checking Conditions for AP-000002 (Purchase Form)...')
    m = frappe.get_doc('Approval Matrix', 'AP-000002')
    print('Conditions:')
    for c in m.get('conditions', []):
        print(c.fieldname, c.operator, c.value)


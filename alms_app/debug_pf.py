import frappe

def run():
    print('Checking all Purchase Forms...')
    docs = frappe.get_all('Purchase Form', fields=['name', 'is_submitted', 'approval_initiated', 'status', 'docstatus'])
    for d in docs:
        print(d.name, 'is_submitted:', d.is_submitted, 'approval_initiated:', d.approval_initiated, 'status:', d.status, 'docstatus:', d.docstatus)


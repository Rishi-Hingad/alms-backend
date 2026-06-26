import frappe

def run():
    print('Checking Approval Entries for Purchase Form...')
    entries = frappe.get_all('Approval Entry', filters={'applied_to_doctype': 'Purchase Form'}, fields=['name', 'status', 'record'])
    print(entries)


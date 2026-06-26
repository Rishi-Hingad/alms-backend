import frappe

def run():
    print('Checking ALL Approval Entries...')
    entries = frappe.get_all('Approval Entry', fields=['name', 'applied_to_doctype', 'status', 'record'])
    print(len(entries))
    for e in entries:
        print(e.applied_to_doctype, e.record, e.status)


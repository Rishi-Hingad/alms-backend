import frappe

def run():
    print('Checking Error Logs...')
    errors = frappe.get_all('Error Log', fields=['name', 'method', 'error'], limit=5, order_by='creation desc')
    for e in errors:
        print(e.method, e.error[:200])


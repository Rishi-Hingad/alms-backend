import frappe

def execute():
    notifications = frappe.get_all('Notification', fields=['name', 'subject', 'message'])
    for n in notifications:
        if 'Company vehicle' in (n.message or ''):
            print('Found in Notification:', n.name)
            print('Subject:', repr(n.subject))
            

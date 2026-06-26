import frappe
frappe.init(site="alms.com")
frappe.connect()
errors = frappe.get_all("Error Log", fields=["error", "method"], order_by="creation desc", limit=2)
for e in errors:
    print(e.error)

import frappe

def execute():
    frappe.init(site="alms.localhost")
    frappe.connect()
    
    logs = frappe.get_all("Error Log", fields=["name", "method", "error"], order_by="creation desc", limit_page_length=20)
    for log in logs:
        print(f"[{log.name}] Method: {log.method}")
        if "Generic Create Approval Entry Error" in log.error or "Approval" in log.method:
            print(f"Error:\n{log.error[:500]}")
        print("----------")

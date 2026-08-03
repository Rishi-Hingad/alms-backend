import frappe
def run_test():
    escalations = frappe.get_all("Escalation", filters={"parent": "LMS-APR22_MAR27-154"}, fields=["*"])
    print(f"Escalations: {escalations}")

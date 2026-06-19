import frappe

def execute():
    entries = frappe.get_all("Approval Entry", filters={"applied_to_doctype": "Invoice Batch", "status": "Pending"}, fields=["name"])
    if not entries:
        print("No pending Invoice Batch entries found.")
        return

    for entry in entries:
        doc = frappe.get_doc("Approval Entry", entry.name)
        ledger = getattr(doc, "approval_ledger", getattr(doc, "approval_entry", []))
        if ledger:
            row = ledger[-1]
            print(f"Entry {entry.name}: Role={row.next_approver_role}, Team={row.next_approver_team}, User={row.next_approver}")
        else:
            print(f"Entry {entry.name}: No ledger items.")

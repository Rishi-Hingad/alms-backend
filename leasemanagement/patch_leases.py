import frappe

def execute():
    # Find all Vehicle Details that are Easy Asset
    vehicles = frappe.get_all("Vehicle Details", filters={"vendor_company": "Easy Asset"})
    count = 0
    for v in vehicles:
        doc = frappe.get_doc("Vehicle Details", v.name)
        # Re-saving triggers the sync which corrects the lease type to Daily Rate
        doc.save(ignore_permissions=True)
        count += 1
    
    frappe.db.commit()
    print(f"Patched {count} Easy Asset leases.")

execute()

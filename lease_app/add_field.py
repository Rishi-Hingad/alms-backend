import frappe

def execute():
    try:
        # Check if field already exists
        if not frappe.db.exists("DocField", {"parent": "Lease Management", "fieldname": "contract_number"}):
            doc = frappe.get_doc("DocType", "Lease Management")
            
            # Create a new DocField dictionary
            new_field = {
                "fieldname": "contract_number",
                "fieldtype": "Link",
                "options": "Contract Master",
                "label": "Contract Number",
                "insert_after": "car_description"
            }
            
            # Append to fields
            doc.append("fields", new_field)
            doc.save()
            
            # Export fixtures or custom fields if necessary, but this saves directly to doc and updates json because it's a custom doctype
            
            print("Field contract_number added to Lease Management")
        else:
            print("Field already exists")
    except Exception as e:
        print("Error: ", e)

execute()

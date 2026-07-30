import frappe

def execute():
    # Fetch all Vendor Master records with their current name, vendor name, and vendor code
    vendors = frappe.get_all("Vendor Master", fields=["name", "vendor_name", "vendor_code"])

    for v in vendors:
        # Ensure both fields exist to avoid errors
        if v.vendor_code and v.vendor_name:
            
            # Construct the new desired ID format
            new_name = f"{v.vendor_code}-{v.vendor_name}"
            
            # Check if the current name is different from the desired new name
            if v.name != new_name:
                try:
                    # Safely rename the document and cascade changes to linked docs
                    frappe.rename_doc("Vendor Master", v.name, new_name, force=True, ignore_permissions=True)
                except Exception as e:
                    frappe.log_error(f"Failed to rename {v.name} to {new_name}", "Rename Vendor Error")

import frappe
import pandas as pd

@frappe.whitelist()
def process_vendor_excel(file_url):
    try:
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        file_path = file_doc.get_full_path()

        df = pd.read_excel(file_path)

        # Example: take first row
        row = df.iloc[0]

        return {
            "financed_amount": row.get("Financed Amount"),
            "location": row.get("Location"),
            "variant": row.get("Variant"),
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Excel Processing Error")
        frappe.throw("Failed to process Excel file")
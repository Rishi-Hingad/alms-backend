import frappe
import requests

@frappe.whitelist()
def on_update_invoice(doc, method):
    # Get previous value from DB
    old_status = doc.get_db_value("payment_status")

    # Trigger ONLY when changed to "Paid"
    if doc.payment_status == "Paid" and old_status != "Paid":

        payload = {
            "doctype_name": doc.batch_name,
            "payment_status": doc.payment_status
        }

        try:
            response = requests.post(
                "https://carleasing-dev.bilakhiagroup.com/api/method/alms_app.api.payment_status.update_payment_status",
                json=payload,
                headers={
                    "Authorization": "token YOUR_API_KEY:YOUR_API_SECRET"
                },
                timeout=10
            )

            if response.status_code != 200:
                frappe.log_error(response.text, "Payment API Failed")
            else:
                frappe.log_error(response.text, "Payment API Sent Successfully")

        except Exception:
            frappe.log_error(frappe.get_traceback(), "Payment API Error")
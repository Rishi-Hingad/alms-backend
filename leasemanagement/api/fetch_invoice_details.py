import frappe
import requests

@frappe.whitelist()
def fetch_invoice(batch_date):
    payload = {
        "batch_date": batch_date
    }

    try:
        API_KEY="aa73190b237609d"
        API_SECRET="f4fd964e0ffabd7"
        response = requests.post(
            "https://carleasing-dev.bilakhiagroup.com//api/method/alms_app.api.invoice_details.get_invoice_batch_details",
            json=payload,
            headers={
                "Authorization": f"token {API_KEY}:{API_SECRET}"
            },
            timeout=10
        )

        if response.status_code != 200:
            frappe.log_error(
                title="Fetch Invoice Details API Failed",
                message=response.text
            )
            return {"status": "error", "message": "API Failed"}
        else:
            frappe.log_error(title="Fetch Invoice Details API Sent Successfully", message=response.text)
            return response.json()

    except Exception:
        frappe.log_error(title="Fetch Invoice Details API Error", message=frappe.get_traceback())
        return {"status": "error", "message": "Exception occurred"}
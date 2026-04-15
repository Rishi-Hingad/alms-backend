import frappe
import requests


@frappe.whitelist()
def on_update_invoice(doc, method):
	# Get previous value from DB
	# old_status = doc.get_db_value("payment_status")
	old_doc = doc.get_doc_before_save()
	old_status = old_doc.payment_status if old_doc else None

	# Trigger ONLY when changed to "Paid"
	if doc.payment_status == "Paid" and old_status != "Paid":
		payload = {"doctype_name": doc.batch_name, "payment_status": doc.payment_status}
		try:
			api_key = frappe.conf.car_leasing_api_key
			api_secret = frappe.conf.car_leasing_api_secret
			api_url = frappe.conf.car_leasing_payment_api_base_url
			response = requests.post(
				api_url,
				json=payload,
				headers={"Authorization": f"token {api_key}:{api_secret}"},
				timeout=10,
			)
			if response.status_code != 200:
				frappe.log_error(
					title="Payment API Failed",
					message=f"Payload: {payload}\nResponse: {response.text[:300]}",
					reference_doctype=doc.doctype,
					reference_name=doc.name,
				)
			# else:
			# 	frappe.log_error(
			# 		title="Payment API Sent Successfully",
			# 		message=f"Payload: {payload}\nResponse: {response.text[:300]}",
			# 	)

		except Exception:
			frappe.log_error(title="Payment API Error", message=frappe.get_traceback())

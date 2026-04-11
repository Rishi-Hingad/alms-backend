import frappe
import requests
from dateutil.relativedelta import relativedelta
from frappe.utils import getdate, nowdate

from leasemanagement.api.invoice_details import _link_invoice_to_lease, map_invoice_row

# from frappe.exceptions import DuplicateEntryError


@frappe.whitelist()
def fetch_invoice(batch_date):
	payload = {"batch_date": batch_date}

	try:
		API_KEY = "aa73190b237609d"
		API_SECRET = "f4fd964e0ffabd7"

		response = requests.post(
			"https://carleasing-dev.bilakhiagroup.com/api/method/alms_app.api.invoice_details.get_invoice_batch_details",
			json=payload,
			headers={"Authorization": f"token {API_KEY}:{API_SECRET}"},
			timeout=15,
		)

		if response.status_code != 200:
			frappe.log_error("API Failed", response.text)
			return {"status": "Error", "message": "API Failed"}

		data = response.json()
		# data = {
		# 	"message": [
		# 		{
		# 			"name": "BATCH-New-01",
		# 			"batch_date": "2026-05-01",
		# 			"vendor_name": "PQR Vendor",
		# 			"company": "PQR Pvt Ltd",
		# 			"total_value_of_rental_charges":9999,
		# 			"total_value_of_fleet_charges":8888,
		# 			"total_value_of_rto":7777,
		# 			"total_value_of_insurance":97879,
		# 			"total_value_of_company_contribution":90909,
		# 			"total_value_of_employee_contribution":564656,
		# 			"total_value_of_all":676757,
		# 			"rows": [
		# 				{
		# 					"contract_number": "CONT-2",
		# 					"company": "PQR Pvt Ltd",
		# 					"employee_name": "Rahul Mehta",
		# 					"cost_center": "CC-10",
		# 					"vehicle_details": "Car - GJ01AB1111",
		# 					"billing_date": "2026-05-01",

		# 					"month": "April",
		# 					"installment_no": "1",

		# 					"invoice_value_a": 11000,
		# 					"invoice_value_b": 2100,
		# 					"invoice_value_c": 1300,
		# 					"invoice_value_d": 600,

		# 					"total_invoice_value": 15000,

		# 					"company_contribution": 9000,
		# 					"employee_contribution": 6000
		# 				},
		# 				{
		# 					"contract_number": "CONqwerty-1",
		# 					"company": "PQR Pvt Ltd",
		# 					"employee_name": "Neha Patel",
		# 					"cost_center": "CC-11",
		# 					"vehicle_details": "Car - GJ02CD2222",

		# 					"invoice_date_from": "2026-04-01",
		# 					"invoice_date_to": "2026-04-30",
		# 					"billing_date": "2026-05-01",

		# 					"month": "April",
		# 					"installment_no": "2",

		# 					"invoice_value_a": 13000,
		# 					"invoice_value_b": 2600,
		# 					"invoice_value_c": 1700,
		# 					"invoice_value_d": 800,

		# 					"total_invoice_value": 18100,

		# 					"company_contribution": 10000,
		# 					"employee_contribution": 8100
		# 				}
		# 			]
		# 		},
		# 		{
		# 			"name": "BATCH-103",
		# 			"batch_date": "2026-05-02",
		# 			"vendor_name": "LMN Vendor",
		# 			"company": "LMN Pvt Ltd",
		# 			"rows": [
		# 				{
		# 					"contract_number": "CON-012",
		# 					"company": "LMN Pvt Ltd",
		# 					"employee_name": "Amit Shah",
		# 					"cost_center": "CC-12",
		# 					"vehicle_details": "Car - MH01EF3333",

		# 					"invoice_date_from": "2026-04-01",
		# 					"invoice_date_to": "2026-04-30",
		# 					"billing_date": "2026-05-02",

		# 					"month": "April",
		# 					"installment_no": "1",

		# 					"invoice_value_a": 9500,
		# 					"invoice_value_b": 1400,
		# 					"invoice_value_c": 1100,
		# 					"invoice_value_d": 400,

		# 					"total_invoice_value": 12400,

		# 					"company_contribution": 7000,
		# 					"employee_contribution": 5400
		# 				},
		# 				{
		# 					"contract_number": "CON-013",
		# 					"company": "LMN Pvt Ltd",
		# 					"employee_name": "Priya Desai",
		# 					"cost_center": "CC-13",
		# 					"vehicle_details": "Car - KA05GH4444",

		# 					"invoice_date_from": "2026-04-01",
		# 					"invoice_date_to": "2026-04-30",
		# 					"billing_date": "2026-05-02",

		# 					"month": "April",
		# 					"installment_no": "3",

		# 					"invoice_value_a": 14000,
		# 					"invoice_value_b": 3000,
		# 					"invoice_value_c": 2000,
		# 					"invoice_value_d": 1000,

		# 					"total_invoice_value": 20000,

		# 					"company_contribution": 12000,
		# 					"employee_contribution": 8000
		# 				}
		# 			]
		# 		}
		# 	]
		# }
		# data = {"message":[]}
		batches = data.get("message", [])

		if not batches:
			return {"status": "Ok", "message": "No Batches returned for this date.", "results": []}

		results = []

		for batch in batches:
			result = _upsert_invoice_batch(batch)
			results.append(result)

		return {"status": "Ok", "results": results}

	except Exception:
		frappe.log_error("Fetch Invoice Error", frappe.get_traceback())
		return {"status": "Error", "message": "Exception occurred"}


def _upsert_invoice_batch(batch):
	"""
	Upsert a single batch into Invoice Details.
	"""
	batch_name = batch.get("name")
	batch_date = batch.get("batch_date")
	vendor_name = batch.get("vendor_name")
	company = batch.get("company")
	total_rental = batch.get("total_value_of_rental_charges", "")
	total_fleet = batch.get("total_value_of_fleet_charges", "")
	total_rto = batch.get("total_value_of_rto", "")
	total_ins = batch.get("total_value_of_insurance", "")
	total_co = batch.get("total_value_of_company_contribution", "")
	total_emp = batch.get("total_value_of_employee_contribution", "")
	total_all = float(batch.get("total_value_of_all", 0) or 0)
	rows = batch.get("rows", [])

	excel_file_url = None
	invoice_attach_url = None

	excel_data = batch.get("excel_file")  # {"file_name": "...", "content": "<base64>"}
	pdf_data = batch.get("invoice_attachment")  # same structure or null

	if excel_data and excel_data.get("content"):
		excel_file_url = _save_base64_file(
			file_name=excel_data["file_name"],
			b64_content=excel_data["content"],
			doctype="Invoice Details",
		)

	if pdf_data and pdf_data.get("content"):
		invoice_attach_url = _save_base64_file(
			file_name=pdf_data["file_name"],
			b64_content=pdf_data["content"],
			doctype="Invoice Details",
		)

	# ------------------------------------------------------------------
	# Step 2: Check if record already exists
	# ------------------------------------------------------------------
	existing_name = frappe.db.get_value(
		"Invoice Details",
		filters={
			"batch_name": batch_name,
			"batch_date": batch_date,
			"vendor_name": vendor_name,
			"company": company,
		},
		fieldname="name",
	)

	# ------------------------------------------------------------------
	# Step 3a: Create new record
	# ------------------------------------------------------------------
	if not existing_name:
		doc = frappe.new_doc("Invoice Details")
		doc.batch_name = batch_name
		doc.batch_date = batch_date
		doc.vendor_name = vendor_name
		doc.company = company
		doc.total_value_of_rental_charges = total_rental
		doc.total_value_of_fleet_charges = total_fleet
		doc.total_value_of_rto = total_rto
		doc.total_value_of_insurance = total_ins
		doc.total_value_of_all = total_all
		doc.total_value_of_company_contribution = total_co
		doc.total_value_of_employee_contribution = total_emp

		# Attach files if decoded successfully
		if excel_file_url:
			doc.excel_file = excel_file_url
		if invoice_attach_url:
			doc.invoice_attachment = invoice_attach_url

		for row in rows:
			doc.append("rows", map_invoice_row(row))

		_fill_missing_dates(doc)

		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		# Link file records to the new doc
		if excel_file_url:
			_relink_file_to_doc(excel_file_url, "Invoice Details", doc.name)
		if invoice_attach_url:
			_relink_file_to_doc(invoice_attach_url, "Invoice Details", doc.name)

		# Run lease linking (same as your existing flow)
		_link_invoice_to_lease(doc)

		return {
			"batch": batch_name,
			"status": "Created",
			"docname": doc.name,
			"rows_added": len(rows),
		}

	# ------------------------------------------------------------------
	# Step 3b: Record exists — append only missing child rows
	# ------------------------------------------------------------------
	doc = frappe.get_doc("Invoice Details", existing_name)

	# Build lookup key: contract_number + installment_no
	existing_keys = {(r.contract_number, str(r.installment_no)) for r in doc.rows}

	new_rows = [
		row
		for row in rows
		if (row.get("contract_number"), str(row.get("installment_no"))) not in existing_keys
	]

	if not new_rows:
		return {
			"batch": batch_name,
			"status": "No_Change",
			"docname": existing_name,
		}

	for row in new_rows:
		doc.append("rows", map_invoice_row(row))

	_fill_missing_dates(doc)

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	# Link only the newly added rows to leases
	_link_invoice_to_lease(doc)

	return {
		"batch": batch_name,
		"status": "Updated",
		"docname": existing_name,
		"rows_added": len(new_rows),
	}


def _fill_missing_dates(doc):
	"""
	Mirror your existing date-fill logic for child rows.
	"""
	for child in doc.rows:
		invoice_from = getdate(child.invoice_from_date) if child.invoice_from_date else None
		invoice_to = getdate(child.invoice_to_date) if child.invoice_to_date else None
		billing = getdate(child.billing_date) if child.billing_date else None

		if (invoice_from is None or invoice_to is None) and billing:
			child.invoice_from_date = billing
			child.invoice_to_date = billing + relativedelta(day=31)


def _save_base64_file(file_name: str, b64_content: str, doctype: str, is_private: int = 1):
	"""
	Decode a base64 string and save it as a Frappe File doc.
	Returns the file_url on success, or None on failure.
	"""
	import base64

	try:
		content = base64.b64decode(b64_content)
	except Exception:
		frappe.log_error(title=f"Base64 decode failed for {file_name}", message=frappe.get_traceback())
		return None

	file_doc = frappe.new_doc("File")
	file_doc.file_name = file_name
	file_doc.is_private = is_private
	file_doc.attached_to_doctype = doctype
	file_doc.attached_to_name = "temp"  # re-linked after parent doc is saved
	file_doc.content = content
	file_doc.save(ignore_permissions=True)

	return file_doc.file_url


def _relink_file_to_doc(file_url: str, doctype: str, docname: str):
	"""
	After the parent doc is inserted, point the File record at it.
	"""
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if file_name:
		frappe.db.set_value(
			"File",
			file_name,
			{
				"attached_to_doctype": doctype,
				"attached_to_name": str(docname),
			},
		)
		frappe.db.commit()


def run_daily_invoice_fetch():
	"""
	Scheduler entry point — runs daily at midnight
	"""
	try:
		batch_date = nowdate()  # YYYY-MM-DD (current date)
		fetch_invoice(batch_date)

	except Exception:
		frappe.log_error("Daily Invoice Scheduler Failed", frappe.get_traceback())

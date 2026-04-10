import json
from datetime import date, datetime

import frappe
from dateutil.relativedelta import relativedelta
from frappe.utils import getdate
from frappe.utils.file_manager import save_file


@frappe.whitelist(allow_guest=True)
def insert_invoice_batch_data():
	# ------------------------------------------------------------------
	# 1. Read uploaded files from multipart form
	# ------------------------------------------------------------------
	files = frappe.request.files
	excel_file_obj = files.get("excel_file")
	invoice_attachment_obj = files.get("invoice_attachment")

	if not excel_file_obj:
		frappe.throw("excel_file is required (Invoice Excel).", frappe.ValidationError)

	_validate_extension(excel_file_obj.filename, (".xlsx", ".xls"), "excel_file")

	if not invoice_attachment_obj:
		frappe.throw("invoice_attachment (PDF) is required.", frappe.ValidationError)

	if invoice_attachment_obj:
		_validate_extension(invoice_attachment_obj.filename, (".pdf",), "invoice_attachment")

	# ------------------------------------------------------------------
	# 2. Read form fields
	# ------------------------------------------------------------------
	form = frappe.form_dict

	required_fields = {
		"vendor_name": "Vendor Name",
		"company": "Company",
		"batch_name": "Batch Name",
		"batch_date": "Batch Date",
		"total_value_of_rental_charges": "Total Rental Charges",
		"total_value_of_fleet_charges": "Total Fleet Charges",
		"total_value_of_rto": "Total RTO",
		"total_value_of_insurance": "Total Insurance",
		"total_value_of_company_contribution": "Company Contribution",
		"total_value_of_employee_contribution": "Employee Contribution",
		"total_value_of_all": "Total Value",
		"rows": "Rows Data",
	}

	missing_fields = []

	for field_key, field_label in required_fields.items():
		value = form.get(field_key)

		if value in (None, "", []):
			missing_fields.append(field_label)

	if missing_fields:
		frappe.throw(f"Missing required fields: {', '.join(missing_fields)}", frappe.ValidationError)

	vendor_name = form.get("vendor_name", "")
	company = form.get("company", "")
	batch_name = form.get("name", "")
	batch_date = form.get("batch_date", "")
	total_rental = form.get("total_value_of_rental_charges", "")
	total_fleet = form.get("total_value_of_fleet_charges", "")
	total_rto = form.get("total_value_of_rto", "")
	total_ins = form.get("total_value_of_insurance", "")
	total_co = form.get("total_value_of_company_contribution", "")
	total_emp = form.get("total_value_of_employee_contribution", "")
	rows_raw = form.get("rows", "[]")

	try:
		total_all = float(form.get("total_value_of_all", 0) or 0)
	except (ValueError, TypeError):
		frappe.throw("total_value_of_all must be a valid number.", frappe.ValidationError)

	try:
		rows_data = json.loads(rows_raw) if rows_raw else []
		if not isinstance(rows_data, list):
			raise ValueError("rows must be a JSON array.")
	except (json.JSONDecodeError, ValueError) as exc:
		frappe.throw(f"Invalid rows JSON: {exc}", frappe.ValidationError)

	# ------------------------------------------------------------------
	# 3. Save files WITHOUT linking to any doc yet (dn=None)
	# ------------------------------------------------------------------
	excel_saved = _save_uploaded_file(excel_file_obj, doctype="Invoice Details", is_private=1)

	pdf_saved = None
	if invoice_attachment_obj:
		pdf_saved = _save_uploaded_file(invoice_attachment_obj, doctype="Invoice Details", is_private=1)

	# ------------------------------------------------------------------
	# 4. Build and insert the Invoice Details document
	# ------------------------------------------------------------------
	doc = frappe.new_doc("Invoice Details")

	doc.vendor_name = vendor_name
	doc.company = company
	doc.batch_name = batch_name
	doc.batch_date = batch_date
	doc.excel_file = excel_saved.file_url
	doc.invoice_attachment = pdf_saved.file_url if pdf_saved else None
	doc.total_value_of_rental_charges = total_rental
	doc.total_value_of_fleet_charges = total_fleet
	doc.total_value_of_rto = total_rto
	doc.total_value_of_insurance = total_ins
	doc.total_value_of_all = total_all
	doc.total_value_of_company_contribution = total_co
	doc.total_value_of_employee_contribution = total_emp

	for row in rows_data:
		mapped_row = map_invoice_row(row)
		doc.append("rows", mapped_row)
		# doc.append("rows", row)

	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	# ------------------------------------------------------------------
	# 5. Link saved files to the new document
	# ------------------------------------------------------------------
	_attach_file_to_doc(excel_saved, "Invoice Details", doc.name)
	if pdf_saved:
		_attach_file_to_doc(pdf_saved, "Invoice Details", doc.name)

	for child in doc.rows:
		invoice_date = getdate(child.billing_date) if child.billing_date else None
		invoice_from_date = getdate(child.invoice_from_date) if child.invoice_from_date else None
		invoice_to_date = getdate(child.invoice_to_date) if child.invoice_to_date else None

		if invoice_from_date is None or invoice_to_date is None:
			if invoice_date:
				child.invoice_from_date = invoice_date
				child.invoice_to_date = invoice_date + relativedelta(day=31)
	# validate lease
	_link_invoice_to_lease(doc)

	# ------------------------------------------------------------------
	# 6. Return success response
	# ------------------------------------------------------------------
	return {
		"message": "Invoice Details Created Successfully",
		"invoice_name": doc.name,
		"excel_file_url": excel_saved.file_url,
		"invoice_attachment_url": pdf_saved.file_url if pdf_saved else None,
	}


# ──────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────
def map_invoice_row(row):
	from frappe.utils import get_last_day, getdate

	billing_date = getdate(row.get("billing_date")) if row.get("billing_date") else None

	return {
		"contract_number": row.get("contract_number"),
		"company": row.get("company"),
		"company_code": "",
		# "employee_code": row.get("employee_name"),  # ⚠️ confirm this mapping
		"employee_code": "",
		"cost_center": row.get("cost_center"),
		"vehicle_details": row.get("vehicle_details"),
		# Dates
		"billing_date": billing_date,
		"invoice_from_date": row.get("invoice_date_from"),
		"invoice_to_date": row.get("invoice_date_to"),
		# Optional: auto derive if missing
		# "invoice_from_date": billing_date.replace(day=1) if billing_date else None,
		# "invoice_to_date": get_last_day(billing_date) if billing_date else None,
		# Financials
		"invoice_amount": row.get("total_invoice_value"),
		"invoice_value_a": row.get("invoice_value_a"),
		"invoice_value_b": row.get("invoice_value_b"),
		"invoice_value_c": row.get("invoice_value_c"),
		"invoice_value_d": row.get("invoice_value_d"),
		# Contributions
		"company_contribution": row.get("company_contribution"),
		"employee_contribution": row.get("employee_contribution"),
		# Other
		"installment_no": row.get("installment_no"),
		"month": row.get("month"),
	}


def _validate_extension(filename: str, allowed: tuple, field_label: str):
	if not filename:
		frappe.throw(f"{field_label}: filename is missing.", frappe.ValidationError)
	ext = ("." + filename.rsplit(".", 1)[-1]).lower() if "." in filename else ""
	if ext not in allowed:
		frappe.throw(
			f"{field_label} must be one of {allowed}. Received: '{filename}'",
			frappe.ValidationError,
		)


def _save_uploaded_file(file_obj, doctype: str, is_private: int = 1):
	content = file_obj.read()
	if not content:
		frappe.throw(
			f"Uploaded file '{file_obj.filename}' is empty.",
			frappe.ValidationError,
		)

	# Save file to disk manually
	file_doc = frappe.new_doc("File")
	file_doc.file_name = file_obj.filename
	file_doc.is_private = is_private
	file_doc.attached_to_doctype = doctype
	file_doc.attached_to_name = "temp"  # ← temporary placeholder, updated later
	file_doc.content = content
	file_doc.save(ignore_permissions=True)

	return file_doc


def _attach_file_to_doc(file_doc, doctype: str, docname: str):
	"""Link a File record to the given document after insert."""
	frappe.db.set_value(
		"File",
		file_doc.name,
		{
			"attached_to_doctype": doctype,
			"attached_to_name": str(docname),
		},
	)
	frappe.db.commit()


# validations */
def _link_invoice_to_lease(doc):
	for child in doc.rows:
		contract_no = child.contract_number
		invoice_date = getdate(child.billing_date) if child.billing_date else None
		invoice_from_date = getdate(child.invoice_from_date) if child.invoice_from_date else None
		invoice_to_date = getdate(child.invoice_to_date) if child.invoice_to_date else None

		# ----------------------------------------
		# 1. Contract Number Check
		# ----------------------------------------
		car = frappe.db.get_value(
			"Car Description Master",
			{"contract_details": contract_no},
			["name", "vendor", "company", "employee_code"],
			as_dict=1,
		)

		if not car:
			child.lease_status = "Contract Not Found"
			continue

		car_company_code = frappe.db.get_value("Company Master", {"name": car.company}, "company_code")

		# ----------------------------------------
		# 2. Company Match
		# ----------------------------------------
		if str(car_company_code) != str(child.company_code):
			child.lease_status = "Company Mismatch"
			continue

		# ----------------------------------------
		# 3. Employee Code Match
		# ----------------------------------------
		if str(car.employee_code) != str(child.employee_code):
			child.lease_status = "Employee Mismatch"
			continue

		# ----------------------------------------
		# 4. Find Lease Management
		# ----------------------------------------
		leases = frappe.get_all(
			"Lease Management",
			filters={"car_description": car.name, "vendor": car.vendor, "company": car.company},
			fields=["name", "agreement_start_date", "agreement_end_date", "status"],
		)

		if not leases:
			child.lease_status = "Lease Not Found"
			continue

		matched = False
		if len(leases) > 0:
			for lease in leases:
				lease_doc = frappe.get_doc("Lease Management", lease.name)
				if lease.status == "Discarded":
					if lease_doc.modifications:
						temp = frappe.db.get_value(
							"Lease Management",
							lease_doc.modifications[0].modified_lease,
							"agreement_start_date",
						)
						modified_date = date(temp.year, temp.month, temp.day) - relativedelta(days=1)
						if invoice_date:
							if not (
								lease.agreement_start_date <= invoice_from_date
								and invoice_to_date <= modified_date
							):
								child.lease_status = "Date Out of Range for lease " + str(lease_doc.name)
								continue
						lease_doc.append(
							"invoice_details",
							{
								"amount": child.invoice_amount,
								"from_date": child.invoice_from_date,
								"to_date": child.invoice_to_date,
							},
						)

						lease_doc.save(ignore_permissions=True)

						child.lease_reference = lease.name
						child.lease_status = "Linked"

						matched = True
						break
				if lease.status == "Modified":
					if invoice_date:
						if not (
							lease_doc.agreement_start_date <= invoice_from_date
							and invoice_to_date <= lease_doc.agreement_end_date
						):
							child.lease_status = "Date Out of Range for lease " + str(lease_doc.name)
							continue
					lease_doc.append(
						"invoice_details",
						{
							"amount": child.invoice_amount,
							"from_date": child.invoice_from_date,
							"to_date": child.invoice_to_date,
						},
					)

					lease_doc.save(ignore_permissions=True)

					child.lease_reference = lease.name
					child.lease_status = "Linked"

					matched = True
					break

				if lease.status == "Terminated":
					child.lease_status = "Terminated Lease"
					if invoice_date:
						if not (
							lease_doc.agreement_start_date <= invoice_from_date
							and invoice_to_date <= lease_doc.termination_date
						):
							child.lease_status = "Date Out of Range for lease " + str(lease_doc.name)
							continue
					lease_doc.append(
						"invoice_details",
						{
							"amount": child.invoice_amount,
							"from_date": child.invoice_from_date,
							"to_date": child.invoice_to_date,
						},
					)

					lease_doc.save(ignore_permissions=True)

					child.lease_reference = lease.name
					child.lease_status = "Linked"

					matched = True
					break

		# for lease in leases:
		# 	# ----------------------------------------
		# 	# 5. Date Validation
		# 	# ----------------------------------------
		# 	if invoice_date:
		# 		if not (lease.agreement_start_date <= invoice_date <= lease.agreement_end_date):
		# 			child.lease_status = "Date Out of Range"
		# 			continue

		# 	# ----------------------------------------
		# 	# 6. linking successful
		# 	# ----------------------------------------
		# 	lease_doc = frappe.get_doc("Lease Management", lease.name)

		# 	lease_doc.append(
		# 		"invoice_details",
		# 		{
		# 			"amount": child.invoice_amount,
		# 			"from_date": child.invoice_from_date,
		# 			"to_date": child.invoice_to_date,
		# 		},
		# 	)

		# 	lease_doc.save(ignore_permissions=True)

		# 	child.lease_reference = lease.name
		# 	child.lease_status = "Linked"

		# 	matched = True
		# 	break

		if not matched and not child.lease_status:
			child.lease_status = "Lease Not Found"

	# Save updates
	doc.save(ignore_permissions=True)

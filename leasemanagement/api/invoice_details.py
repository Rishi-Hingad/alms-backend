import json

import frappe
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

	if invoice_attachment_obj:
		_validate_extension(invoice_attachment_obj.filename, (".pdf",), "invoice_attachment")

	# ------------------------------------------------------------------
	# 2. Read form fields
	# ------------------------------------------------------------------
	form = frappe.form_dict

	vendor_name = form.get("vendor_name", "")
	# return vendor_name
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
		doc.append("rows", row)

	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	# ------------------------------------------------------------------
	# 5. Link saved files to the new document
	# ------------------------------------------------------------------
	_attach_file_to_doc(excel_saved, "Invoice Details", doc.name)
	if pdf_saved:
		_attach_file_to_doc(pdf_saved, "Invoice Details", doc.name)

	# validate lease
	_link_invoice_to_lease(doc)

	# ------------------------------------------------------------------
	# 6. Return success response
	# ------------------------------------------------------------------
	return {
		"message": "Invoice Details created successfully",
		"invoice_name": doc.name,
		"excel_file_url": excel_saved.file_url,
		"invoice_attachment_url": pdf_saved.file_url if pdf_saved else None,
	}


# ──────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────


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
	from frappe.utils import getdate

	for child in doc.rows:
		contract_no = child.contract_number
		invoice_date = getdate(child.billing_date) if child.billing_date else None

		# ----------------------------------------
		# 1. Contract Number Check
		# ----------------------------------------
		car = frappe.db.get_value(
			"Car Description Master",
			{"contract_details": contract_no},
			["name", "vendor", "company", "employee_code"],
			as_dict=1,
		)

		car_company_code = frappe.db.get_value("Company Master", {"name": car.company}, "company_code")

		if not car:
			child.lease_status = "Contract Not Found"
			continue

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
			fields=["name", "agreement_start_date", "agreement_end_date"],
		)

		if not leases:
			child.lease_status = "Lease Not Found"
			continue

		matched = False

		for lease in leases:
			# ----------------------------------------
			# 5. Date Validation
			# ----------------------------------------
			if invoice_date:
				if not (lease.agreement_start_date <= invoice_date <= lease.agreement_end_date):
					child.lease_status = "Date Out of Range"
					continue

			# ----------------------------------------
			# 6. linking successful
			# ----------------------------------------
			lease_doc = frappe.get_doc("Lease Management", lease.name)

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

		if not matched and not child.lease_status:
			child.lease_status = "Lease Not Found"

	# Save updates
	doc.save(ignore_permissions=True)

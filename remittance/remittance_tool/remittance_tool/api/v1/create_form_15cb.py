import frappe
from frappe import _


def _rate_signature(entry):
	"""Return (exchange_rate, tax_rate) rounded to 4 dp for grouping comparisons."""
	kurse = round(float(entry.kurse or 0), 4)
	qsshb = float(entry.qsshb or 0)
	qbshb = float(entry.qbshb or 0)
	tax_rate = round((qbshb / qsshb) * 100, 4) if qsshb else 0.0
	return kurse, tax_rate


def _assert_same_rate_group(fbl1n_docs):
	"""All selected RE KR entries must share the same Exchange Rate AND Tax Rate.

	A Form 15 CB is one certificate for one rate combination — mixing rates would
	produce wrong tax computations on the certificate.
	"""
	if len(fbl1n_docs) < 2:
		return

	first = fbl1n_docs[0]
	first_kurse, first_rate = _rate_signature(first)

	for d in fbl1n_docs[1:]:
		kurse, rate = _rate_signature(d)
		if kurse != first_kurse:
			frappe.throw(
				_(
					"All selected entries must share the same Exchange Rate. "
					"Conflict: {0} has rate {1}, {2} has rate {3}."
				).format(first.name, first_kurse, d.name, kurse)
			)
		if rate != first_rate:
			frappe.throw(
				_(
					"All selected entries must share the same Tax Rate (qbshb / qsshb). "
					"Conflict: {0} has rate {1}%, {2} has rate {3}%."
				).format(first.name, first_rate, d.name, rate)
			)


@frappe.whitelist()
def get_fbl1n_entries(bukrs, lifnr, posting_date=None, from_date=None, to_date=None):
	"""
	Return RE KR Entry records matching company code, vendor number, and an
	optional posting-date filter. Excludes entries already marked as used.

	Date filter resolution (first match wins):
	  - posting_date           -> exact match (legacy behavior)
	  - from_date AND to_date  -> between [from_date, to_date]
	  - from_date only         -> >= from_date
	  - to_date only           -> <= to_date
	  - none                   -> no posting-date filter
	"""
	filters = {
		"bukrs": bukrs,
		"is_used": 0,
		"is_outdated": 0,
	}

	if posting_date:
		filters["budat"] = posting_date
	elif from_date and to_date:
		filters["budat"] = ["between", [from_date, to_date]]
	elif from_date:
		filters["budat"] = [">=", from_date]
	elif to_date:
		filters["budat"] = ["<=", to_date]

	entries = frappe.get_all(
		"RE KR Entry",
		filters=filters,
		fields=[
			"name",
			"bukrs",
			"lifnr",
			"name1",
			"belnr",
			"xblnr",
			"blart",
			"bldat",
			"budat",
			"qsshb",
			"qbshb",
			"wrshb",
			"dmshb",
			"waers",
			"kurse",
			"punch_time",
		],
		order_by="budat desc, bldat desc",
	)

	normalized_input = lifnr.lstrip("0")
	entries = [e for e in entries if e.lifnr and e.lifnr.lstrip("0") == normalized_input]

	return entries


@frappe.whitelist()
def create_form_15cb(company, vendor, selected_entries):
	"""
	Create a Remittance Form 15 CB from selected RE KR Entry records.

	Args:
		company: Remittance Company name (link value)
		vendor: Remittance Vendor name (link value)
		selected_entries: JSON list of RE KR Entry names
	"""
	if isinstance(selected_entries, str):
		selected_entries = frappe.parse_json(selected_entries)

	if not selected_entries:
		frappe.throw(_("Please select at least one entry"))

	# Duplicate check: ensure none of the selected FBL1N entries are already linked
	# to an existing Remittance Form 15 CB (via the invoices child table).
	already_used = frappe.get_all(
		"Remittance Invoice",
		filters={"fbl1n_entry": ["in", selected_entries]},
		fields=["fbl1n_entry", "parent"],
	)
	if already_used:
		details = ", ".join(f"{row.fbl1n_entry} (used in {row.parent})" for row in already_used)
		frappe.throw(
			_("These SAP FBL1N entries are already linked to other Form 15 CB records: {0}").format(details)
		)

	fbl1n_docs = []
	for entry_name in selected_entries:
		if frappe.db.exists("RE KR Entry", entry_name):
			fbl1n_docs.append(frappe.get_doc("RE KR Entry", entry_name))

	if not fbl1n_docs:
		frappe.throw(_("No valid SAP FBL1N entries found"))

	_assert_same_rate_group(fbl1n_docs)

	form_15cb = frappe.new_doc("Remittance Form 15 CB")
	form_15cb.company = company
	form_15cb.vendor = vendor
	for fbl1n in fbl1n_docs:
		row = form_15cb.append("invoices", {})
		row.fbl1n_entry = fbl1n.name
		row.sap_document_no = fbl1n.belnr
		row.invoice_no = fbl1n.xblnr
		row.document_type = fbl1n.blart
		row.document_date = fbl1n.bldat
		row.qsshb = fbl1n.qsshb or 0
		row.zzqsshb = fbl1n.zzqsshb or 0
		row.qbshb = fbl1n.qbshb or 0
		row.zzqbshb = fbl1n.zzqbshb or 0
		row.wrshb = fbl1n.wrshb or 0
		row.dmshb = fbl1n.dmshb or 0
		row.waers = fbl1n.waers or ""
		row.kurse = fbl1n.kurse or 0
		row.hwaer = fbl1n.hwaer or ""

	form_15cb.insert(ignore_permissions=True, ignore_mandatory=True)

	# Mark each linked RE KR Entry as used
	for fbl1n in fbl1n_docs:
		frappe.db.set_value(
			"RE KR Entry",
			fbl1n.name,
			{"form_15cb": form_15cb.name, "is_used": 1},
			update_modified=False,
		)

	frappe.db.commit()

	return {
		"name": form_15cb.name,
		"invoices_count": len(form_15cb.invoices),
	}

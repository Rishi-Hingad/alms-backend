import frappe


@frappe.whitelist()
def create_remittance_from_sap(payload):
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)

	# Expected payload keys (example): company_code, vendor_code, invoices, amounts, tax_details
	remittance = frappe.get_doc({"doctype": "Remittance"})

	for key, value in payload.items():
		if key in ("invoices", "tax_documents"):
			continue
		if hasattr(remittance, key):
			remittance.set(key, value)

	for inv in payload.get("invoices", []):
		remittance.append("invoices", inv)

	for tax_doc in payload.get("tax_documents", []):
		remittance.append("tax_documents", tax_doc)

	remittance.insert()
	return remittance.name

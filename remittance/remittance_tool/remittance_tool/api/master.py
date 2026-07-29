import frappe

ALLOWED_MASTER_DOCTYPES = {
	"Remittance Company",
	"Remittance Vendor",
	"Remittance Country",
	"Remittance Currency",
	"Remittance Purpose Code",
	"Remittance Nature",
	"Remittance Bank Branch",
	"Remittance Tax Document Type",
}


@frappe.whitelist()
def get_master_data(doctype, fields=None, filters=None, limit=200):
	if doctype not in ALLOWED_MASTER_DOCTYPES:
		frappe.throw("Invalid master doctype")
	if not fields:
		fields = ["name"]
	return frappe.get_all(doctype, fields=fields, filters=filters, limit=limit)


@frappe.whitelist()
def upsert_master_data(doctype, data):
	if doctype not in ALLOWED_MASTER_DOCTYPES:
		frappe.throw("Invalid master doctype")
	if isinstance(data, str):
		data = frappe.parse_json(data)
	name = data.get("name")
	if name and frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		doc.update(data)
		doc.save()
		return doc.name
	doc = frappe.get_doc({"doctype": doctype, **data})
	doc.insert()
	return doc.name

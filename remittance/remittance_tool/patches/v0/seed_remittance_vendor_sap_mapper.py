"""Seed SAP Mapper for Remittance Vendor with the canonical SAP → ERP field mapping.

Re-runnable: rebuilds the mapping rows from the canonical source below so admins
can re-apply this patch (via bench execute) after manual edits, if desired.
"""
import frappe


TARGET_DOCTYPE = "Remittance Vendor"

# SAP technical field name -> Remittance Vendor fieldname
SAP_TO_ERP = [
	("LIFNR", "vendor_code"),
	("NAME", "vendor_name"),
	("BEZEI", "state"),
	("REGIO", "state_code"),
	("STCD3", "gstn_no"),
	("J_1IPANNO", "pan"),
	("VGCLASS", "vendor_gst_classification"),
	("STR_SUPPL1", "address01"),
	("STR_SUPPL2", "address02"),
	("STREET", "address03"),
	("STR_SUPPL3", "address04"),
	("LOCATION", "address05"),
	("CITY1", "city_district"),
	("POST_CODE1", "pincode"),
	("COUNTRY", "country"),
	("TELF1", "contact_no"),
	("TELF2", "alternate_no"),
	("SMTP_ADDR", "email_id"),
	("REMARK", "remark"),
	("ERDAT", "created_on"),
	("BUKRS", "c_code"),
	("ZCOUNT", "count"),
	("WAERS", "currency"),
	("KTOKK", "account_group"),
	("J_1KFTIND", "type_of_industry"),
	("ZTERM", "terms_of_payment"),
	("TEXT1", "payment_term_description"),
	("AKONT", "reconciliation_account"),
]


def execute():
	if not frappe.db.exists("DocType", "SAP Mapper"):
		return

	existing = frappe.db.get_value(
		"SAP Mapper", {"doctype_name": TARGET_DOCTYPE}, "name"
	)
	if existing:
		mapper = frappe.get_doc("SAP Mapper", existing)
		mapper.set("fields_mapper", [])
	else:
		mapper = frappe.new_doc("SAP Mapper")
		mapper.doctype_name = TARGET_DOCTYPE

	for sap_field, erp_field in SAP_TO_ERP:
		mapper.append("fields_mapper", {"sap_field": sap_field, "erp_field": erp_field})

	mapper.save(ignore_permissions=True)
	frappe.db.commit()

	# Drop cached aliases so vendor.py picks the fresh mapping immediately.
	frappe.cache().delete_value("sap_mapper_aliases:" + TARGET_DOCTYPE)

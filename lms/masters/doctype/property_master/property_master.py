# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PropertyMaster(Document):
	pass

def get_permission_query_conditions(user):
	if not user:
		return ""
	roles=frappe.get_roles(user)
	if "System Manager" in roles or "Accounts" in roles:
		return ""
	if "Vendor" in roles:
		vendor=frappe.db.get_value("Vendor Master",{"email_address":user},"name")

		if not vendor:
			return "1=0"
		return f"`tabProperty Master`.`vendor`='{vendor}'"
	return ""

def has_permission(doc,user):
	roles=frappe.get_roles(user)
	if "System Manager" in roles or "Accounts" in roles:
		return True
	if "Vendor" in roles:
		vendor=frappe.db.get_value("Vendor Master",{"email_address":user},"name")
		return doc.vendor==vendor
	return False
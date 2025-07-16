# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LeaseManagement(Document):
	@frappe.whitelist()
	def get_pincodes_by_city(city):
		pincodes = frappe.get_all("Pincode Master", 
			filters={"city": city},
			fields=["pincode"])

		if not pincodes:
			return "No pincodes found for this city."

		pincode_list = ", ".join(p["pincode"] for p in pincodes)
		return pincode_list


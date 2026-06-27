# Copyright (c) 2026, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PreviousLeaseNoteDetails(Document):
	def autoname(self):
		if self.company and self.financial_start_year:
			company_code = frappe.db.get_value("Company Master", self.company, "company_code")

			if not company_code:
				frappe.throw("Company Code not found for selected Company")

			self.name = f"{company_code}-{self.financial_start_year}"

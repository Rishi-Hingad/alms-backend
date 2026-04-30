# Copyright (c) 2025, Rishi Hingad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SelectedVendor(Document):

	def on_update(self):
		if not self.employee_details:
			return

		count = len(self.selected_finance_company or [])

		frappe.db.set_value(
			"Purchase Team Form",
			self.employee_details,
			{
				"no_of_quotations": count,
				"all_quotations_ref_no": self.name
			},
			update_modified=False
		)

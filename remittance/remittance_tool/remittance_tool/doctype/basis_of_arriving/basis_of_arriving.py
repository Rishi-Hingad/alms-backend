# Copyright (c) 2026, Saurabh Tiwari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BasisofArriving(Document):
	def validate(self):
		self.validate_single_enabled(self.option_1, "Option 1")
		self.validate_single_enabled(self.option_2, "Option 2")
		self.validate_is_enabled()


	def validate_single_enabled(self, child_table, table_label):
		enabled_rows = [row for row in child_table if row.enabled]

		if len(enabled_rows) > 1:
			frappe.throw(
				f"Only one row can be enabled in {table_label}"
			)
	
	def validate_is_enabled(self):
		if self.is_enabled:

			existing_enabled = frappe.db.exists(
				"Basis of Arriving",
				{
					"is_enabled": 1,
					"name": ["!=", self.name]
				}
			)

			if existing_enabled:
				frappe.throw(
					f"Only one Basis of Arriving record can be enabled at a time. "
					f"Already enabled record: {existing_enabled}"
				)

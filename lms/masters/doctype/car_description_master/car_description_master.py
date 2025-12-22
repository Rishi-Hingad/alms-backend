# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CarDescriptionMaster(Document):
	def autoname(self):
		if not self.employee_code:
			frappe.throw("Employee Code is required")

		last_number = frappe.db.sql("""
            SELECT MAX(CAST(SUBSTRING_INDEX(name, '-', -1) AS UNSIGNED))
            FROM `tabCar Description Master`
            WHERE employee_code = %s
        """, (self.employee_code,))[0][0]
		
		next_number = (last_number or 0) + 1
		self.name = f"CAR-{self.employee_code}-{next_number}"
# Copyright (c) 2026, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType


class EscalationMatrix(Document):
	def autoname(self):
		prefix = "EM-"
		EscalationMatrixTable = DocType("Escalation Matrix")

		names = (
			frappe.qb.from_(EscalationMatrixTable)
			.select(EscalationMatrixTable.name)
			.where(EscalationMatrixTable.name.like(f"{prefix}%"))
		).run(pluck=True)

		numbers = [
			int(name.split("-")[-1])
			for name in names
			if name.split("-")[-1].isdigit()
		]

		last_number = max(numbers) if numbers else 0
		next_number = last_number + 1

		self.name = f"{prefix}{str(next_number).zfill(6)}"


# def validate(self):
#     for rule in self.escalation_rules:
#         if rule.escalation_param == "Time":
#             if not rule.escalation_uom:
#                 frappe.throw(
#                     f"Row {rule.idx}: Escalation UOM is required for Time-based escalation"
#                 )
#             rule.currency = None

#         if rule.escalation_param == "Amount":
#             if not rule.currency:
#                 frappe.throw(
#                     f"Row {rule.idx}: Currency is required for Amount-based escalation"
#                 )
#             rule.escalation_uom = None

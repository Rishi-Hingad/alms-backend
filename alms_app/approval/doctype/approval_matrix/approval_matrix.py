# Copyright (c) 2024, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType


class ApprovalMatrix(Document):
	def autoname(self):
		prefix = "AP-"
		ApprovalPolicyTable = DocType("Approval Matrix")

		names = (
			frappe.qb.from_(ApprovalPolicyTable)
			.select(ApprovalPolicyTable.name)
			.where(ApprovalPolicyTable.name.like(f"{prefix}%"))
		).run(pluck=True)

		numbers = [int(name.split("-")[-1]) for name in names if name.split("-")[-1].isdigit()]
		last_number = max(numbers) if numbers else 0
		next_number = last_number + 1
		self.name = f"{prefix}{str(next_number).zfill(6)}"





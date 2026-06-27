# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AssetInvoice(Document):
	def before_save(self):
		gst = self.basic_amount * (18/100)
		self.gst = gst
		total = self.basic_amount + gst
		self.total_bill_amount_inc_gst = total
		self.total_sch_amount = self.total_bill_amount_inc_gst

	pass

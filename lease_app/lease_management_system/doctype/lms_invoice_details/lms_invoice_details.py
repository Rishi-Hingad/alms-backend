# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import getdate


class LMSInvoiceDetails(Document):
	def autoname(self):
		vendor = (self.vendor_name or "").strip()

		mapping = {"eazy assets": "Eazy", "ald": "ALD"}

		vendor_part = mapping.get(vendor.lower(), vendor.replace(" ", "_"))

		dt = getdate(self.batch_date) if self.batch_date else datetime.now()

		year = dt.strftime("%Y")
		month = dt.strftime("%m")

		prefix = f"INV-{vendor_part}-{year}-{month}-"

		self.name = make_autoname(prefix + ".###")

	def validate(self):
		parent_code = self.name

		for i, row in enumerate(self.rows, start=1):
			row.name = f"{parent_code}-ITEM-{str(i).zfill(3)}"

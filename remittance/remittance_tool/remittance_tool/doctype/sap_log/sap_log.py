# Copyright (c) 2026, Saurabh Tiwari and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SAPLog(Document):
	def autoname(self):
		from frappe.model.naming import make_autoname
		from frappe.utils import now_datetime
		
		dt = now_datetime()
		# Format: SAP-LOG-VENDOR-COMPANY-YYYY-MM-DD-.#####
		prefix = f"SAP-LOG-{self.vendor_code}-{self.company_code}-{dt.strftime('%Y-%m-%d')}-.#####"
		self.name = make_autoname(prefix)


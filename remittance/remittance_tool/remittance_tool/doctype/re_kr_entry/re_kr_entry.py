# Copyright (c) 2026, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class REKREntry(Document):
	def before_insert(self):
		self.punch_time = now_datetime()

	def before_save(self):
		if self.has_value_changed("belnr") or not self.punch_time:
			self.punch_time = now_datetime()

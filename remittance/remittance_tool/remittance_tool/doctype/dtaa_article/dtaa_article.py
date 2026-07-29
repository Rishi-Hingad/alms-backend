# Copyright (c) 2026, Saurabh Tiwari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DTAAArticle(Document):
	pass
	# def autoname(self):
	# 	if self.parent:
	# 		parent_doc = frappe.get_doc("DTAA Master", self.parent)

	# 		country = parent_doc.country or ""
	# 		article_no = self.article_no or ""
	# 		description = self.article_description or ""

	# 		# Clean description
	# 		description = description.strip().replace(" ", "_")

	# 		self.name = f"{country}-{article_no}-{description}"

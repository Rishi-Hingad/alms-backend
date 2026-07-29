# Copyright (c) 2026, Saurabh Tiwari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class RemittanceDTAATaxDocuments(Document):
	def validate(self):
		self.validate_single_enabled_document()
	
	def validate_single_enabled_document(self):
		enabled_docs = {}

		for row in self.tax_documents:
			# only validate enabled rows
			if row.enabled:

				if row.tax_document_type in enabled_docs:
					frappe.throw(
						_(
							"Only one Enabled record is allowed for Tax Document Type: {0}"
						).format(frappe.bold(row.tax_document_type))
					)

				enabled_docs[row.tax_document_type] = row.name

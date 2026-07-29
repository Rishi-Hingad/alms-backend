import frappe
from frappe import _
from frappe.model.document import Document


class RemittanceVendor(Document):
	def validate(self):
		# Composite uniqueness: (vendor_code, c_code) must be unique.
		# autoname = "format:{vendor_code}-{c_code}" enforces this at the
		# primary-key level, but we throw a friendly error first so the user
		# sees a clear message instead of a raw SQL "Duplicate entry" trace.
		if not self.c_code:
			frappe.throw(_("Company Code (C.Code) is required for a vendor record."))

		conflict = frappe.db.get_value(
			"Remittance Vendor",
			{
				"vendor_code": self.vendor_code,
				"c_code": self.c_code,
				"name": ["!=", self.name or ""],
			},
			"name",
		)
		if conflict:
			frappe.throw(
				_("Vendor {0} already exists for Company Code {1} (record: {2}).").format(
					self.vendor_code, self.c_code, conflict
				)
			)

import frappe
from frappe.model.document import Document


class ApprovalEntry(Document):
	def before_save(self):
		self._sync_next_approver_from_last_row()

	def after_insert(self):
		self._sync_next_approver_from_last_row()

	def _sync_next_approver_from_last_row(self):
		if not self.approval_entry:
			return
		last = self.approval_entry[-1]
		self.next_approver = last.next_approver or ""
		self.next_approver_role = last.next_approver_role or ""
		self.next_approval_stage = last.next_stage or ""

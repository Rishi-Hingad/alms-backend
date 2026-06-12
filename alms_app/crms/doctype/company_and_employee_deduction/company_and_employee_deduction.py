# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import math
class CompanyandEmployeeDeduction(Document):
    def before_insert(self):
        self.is_submitted = 1

    def after_insert(self):
        try:
            from alms_app.approval.approval_router import trigger_approval_if_matrix_exists
            trigger_approval_if_matrix_exists(self)
        except Exception as e:
            import frappe
            frappe.log_error(str(e), "trigger_approval_if_matrix_exists fallback")

    def on_update(self):
        try:
            from alms_app.approval.approval_router import trigger_approval_if_matrix_exists
            trigger_approval_if_matrix_exists(self)
        except Exception as e:
            import frappe
            frappe.log_error(str(e), "trigger_approval_if_matrix_exists fallback")

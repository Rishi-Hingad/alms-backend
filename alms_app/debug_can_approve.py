import frappe
from alms_app.approval.approval_router import can_approve

def run():
    frappe.session.user = 'Administrator'
    print(can_approve('Purchase Form', '40048-Mr. Bansraj Chauhan'))


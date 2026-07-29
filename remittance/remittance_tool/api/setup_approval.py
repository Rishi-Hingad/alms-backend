import json

import frappe


def setup_approval():
	doctype = "Remittance Form 15 CB"
	matrix_name = "Remittance 15CB Approval"
	todo_type = "Approval"

	# 1. Create Todo Type
	if not frappe.db.exists("Todo Type", todo_type):
		frappe.get_doc({"doctype": "Todo Type", "todo_type_name": todo_type}).insert(ignore_permissions=True)
		print(f"Created Todo Type: {todo_type}")

	# 2. Create Approval Policy Matrix (Independent version)
	if not frappe.db.exists("Approval Policy Matrix", {"matrix_name": matrix_name}):
		matrix = frappe.get_doc(
			{
				"doctype": "Approval Policy Matrix",
				"matrix_name": matrix_name,
				"target_doctype": doctype,
				"approval_mode": "Sequential",
				"is_active": 1,
				"priority_level": 1,
				"todo_category": todo_type,
				"approval_stages": [
					{
						"approval_name": "Manager Approval",
						"approver_type": "Role",
						"role": "System Manager",
						"update_field": "status",
						"update_value": "Approved",
						"field_to_update_on_rejection": "status",
						"new_value_on_rejection": "Rejected",
						"approval_label": "Approve",
						"rejection_label": "Reject",
						"allow_senderback": 1,
					}
				],
			}
		)
		matrix.insert(ignore_permissions=True)
		frappe.db.commit()
		print(f"Created Approval Policy Matrix: {matrix_name}")
	else:
		print(f"Approval Policy Matrix {matrix_name} already exists")


if __name__ == "__main__":
	setup_approval()

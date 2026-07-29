"""Seed helpers for smoke-testing the approval flow on Remittance Form 15 CB."""

import frappe


def ensure_role(name):
	if not frappe.db.exists("Role", name):
		r = frappe.new_doc("Role")
		r.role_name = name
		r.desk_access = 1
		r.insert(ignore_permissions=True)


def ensure_user(email, first_name):
	ensure_role("Remittance User")
	if not frappe.db.exists("User", email):
		u = frappe.new_doc("User")
		u.email = email
		u.first_name = first_name
		u.send_welcome_email = 0
		u.enabled = 1
		u.user_type = "System User"
		u.append("roles", {"role": "Remittance User"})
		u.insert(ignore_permissions=True)


def ensure_matrix():
	matrix_name = "Form 15CB Maker-Checker"
	if frappe.db.exists("Approval Matrix", matrix_name):
		frappe.delete_doc("Approval Matrix", matrix_name, force=1, ignore_permissions=True)

	m = frappe.new_doc("Approval Matrix")
	m.matrix_name = matrix_name
	m.is_active = 1
	m.applies_to_doctype = "Remittance Form 15 CB"
	m.description = "3-stage maker-checker (any number of approvers is supported)."
	m.action_on_rejection = "Restart from beginning"

	m.append(
		"approval_stages",
		{
			"approval_stage": 1,
			"approval_stage_name": "Maker",
			"approver_type": "User",
			"user": "maker@test.local",
		},
	)
	m.append(
		"approval_stages",
		{
			"approval_stage": 2,
			"approval_stage_name": "Checker 1",
			"approver_type": "User",
			"user": "checker1@test.local",
		},
	)
	m.append(
		"approval_stages",
		{
			"approval_stage": 3,
			"approval_stage_name": "Checker 2 (Final)",
			"approver_type": "User",
			"user": "checker2@test.local",
		},
	)
	m.insert(ignore_permissions=True)
	return matrix_name


def run():
	"""Idempotent seed: users + 3-stage matrix for Form 15CB."""
	ensure_user("maker@test.local", "Maker")
	ensure_user("checker1@test.local", "Checker1")
	ensure_user("checker2@test.local", "Checker2")
	matrix = ensure_matrix()
	frappe.db.commit()
	return {
		"users": ["maker@test.local", "checker1@test.local", "checker2@test.local"],
		"matrix": matrix,
	}

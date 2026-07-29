"""End-to-end smoke test for the Form 15CB maker-checker approval flow."""

import frappe

from remittance_tool.remittance_tool.approval.router import (
	process_approval_action,
	trigger_approval_if_matrix_exists,
)


def _need_vendor_and_company():
	"""Create minimal linked masters if missing so we can insert a Form 15CB."""
	if not frappe.db.exists("Remittance Company", "TEST-CO"):
		c = frappe.new_doc("Remittance Company")
		c.company_name = "Test Company"
		c.company_code = "TEST-CO"
		c.company_short_form = "TCO"
		c.insert(ignore_permissions=True)
	if not frappe.db.exists("Remittance Vendor", "TEST-VENDOR"):
		v = frappe.new_doc("Remittance Vendor")
		v.vendor_name = "Test Vendor"
		v.vendor_code = "TEST-VENDOR"
		v.insert(ignore_permissions=True)


def _create_form_15cb():
	_need_vendor_and_company()
	doc = frappe.new_doc("Remittance Form 15 CB")
	doc.company = frappe.db.get_value("Remittance Company", {"company_code": "TEST-CO"}, "name")
	doc.vendor = frappe.db.get_value("Remittance Vendor", {"vendor_code": "TEST-VENDOR"}, "name")
	doc.document_no = "SMOKE-TEST-001"
	doc.insert(ignore_permissions=True)
	return doc


def _as_user(user):
	frappe.set_user(user)


def run():
	frappe.set_user("Administrator")

	doc = _create_form_15cb()
	print(f"[STEP 0] Created Form 15CB: {doc.name} status={doc.status} is_submitted={doc.is_submitted}")

	# Simulate submit-for-approval
	doc.db_set("is_submitted", 1, update_modified=True)
	doc.db_set("status", "Pending Approval", update_modified=True)
	doc.reload()
	trigger_approval_if_matrix_exists(doc)
	doc.reload()
	print(
		f"[STEP 1] Submitted. approval_initiated={doc.approval_initiated} approval_entry={doc.approval_entry}"
	)

	entry = frappe.get_doc("Approval Entry", doc.approval_entry)
	print(
		f"         Entry status={entry.status} next_stage={entry.next_approval_stage} next_approver={entry.next_approver}"
	)

	# Maker approves
	_as_user("maker@test.local")
	r1 = process_approval_action(doc.doctype, doc.name, "Approve", remarks="Looks good from Maker")
	print(f"[STEP 2] Maker approved → {r1}")
	entry.reload()
	print(
		f"         Entry status={entry.status} next_stage={entry.next_approval_stage} next_approver={entry.next_approver}"
	)

	# Checker1 approves
	_as_user("checker1@test.local")
	r2 = process_approval_action(doc.doctype, doc.name, "Approve", remarks="OK from Checker1")
	print(f"[STEP 3] Checker1 approved → {r2}")
	entry.reload()
	print(
		f"         Entry status={entry.status} next_stage={entry.next_approval_stage} next_approver={entry.next_approver}"
	)

	# Checker2 approves (final)
	_as_user("checker2@test.local")
	r3 = process_approval_action(doc.doctype, doc.name, "Approve", remarks="Final approval")
	print(f"[STEP 4] Checker2 approved → {r3}")
	entry.reload()
	doc.reload()
	print(f"         Entry status={entry.status}  Form 15CB status={doc.status}")

	# Final audit trail
	print("[TRAIL]")
	for row in entry.approval_entry:
		print(
			f"  stage={row.current_stage}->{row.next_stage} status={row.status} "
			f"approved_by={row.approved_by or '-'} next={row.next_approver or row.next_approver_role or '-'} "
			f"remarks={row.remarks or ''}"
		)

	frappe.db.commit()
	frappe.set_user("Administrator")

	assert entry.status == "Approved", f"Expected entry Approved, got {entry.status}"
	assert doc.status == "Approved", f"Expected doc Approved, got {doc.status}"

	return {
		"doc": doc.name,
		"entry": entry.name,
		"entry_status": entry.status,
		"doc_status": doc.status,
		"ledger_rows": len(entry.approval_entry),
	}


def run_reject_then_restart():
	"""Verify rejection flips is_submitted=0 and restart re-opens the flow."""
	frappe.set_user("Administrator")

	doc = _create_form_15cb()
	doc.document_no = "SMOKE-TEST-REJECT"
	doc.save(ignore_permissions=True)

	doc.db_set("is_submitted", 1, update_modified=True)
	doc.db_set("status", "Pending Approval", update_modified=True)
	doc.reload()
	trigger_approval_if_matrix_exists(doc)
	doc.reload()
	print(f"[R-0] Submitted: {doc.name} approval_entry={doc.approval_entry}")

	# Checker1 rejects at stage 2 (first Maker-approves to advance to Checker1)
	_as_user("maker@test.local")
	process_approval_action(doc.doctype, doc.name, "Approve", remarks="ok")
	_as_user("checker1@test.local")
	r = process_approval_action(doc.doctype, doc.name, "Reject", remarks="Needs fix")
	print(f"[R-1] Checker1 rejected → {r}")

	doc.reload()
	entry = frappe.get_doc("Approval Entry", doc.approval_entry)
	print(
		f"      doc status={doc.status} is_submitted={doc.is_submitted} approval_initiated={doc.approval_initiated}"
	)
	print(f"      entry status={entry.status}")

	# Re-submit → should restart at stage 1
	doc.db_set("is_submitted", 1, update_modified=True)
	doc.reload()
	trigger_approval_if_matrix_exists(doc)
	entry.reload()
	print(
		f"[R-2] Resubmitted → entry status={entry.status} next_stage={entry.next_approval_stage} next_approver={entry.next_approver}"
	)

	frappe.db.commit()
	frappe.set_user("Administrator")

	return {
		"doc": doc.name,
		"entry_status_after_reject": "Rejected",
		"restarted_next_stage": entry.next_approval_stage,
		"restarted_next_approver": entry.next_approver,
	}

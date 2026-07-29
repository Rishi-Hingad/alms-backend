import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import frappe
from frappe.utils.data import cast, compare, cstr, sql_like

RESTART_FROM_BEGINNING = "Restart from beginning"

_CONDITION_LABEL_TO_OPERATOR = {
	"Equals": "=",
	"Not Equals": "!=",
	"Like": "like",
	"Not Like": "not like",
	"In": "in",
	"Not In": "not in",
	"Is": "is",
}


# ---------------------------------------------------------
# 1. TRIGGER APPROVAL FLOW
# ---------------------------------------------------------


def trigger_approval_if_matrix_exists(doc, method=None):
	if not _should_process_approval(doc):
		return

	matched_matrix_name = _get_matching_matrix(doc)
	if matched_matrix_name:
		approval_matrix = frappe.get_doc("Approval Matrix", matched_matrix_name)
		generic_process_approval_entry(doc, approval_matrix)


def _should_process_approval(doc):
	if not (doc.get("is_submitted") == 1 or doc.docstatus == 1):
		return False
	if not doc.get("approval_initiated"):
		return True
	latest = _get_latest_approval_entry_row(doc)
	if latest and latest.status == "Rejected":
		return True
	return False


def _get_matching_matrix(doc):
	"""Pick the Approval Matrix to run for this doc.

	A matrix can optionally restrict itself to specific users via the
	`user_assignment` table. Selection happens in two passes:

	  1. User-specific match: matrices that list `doc.owner` in
	     `user_assignment` AND whose conditions evaluate true.
	  2. Fallback (default) match: matrices with an empty
	     `user_assignment` list AND whose conditions evaluate true.

	A user-specific match always wins over a fallback match. This means
	existing matrices (with no user_assignment configured) keep working
	exactly as before for users who aren't explicitly assigned elsewhere.
	"""
	matrices = frappe.get_all(
		"Approval Matrix",
		filters={"applies_to_doctype": doc.doctype, "is_active": 1},
		pluck="name",
	)

	user_specific_match = None
	fallback_match = None

	for matrix_name in matrices:
		matrix = frappe.get_doc("Approval Matrix", matrix_name)
		assigned_users = [
			row.user for row in (matrix.get("user_assignment") or []) if row.user
		]

		if not _evaluate_matrix_conditions(doc, matrix):
			continue

		if assigned_users:
			if doc.owner in assigned_users and user_specific_match is None:
				user_specific_match = matrix_name
		else:
			if fallback_match is None:
				fallback_match = matrix_name

	return user_specific_match or fallback_match


def _evaluate_matrix_conditions(doc, matrix):
	doctype = doc.doctype
	for cond_row in getattr(matrix, "conditions", []):
		fieldname = cond_row.conditional_field
		raw_val = doc.get(fieldname)
		label = getattr(cond_row, "condition", None) or "Equals"
		expected = cond_row.value
		op = _CONDITION_LABEL_TO_OPERATOR.get(label, "=")

		try:
			df = frappe.get_meta(doctype).get_field(fieldname)
			fieldtype = df.fieldtype if df else None
		except Exception:
			fieldtype = None

		if label in (None, "", "Equals") and isinstance(expected, str):
			ev = expected
			if ev.startswith("%") and ev.endswith("%") and len(ev) > 2:
				if not sql_like(cstr(raw_val), ev):
					return False
				continue
			if ev.startswith("*") and ev.endswith("*") and len(ev) > 2:
				if ev.strip("*") not in cstr(raw_val):
					return False
				continue

		if op in ("in", "not in"):
			val2 = []
			if isinstance(expected, (list, tuple)):
				val2 = [cstr(x).strip() for x in expected if cstr(x).strip() != ""]
			elif isinstance(expected, str):
				s = expected.strip()
				if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
					s = s[1:-1]
				val2 = [p.strip() for p in s.split(",") if p.strip() != ""]
			else:
				val2 = [cstr(expected).strip()]
			if fieldtype:
				val2 = [cast(fieldtype, x) for x in val2]
		elif op == "is":
			val2 = (cstr(expected).strip().lower() or "set") if expected is not None else "set"
		else:
			val2 = expected

		if not compare(raw_val, op, val2, fieldtype):
			return False

	return True


# ---------------------------------------------------------
# 2. INITIALIZE APPROVAL ENTRY
# ---------------------------------------------------------


def generic_process_approval_entry(doc, approval_matrix):
	try:
		first_stage = _get_first_stage(approval_matrix)
		if not first_stage:
			frappe.throw(f"Approval Matrix {approval_matrix.name} matched but has no Approval Stages.")

		latest = _get_latest_approval_entry_row(doc)
		if latest:
			if latest.status in ("Pending", "Approved"):
				return
			if latest.status == "Rejected":
				if check_restart_approval(latest):
					_reset_approval_entry_to_first_stage(latest.name, doc, first_stage)
				return

		_create_initial_approval_entry(doc, first_stage)

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Generic Create Approval Entry Error")
		raise


def _get_first_stage(approval_matrix):
	stages_list = getattr(approval_matrix, "approval_stages", [])
	sorted_stages = sorted(stages_list, key=lambda r: r.approval_stage or 0)
	for row in sorted_stages:
		if getattr(row, "user", None) or getattr(row, "role", None):
			return row
	return None


def _get_latest_approval_entry_row(doc):
	rows = frappe.get_all(
		"Approval Entry",
		filters={"record": doc.name, "applied_to_doctype": doc.doctype},
		fields=["name", "status", "approval_matrix"],
		order_by="modified desc",
		limit_page_length=1,
	)
	return frappe._dict(rows[0]) if rows else None


def _append_first_pending_stage(entry, doc, first_stage):
	next_stage_val = first_stage.approval_stage or 1
	if first_stage.approver_type == "User":
		entry.append(
			"approval_entry",
			{
				"status": "Pending",
				"current_stage": 0,
				"next_stage": next_stage_val,
				"next_approver": first_stage.user,
				"next_approver_role": None,
			},
		)
		return first_stage.user
	# Role
	entry.append(
		"approval_entry",
		{
			"status": "Pending",
			"current_stage": 0,
			"next_stage": next_stage_val,
			"next_approver": None,
			"next_approver_role": first_stage.role,
		},
	)
	return None


def _notify_first_stage_if_configured(first_stage, doc, next_user):
	matrix_doc = frappe.get_cached_doc("Approval Matrix", first_stage.parent)
	if not matrix_doc.send_email_alert or not matrix_doc.submission_email_template:
		return
	recipients = [next_user] if next_user else _role_recipients(first_stage.role)
	if not recipients:
		return
	_send_email(
		matrix_doc.submission_email_template,
		recipients,
		{"doc": doc, "next_user": next_user, "action": "Submitted"},
	)


def _role_recipients(role):
	"""Return list of email addresses for all enabled users holding `role`.

	Filters out:
	  - Disabled users (User.enabled = 0)
	  - System users (Administrator, Guest)
	  - Users with no email-like name (must contain '@')

	Returns User.name (which IS the email in Frappe) for each match.
	"""
	if not role:
		return []
	user_names = frappe.get_all(
		"Has Role",
		filters={"role": role, "parenttype": "User"},
		pluck="parent",
	)
	if not user_names:
		return []

	enabled = frappe.get_all(
		"User",
		filters=[
			["name", "in", user_names],
			["enabled", "=", 1],
			["name", "not in", ["Administrator", "Guest"]],
		],
		pluck="name",
	)
	enabled_set = set(enabled)
	# Email-like filter (defensive — Frappe usually stores email as name)
	return [u for u in user_names if u in enabled_set and "@" in u]


def _set_doc_approval_initiated_and_link(doc, entry_name):
	if hasattr(doc, "approval_initiated"):
		doc.db_set("approval_initiated", 1, update_modified=False)
	if hasattr(doc, "approval_entry"):
		doc.db_set("approval_entry", entry_name, update_modified=False)


def _reset_approval_entry_to_first_stage(entry_name, doc, first_stage):
	entry = frappe.get_doc("Approval Entry", entry_name)
	entry.status = "Pending"
	entry.approval_matrix = first_stage.parent
	next_user = _append_first_pending_stage(entry, doc, first_stage)
	entry.save(ignore_permissions=True)
	_notify_first_stage_if_configured(first_stage, doc, next_user)
	_set_doc_approval_initiated_and_link(doc, entry.name)


def _create_initial_approval_entry(doc, first_stage):
	entry = frappe.new_doc("Approval Entry")
	entry.status = "Pending"
	entry.applied_to_doctype = doc.doctype
	entry.record = doc.name
	entry.approval_matrix = first_stage.parent
	next_user = _append_first_pending_stage(entry, doc, first_stage)
	entry.insert(ignore_permissions=True)
	_notify_first_stage_if_configured(first_stage, doc, next_user)
	_set_doc_approval_initiated_and_link(doc, entry.name)


# ---------------------------------------------------------
# 3. ACTION PROCESSOR (API)
# ---------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def process_approval_action(doctype, doc_name, action, remarks="", target_user=None):
	try:
		entry, ledger_items = _get_active_entry_and_ledger(doctype, doc_name)
		pending_row = _get_pending_stage(ledger_items, entry.next_approval_stage)
		_validate_approver_permissions(pending_row)

		if action == "Reject":
			_handle_reject_action(doctype, doc_name, entry, pending_row, remarks)
			return {"status": "success", "message": "Document Rejected."}
		if action == "Approve":
			return _handle_approve_action(doctype, doc_name, entry, pending_row, remarks)
		if action == "Send Back":
			return _handle_send_back_action(doctype, doc_name, entry, pending_row, remarks, target_user)

		frappe.throw(f"Unknown action: {action}")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Process Approval Action Error")
		frappe.throw(f"Error processing approval: {str(e)}")


def _get_active_entry_and_ledger(doctype, doc_name):
	entry_name = frappe.db.get_value(
		"Approval Entry",
		{"applied_to_doctype": doctype, "record": doc_name, "status": "Pending"},
		"name",
	)
	if not entry_name:
		frappe.throw("No pending approval entry found for this document.")

	entry = frappe.get_doc("Approval Entry", entry_name)
	ledger_items = entry.approval_entry
	if not ledger_items:
		frappe.throw("Approval ledger is empty.")
	return entry, ledger_items


def _get_pending_stage(ledger_items, next_stage):
	target = int(next_stage) if next_stage else None
	if target is None:
		frappe.throw("Approval Entry has no next_approval_stage set.")
	match = None
	for row in ledger_items:
		if row.next_stage == target:
			match = row
	if match:
		return match
	frappe.throw("No pending stage found for this document.")


def _validate_approver_permissions(pending_row):
	user = frappe.session.user
	allowed_user = pending_row.next_approver
	allowed_role = pending_row.next_approver_role

	if allowed_user and allowed_user == user:
		return True
	if allowed_role and allowed_role in frappe.get_roles(user):
		return True
	if user == "Administrator":
		return True

	if allowed_user:
		waiting_for = allowed_user
	elif allowed_role:
		waiting_for = f"role '{allowed_role}'"
	else:
		waiting_for = "the next approver"
	frappe.throw(f"You are not authorized to approve this step. Waiting for {waiting_for}.")


def _handle_reject_action(doctype, doc_name, entry, pending_row, remarks):
	user = frappe.session.user
	entry.append(
		"approval_entry",
		{
			"action": "Rejected",
			"status": "Rejected",
			"approved_by": user,
			"remarks": remarks,
			"current_stage": pending_row.next_stage,
			"next_stage": None,
			"next_approver": None,
			"next_approver_role": None,
		},
	)
	entry.status = "Rejected"
	entry.save(ignore_permissions=True)

	if frappe.db.has_column(doctype, "status"):
		frappe.db.set_value(doctype, doc_name, "status", "Rejected", update_modified=True)
		if (
			frappe.get_value("Approval Matrix", entry.approval_matrix, "action_on_rejection")
			== RESTART_FROM_BEGINNING
		):
			if frappe.db.has_column(doctype, "is_submitted"):
				frappe.db.set_value(doctype, doc_name, "is_submitted", 0, update_modified=True)
			if frappe.db.has_column(doctype, "approval_initiated"):
				frappe.db.set_value(doctype, doc_name, "approval_initiated", 0, update_modified=True)

	# Email notification — send to:
	#   1. Maker (document owner)
	#   2. All previous approvers (anyone who already approved at a stage BELOW
	#      the stage being rejected). They invested effort approving — they
	#      should know the doc was rejected later in the chain.
	matrix_doc = frappe.get_cached_doc("Approval Matrix", entry.approval_matrix)
	if matrix_doc.send_email_alert and matrix_doc.rejection_email_template:
		try:
			doc = frappe.get_doc(doctype, doc_name)
			recipients = _rejection_recipients(doc, entry, pending_row.next_stage)
			if recipients:
				_send_email(
					matrix_doc.rejection_email_template,
					recipients,
					{"doc": doc, "rejected_by": user, "remarks": remarks, "action": "Rejected"},
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Rejection Email Error")


def _rejection_recipients(doc, entry, rejection_stage):
	"""Maker + all previous approvers (stages below `rejection_stage`).

	Returns deduped list of email addresses.
	"""
	emails = []
	seen = set()

	# 1. Maker (document owner)
	owner_email = frappe.db.get_value("User", doc.owner, "email") or doc.owner
	if owner_email and "@" in owner_email:
		emails.append(owner_email)
		seen.add(owner_email.lower())

	# 2. Previous approvers — anyone who Approved at a stage < rejection_stage
	try:
		target_stage = int(rejection_stage) if rejection_stage else None
	except (TypeError, ValueError):
		target_stage = None

	for row in (entry.approval_entry or []):
		if row.status != "Approved":
			continue
		if not row.approved_by:
			continue
		# Stage check — must be strictly below the rejection stage
		try:
			row_stage = int(row.current_stage) if row.current_stage else None
		except (TypeError, ValueError):
			row_stage = None
		if target_stage is not None and row_stage is not None and row_stage >= target_stage:
			continue

		approver_email = frappe.db.get_value("User", row.approved_by, "email") or row.approved_by
		if approver_email and "@" in approver_email and approver_email.lower() not in seen:
			emails.append(approver_email)
			seen.add(approver_email.lower())

	return emails


def _get_send_back_candidates(doctype, doc_name, entry, current_stage):
	"""Return list of [{user, label, type, stage}] the doc can be sent back to.

	Always includes:
	  - The document owner (Maker) as the first option (type='owner', stage=0)

	Plus any previous approver who approved a stage before the current one
	(type='approver', stage=<their approval_stage>).
	"""
	candidates = []

	# 1. Document owner (Maker) — always first
	owner = frappe.db.get_value(doctype, doc_name, "owner")
	if owner:
		owner_name = frappe.db.get_value("User", owner, "full_name") or owner
		candidates.append(
			{
				"user": owner,
				"label": f"Maker — {owner_name} ({owner})",
				"type": "owner",
				"stage": 0,
			}
		)

	# 2. Previous approvers (approved rows before current_stage)
	seen_users = {owner}
	for row in entry.approval_entry:
		if (
			row.status == "Approved"
			and row.approved_by
			and row.current_stage
			and current_stage
			and row.current_stage < current_stage
			and row.approved_by not in seen_users
		):
			user_name = frappe.db.get_value("User", row.approved_by, "full_name") or row.approved_by
			candidates.append(
				{
					"user": row.approved_by,
					"label": f"Stage {row.current_stage} — {user_name} ({row.approved_by})",
					"type": "approver",
					"stage": row.current_stage,
				}
			)
			seen_users.add(row.approved_by)

	return candidates


@frappe.whitelist()
def get_send_back_candidates(doctype, doc_name):
	"""API: return users/stages this document can be sent back to."""
	entry_name = frappe.db.get_value(
		"Approval Entry",
		{"applied_to_doctype": doctype, "record": doc_name, "status": "Pending"},
		"name",
	)
	if not entry_name:
		return []

	entry = frappe.get_doc("Approval Entry", entry_name)
	pending_row = None
	target = int(entry.next_approval_stage) if entry.next_approval_stage else None
	for row in entry.approval_entry:
		if row.next_stage == target:
			pending_row = row
	if not pending_row:
		return []

	return _get_send_back_candidates(doctype, doc_name, entry, pending_row.next_stage)


def _handle_send_back_action(doctype, doc_name, entry, pending_row, remarks, target_user=None):
	"""Send the document back to a chosen user — either the Maker (doc owner)
	or a previous approver. Behavior depends on which one:

	  - Maker: resets is_submitted/approval_initiated on the doc so the maker
	    can edit and resubmit. Status set to "Sent Back".
	  - Previous approver: rewinds next_approval_stage to their stage so they
	    get Approve/Reject buttons again. Status stays "Pending".
	"""
	user = frappe.session.user
	current_stage = pending_row.next_stage

	candidates = _get_send_back_candidates(doctype, doc_name, entry, current_stage)
	if not candidates:
		frappe.throw("No candidate found to send this document back to.")

	# If caller didn't specify, default to the Maker (first candidate)
	if not target_user:
		target_user = candidates[0]["user"]

	chosen = next((c for c in candidates if c["user"] == target_user), None)
	if not chosen:
		frappe.throw(f"{target_user} is not a valid send-back target for this document.")

	# Common ledger row
	ledger_row = {
		"action": "Sent Back",
		"status": "Sent Back",
		"approved_by": user,
		"remarks": remarks,
		"current_stage": current_stage,
		"next_approver": chosen["user"],
		"next_approver_role": None,
	}

	if chosen["type"] == "owner":
		# Send back to Maker — they edit & resubmit; flow will restart.
		ledger_row["next_stage"] = 0
		entry.append("approval_entry", ledger_row)
		entry.status = "Sent Back"
		entry.save(ignore_permissions=True)

		# Reset doc so Maker sees "Resubmit for Approval"
		if frappe.db.has_column(doctype, "is_submitted"):
			frappe.db.set_value(doctype, doc_name, "is_submitted", 0, update_modified=True)
		if frappe.db.has_column(doctype, "approval_initiated"):
			frappe.db.set_value(doctype, doc_name, "approval_initiated", 0, update_modified=True)
		if frappe.db.has_column(doctype, "status"):
			frappe.db.set_value(doctype, doc_name, "status", "Sent Back", update_modified=True)

		# Email notification — send to the target (maker)
		_notify_send_back(entry.approval_matrix, doctype, doc_name, user, chosen["user"], remarks)

		return {
			"status": "success",
			"message": f"Document sent back to Maker ({chosen['user']}).",
		}

	# Previous approver — rewind to their stage
	matrix = frappe.get_doc("Approval Matrix", entry.approval_matrix)
	target_stage = None
	for row in matrix.approval_stages:
		if row.approval_stage == chosen["stage"]:
			target_stage = row
			break
	if not target_stage:
		frappe.throw("Could not find the target approval stage in the matrix.")

	ledger_row["next_stage"] = target_stage.approval_stage
	ledger_row["next_approver"] = (
		target_stage.user if target_stage.approver_type == "User" else chosen["user"]
	)
	ledger_row["next_approver_role"] = target_stage.role if target_stage.approver_type == "Role" else None
	entry.append("approval_entry", ledger_row)

	# Rewind the pointer so the chosen approver becomes active
	entry.next_approval_stage = target_stage.approval_stage
	entry.status = "Pending"
	entry.save(ignore_permissions=True)

	# Email notification — send to the previous approver being re-engaged
	_notify_send_back(entry.approval_matrix, doctype, doc_name, user, target_user, remarks)

	return {
		"status": "success",
		"message": f"Document sent back to {chosen['user']} (stage {chosen['stage']}).",
	}


def _handle_approve_action(doctype, doc_name, entry, pending_row, remarks):
	user = frappe.session.user
	matrix = frappe.get_doc("Approval Matrix", entry.approval_matrix)
	next_stage = _find_next_stage(matrix, pending_row)

	if next_stage:
		next_user = next_stage.user if next_stage.approver_type == "User" else None
		next_role = next_stage.role if next_stage.approver_type == "Role" else None

		entry.append(
			"approval_entry",
			{
				"action": "Approved",
				"status": "Approved",
				"approved_by": user,
				"remarks": remarks,
				"current_stage": pending_row.next_stage,
				"next_stage": next_stage.approval_stage,
				"next_approver": next_user,
				"next_approver_role": next_role,
			},
		)
		entry.save(ignore_permissions=True)

		_notify_next_stage_on_approve(
			matrix, pending_row, doctype, doc_name, next_user, next_role
		)
		return {"status": "success", "message": "Document approved; sent to next stage."}

	return _finalize_approval(doctype, doc_name, entry, pending_row, user, remarks)


def _find_next_stage(matrix, pending_row):
	stages = sorted(matrix.approval_stages, key=lambda r: r.approval_stage or 0)
	current_num = pending_row.next_stage or 0
	for row in stages:
		if (row.approval_stage or 0) > current_num:
			return row
	return None


def _find_current_stage(matrix, pending_row):
	current_num = pending_row.next_stage or 0
	for row in matrix.approval_stages:
		if row.approval_stage == current_num:
			return row
	return None


def _finalize_approval(doctype, doc_name, entry, pending_row, user, remarks):
	entry.status = "Approved"
	entry.append(
		"approval_entry",
		{
			"action": "Approved",
			"status": "Approved",
			"approved_by": user,
			"remarks": remarks,
			"current_stage": pending_row.next_stage,
			"next_stage": None,
			"next_approver": None,
			"next_approver_role": None,
		},
	)
	entry.save(ignore_permissions=True)

	if frappe.db.has_column(doctype, "status"):
		frappe.db.set_value(doctype, doc_name, "status", "Approved", update_modified=True)

	# Email notification — send to:
	#   1. Maker (document owner)
	#   2. All approvers across every stage in the ledger (the full chain
	#      that approved this document — they should all know it's done)
	matrix_doc = frappe.get_cached_doc("Approval Matrix", entry.approval_matrix)
	if matrix_doc.send_email_alert and matrix_doc.final_approval_email_template:
		try:
			doc = frappe.get_doc(doctype, doc_name)
			recipients = _final_approval_recipients(doc, entry)
			if recipients:
				_send_email(
					matrix_doc.final_approval_email_template,
					recipients,
					{"doc": doc, "approved_by": user, "remarks": remarks, "action": "Approved"},
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Final Approval Email Error")

	return {"status": "success", "message": "Document approved successfully."}


def _final_approval_recipients(doc, entry):
	"""Maker + every approver across the entire approval chain.

	Returns deduped list of email addresses.
	"""
	emails = []
	seen = set()

	# 1. Maker (document owner)
	owner_email = frappe.db.get_value("User", doc.owner, "email") or doc.owner
	if owner_email and "@" in owner_email:
		emails.append(owner_email)
		seen.add(owner_email.lower())

	# 2. Every Approved row in the ledger — no stage filter (whole chain)
	for row in (entry.approval_entry or []):
		if row.status != "Approved":
			continue
		if not row.approved_by:
			continue

		approver_email = frappe.db.get_value("User", row.approved_by, "email") or row.approved_by
		if approver_email and "@" in approver_email and approver_email.lower() not in seen:
			emails.append(approver_email)
			seen.add(approver_email.lower())

	return emails


def _notify_next_stage_on_approve(matrix, pending_row, doctype, doc_name, next_user, next_role):
	"""Email the next-stage approver after a mid-stage approval.

	Template resolution (first match wins):
	  1. Per-stage override: current_stage.email_template (if current_stage.send_email)
	  2. Matrix-level fallback: matrix.submission_email_template

	Honors the matrix-level master switch (matrix.send_email_alert). Failures are
	logged but do not block the approval action.
	"""
	if not matrix.send_email_alert:
		return

	current_stage = _find_current_stage(matrix, pending_row)
	template_name = None
	if current_stage and current_stage.send_email and current_stage.email_template:
		template_name = current_stage.email_template
	elif matrix.submission_email_template:
		template_name = matrix.submission_email_template

	if not template_name:
		return

	recipients = [next_user] if next_user else _role_recipients(next_role)
	if not recipients:
		return

	try:
		doc = frappe.get_doc(doctype, doc_name)
		_send_email(
			template_name,
			recipients,
			{"doc": doc, "next_user": next_user, "action": "Approved"},
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Next-Stage Approval Email Error")


def _notify_send_back(matrix_name, doctype, doc_name, sent_by, target_user, remarks):
	"""Send email when a document is sent back to a user."""
	try:
		matrix_doc = frappe.get_cached_doc("Approval Matrix", matrix_name)
		if not matrix_doc.send_email_alert or not matrix_doc.send_back_email_template:
			return
		doc = frappe.get_doc(doctype, doc_name)
		target_email = frappe.db.get_value("User", target_user, "email") or target_user
		_send_email(
			matrix_doc.send_back_email_template,
			[target_email],
			{"doc": doc, "sent_by": sent_by, "target_user": target_user, "remarks": remarks, "action": "Sent Back"},
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Send Back Email Error")


def _get_smtp_connection():
	"""Return an authenticated smtplib.SMTP connection using Email Settings DocType credentials."""
	settings = frappe.get_single("Email Settings")

	server = settings.smtp_server
	port = int(settings.smtp_port or 587)
	use_tls = bool(settings.use_tls)
	use_ssl = bool(settings.use_ssl)
	smtp_user = settings.smtp_user
	smtp_password = settings.get_password("smtp_password")

	if use_ssl:
		conn = smtplib.SMTP_SSL(server, port)
	else:
		conn = smtplib.SMTP(server, port)
		if use_tls:
			conn.starttls()

	conn.login(smtp_user, smtp_password)
	return conn, settings


def _send_email(template_name, recipients, context):
	"""Render template and send via custom SMTP (Email Settings DocType).

	Writes a Remittance Email Log row for every send (Sent / Failed).
	"""
	if not recipients:
		return

	# Detect email type from template name for the log
	tmpl_lower = (template_name or "").lower()
	if "submission" in tmpl_lower or "approval required" in tmpl_lower:
		email_type = "Approval Submission"
	elif "rejected" in tmpl_lower:
		email_type = "Rejection"
	elif "sent back" in tmpl_lower or "send back" in tmpl_lower:
		email_type = "Send Back"
	elif "approved" in tmpl_lower:
		email_type = "Approval Final"
	else:
		email_type = "Approval Mid-Stage"

	# Reference info from context if available
	doc_obj = context.get("doc") if isinstance(context, dict) else None
	ref_doctype = getattr(doc_obj, "doctype", None) if doc_obj else None
	ref_name = getattr(doc_obj, "name", None) if doc_obj else None

	template = frappe.get_doc("Email Template", template_name)
	subject = frappe.render_template(template.subject or "", context)
	message = frappe.render_template(template.response_html or template.response or "", context)

	from remittance_tool.remittance_tool.utils.email_log import log_email

	send_error = None
	settings = None
	sender_email = None
	effective_recipients = list(recipients)

	try:
		conn, settings = _get_smtp_connection()
		sender_email = settings.default_sender_email or settings.smtp_user
		sender_name = settings.default_sender_name or ""
		from_addr = f"{sender_name} <{sender_email}>" if sender_name else sender_email

		# ── TEST MODE: redirect all emails to the configured test address ──
		test_mode = bool(getattr(settings, "test_mode_enabled", 0))
		test_to = (getattr(settings, "test_recipient_email", "") or "").strip()
		if test_mode and test_to:
			original = ", ".join(recipients)
			subject = f"[TEST → {original}] {subject}"
			effective_recipients = [test_to]

		msg = MIMEMultipart("alternative")
		msg["Subject"] = subject
		msg["From"] = from_addr
		msg["To"] = ", ".join(effective_recipients)
		msg.attach(MIMEText(message, "html"))

		conn.sendmail(sender_email, effective_recipients, msg.as_string())
		conn.quit()
	except Exception as smtp_err:
		send_error = str(smtp_err)
		frappe.log_error(send_error, "Email Sending Error (Approval Router)")

	log_email(
		status="Sent" if not send_error else "Failed",
		email_type=email_type,
		recipients=effective_recipients,
		subject=subject, body_html=message,
		reference_doctype=ref_doctype, reference_name=ref_name,
		smtp_server=(settings.smtp_server if settings else None),
		smtp_user=(settings.smtp_user if settings else None),
		from_address=sender_email,
		error=send_error,
	)


# ---------------------------------------------------------
# 4. FRONTEND HELPERS
# ---------------------------------------------------------


@frappe.whitelist()
def can_approve(doctype, doc_name):
	try:
		entry_name = frappe.db.get_value(
			"Approval Entry",
			{"applied_to_doctype": doctype, "record": doc_name, "status": "Pending"},
			"name",
		)
		if not entry_name:
			return False

		entry = frappe.get_doc("Approval Entry", entry_name)
		ledger = entry.approval_entry
		if not ledger:
			return False

		pending_row = _find_pending_row(ledger, entry.next_approval_stage)
		if not pending_row:
			return False

		user = frappe.session.user
		allowed_user = pending_row.next_approver
		allowed_role = pending_row.next_approver_role
		if user == "Administrator":
			return True
		if allowed_user and allowed_user == user:
			return True
		if allowed_role and allowed_role in frappe.get_roles(user):
			return True
		return False
	except Exception:
		frappe.log_error(frappe.get_traceback(), "can_approve error")
		return False


def _find_pending_row(ledger, next_stage):
	if not next_stage:
		return None
	target = int(next_stage)
	match = None
	for row in ledger:
		if row.next_stage == target:
			match = row
	return match


@frappe.whitelist()
def get_approval_status(approval_entry):
	entry = frappe.get_doc("Approval Entry", approval_entry)
	if entry.status == "Pending":
		next_approver = entry.next_approver
		if next_approver:
			full_name = frappe.db.get_value("User", next_approver, "full_name") or next_approver
			return f"Awaiting Approval from {full_name}"
		if entry.next_approver_role:
			return f"Awaiting Approval from role {entry.next_approver_role}"
		return "Awaiting Approval"
	if entry.status == "Rejected":
		return "Rejected"
	return entry.status


def check_restart_approval(entry):
	return (
		frappe.get_value("Approval Matrix", entry.approval_matrix, "action_on_rejection")
		== RESTART_FROM_BEGINNING
		if entry
		else False
	)


def cleanup_approval_entries_on_trash(doc, method=None):
	"""on_trash hook: remove Approval Entries linked to a document being deleted."""
	entries = frappe.get_all(
		"Approval Entry",
		filters={"applied_to_doctype": doc.doctype, "record": doc.name},
		pluck="name",
	)
	for name in entries:
		frappe.delete_doc("Approval Entry", name, force=1, ignore_permissions=True)


@frappe.whitelist()
def get_approval_trail(doctype, doc_name):
	"""
	Return the approval trail grouped by stage. All events for a given stage
	(across multiple Approval Entries / restarts) are clubbed under that stage.
	"""
	entries = frappe.get_all(
		"Approval Entry",
		filters={"applied_to_doctype": doctype, "record": doc_name},
		fields=["name", "status", "approval_matrix", "creation"],
		order_by="creation asc",
	)
	if not entries:
		return {"stages": []}

	# Use the latest entry's matrix to define the stage list
	latest_entry_name = entries[-1].name
	latest_entry = frappe.get_doc("Approval Entry", latest_entry_name)
	matrix_doc = frappe.get_doc("Approval Matrix", latest_entry.approval_matrix)
	stages_def = sorted(matrix_doc.approval_stages, key=lambda r: r.approval_stage or 0)

	# Stage that's currently waiting for action (only meaningful while the entry is Pending)
	current_pending_stage = None
	if latest_entry.status == "Pending" and latest_entry.next_approval_stage:
		try:
			current_pending_stage = int(latest_entry.next_approval_stage)
		except (TypeError, ValueError):
			current_pending_stage = None

	# Collect all events from every entry's ledger
	events_by_stage = {}
	for e in entries:
		entry_doc = frappe.get_doc("Approval Entry", e.name)
		for r in entry_doc.approval_entry:
			ev = _row_to_event(r)
			if ev:
				events_by_stage.setdefault(ev["stage"], []).append(ev)

	for stage_num, evs in events_by_stage.items():
		evs.sort(key=lambda x: x.get("timestamp") or "")

	stages_out = []
	for s in stages_def:
		stage_num = s.approval_stage
		stage_name = s.approval_stage_name or f"Stage {stage_num}"
		expected_user = s.user if s.approver_type == "User" else None
		expected_role = s.role if s.approver_type == "Role" else None

		# If a Send Back rewound the flow, treat the rewound stages as fresh:
		# the target stage shows WAITING FOR APPROVAL, and any stages after it
		# show YET TO RECEIVE — historical events are hidden because those
		# stages need to be re-approved.
		rewound = current_pending_stage is not None and stage_num >= current_pending_stage

		if rewound:
			label = "WAITING FOR APPROVAL" if stage_num == current_pending_stage else "YET TO RECEIVE"
			events = [
				{
					"label": label,
					"approver": expected_user,
					"approver_name": _user_name(expected_user),
					"approver_role": expected_role,
					"remarks": None,
					"action_line": None,
					"timestamp": None,
				}
			]
		else:
			events = events_by_stage.get(stage_num, [])
			if not events:
				label = "WAITING FOR APPROVAL" if stage_num == current_pending_stage else "YET TO RECEIVE"
				events = [
					{
						"label": label,
						"approver": expected_user,
						"approver_name": _user_name(expected_user),
						"approver_role": expected_role,
						"remarks": None,
						"action_line": None,
						"timestamp": None,
					}
				]

		stages_out.append(
			{
				"stage": stage_num,
				"stage_name": stage_name,
				"events": events,
			}
		)

	return {"stages": stages_out}


def _row_to_event(row):
	status = (row.status or "").strip()
	if status == "Pending":
		stage = row.next_stage or 0
		return {
			"stage": stage,
			"label": "WAITING FOR APPROVAL",
			"approver": row.next_approver,
			"approver_name": _user_name(row.next_approver),
			"approver_role": row.next_approver_role,
			"remarks": None,
			"action_line": _line("Submitted On", row.creation),
			"timestamp": str(row.creation) if row.creation else None,
		}
	if status in ("Approved", "Rejected", "Sent Back"):
		stage = row.current_stage or 0
		prefix = {"Approved": "Approved On", "Rejected": "Rejected On", "Sent Back": "Sent Back On"}[status]
		return {
			"stage": stage,
			"label": status.upper(),
			"approver": row.approved_by,
			"approver_name": _user_name(row.approved_by),
			"approver_role": None,
			"remarks": row.remarks,
			"action_line": _line(prefix, row.modified or row.creation),
			"timestamp": str(row.modified or row.creation) if (row.modified or row.creation) else None,
		}
	return None


def _user_name(user):
	if not user:
		return None
	return frappe.db.get_value("User", user, "full_name") or user


def _line(prefix, dt):
	if not dt:
		return None
	return f"{prefix}: {frappe.utils.format_datetime(dt, 'dd-MM-yyyy HH:mm')}"

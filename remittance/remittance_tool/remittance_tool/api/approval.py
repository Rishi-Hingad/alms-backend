import frappe
from frappe import _

from remittance_tool.remittance_tool.approval.router import (
	_get_matching_matrix,
	trigger_approval_if_matrix_exists,
)
from remittance_tool.remittance_tool.approval.router import (
	can_approve as _can_approve,
)
from remittance_tool.remittance_tool.approval.router import (
	get_approval_status as _get_approval_status,
)
from remittance_tool.remittance_tool.approval.router import (
	get_approval_trail as _get_approval_trail,
)
from remittance_tool.remittance_tool.approval.router import (
	get_send_back_candidates as _get_send_back_candidates,
)
from remittance_tool.remittance_tool.approval.router import (
	process_approval_action as _process_approval_action,
)


@frappe.whitelist(methods=["POST"])
def submit_for_approval(doctype, doc_name):
	"""Mark a document as submitted so the approval router will initialize the flow.

	Only the document owner (Maker) or Administrator may submit.
	"""
	doc = frappe.get_doc(doctype, doc_name)

	current_user = frappe.session.user
	if doc.owner != current_user and current_user != "Administrator":
		frappe.throw(_("Only the document owner ({0}) can submit this for approval.").format(doc.owner))

	if doc.get("is_submitted"):
		return {"status": "info", "message": "Document is already submitted."}

	# Pre-flight: ensure a matching, active Approval Matrix exists for this doc.
	# We check BEFORE setting is_submitted so a user retrying after configuration
	# doesn't get stuck with a doc that's marked submitted but has no flow.
	matched = _get_matching_matrix(doc)
	if not matched:
		frappe.throw(
			_(
				"No active Approval Matrix found for {0}. "
				"Please configure an Approval Matrix for this document type before submitting."
			).format(doctype)
		)

	doc.db_set("is_submitted", 1, update_modified=True)
	if frappe.db.has_column(doctype, "status"):
		doc.db_set("status", "Pending Approval", update_modified=True)
	doc.reload()
	trigger_approval_if_matrix_exists(doc)
	return {"status": "success", "message": "Submitted for approval."}


@frappe.whitelist(methods=["POST"])
def approve(doctype, doc_name, remarks=""):
	return _process_approval_action(doctype, doc_name, "Approve", remarks)


@frappe.whitelist(methods=["POST"])
def reject(doctype, doc_name, remarks=""):
	return _process_approval_action(doctype, doc_name, "Reject", remarks)


@frappe.whitelist(methods=["POST"])
def send_back(doctype, doc_name, remarks="", target_user=None):
	"""Send the document back to the Maker (doc owner) or a previous approver.

	If target_user is not provided, defaults to the Maker.
	"""
	return _process_approval_action(doctype, doc_name, "Send Back", remarks, target_user=target_user)


@frappe.whitelist()
def send_back_candidates(doctype, doc_name):
	"""Return list of candidate users this document can be sent back to.

	First entry is always the Maker (doc owner); the rest are previous approvers.
	"""
	return _get_send_back_candidates(doctype, doc_name)


@frappe.whitelist()
def can_approve(doctype, doc_name):
	return _can_approve(doctype, doc_name)


@frappe.whitelist()
def get_approval_status(doc_type, doc_name):
	"""Legacy JS contract used by the Form 15CB client script: {is_approver: bool}."""
	return {"is_approver": bool(_can_approve(doc_type, doc_name))}


@frappe.whitelist()
def status(approval_entry):
	return _get_approval_status(approval_entry)


@frappe.whitelist()
def approval_trail(doctype, doc_name):
	"""Return the full approval history for a document (visible to anyone who can read it)."""
	return _get_approval_trail(doctype, doc_name)

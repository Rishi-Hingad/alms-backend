"""Diagnostic helper for the Form 15CB approval flow."""

import frappe


def describe(doc_name, user=None):
	"""Print the current approval state for a Form 15CB so we can see why buttons are/aren't showing."""
	doctype = "Remittance Form 15 CB"
	user = user or frappe.session.user

	if not frappe.db.exists(doctype, doc_name):
		return f"Doc {doc_name} not found."

	doc = frappe.get_doc(doctype, doc_name)
	out = [
		f"Doc             : {doc.name}",
		f"Status          : {doc.status}",
		f"Is Submitted    : {doc.is_submitted}",
		f"Approval Init   : {doc.approval_initiated}",
		f"Approval Entry  : {doc.approval_entry or '-'}",
		f"Session user    : {user}",
	]

	if not doc.approval_entry:
		out.append("")
		out.append("⚠ No Approval Entry yet — click 'Send for Approval' on the form first.")
		return "\n".join(out)

	entry = frappe.get_doc("Approval Entry", doc.approval_entry)
	out += [
		"",
		f"Entry           : {entry.name}",
		f"Entry status    : {entry.status}",
		f"Next stage      : {entry.next_approval_stage}",
		f"Next approver   : {entry.next_approver or '-'}",
		f"Next role       : {entry.next_approver_role or '-'}",
		"",
		"Ledger:",
	]
	for i, row in enumerate(entry.approval_entry):
		out.append(
			f"  [{i}] stage={row.current_stage}->{row.next_stage} status={row.status} "
			f"approved_by={row.approved_by or '-'} next={row.next_approver or row.next_approver_role or '-'} "
			f"remarks={row.remarks or ''}"
		)

	from remittance_tool.remittance_tool.approval.router import can_approve

	ok = can_approve(doctype, doc.name)

	user_roles = frappe.get_roles(user)
	out += [
		"",
		f"can_approve({user}) = {ok}",
		f"User roles      : {user_roles}",
	]
	if not ok:
		out.append("")
		reasons = []
		if entry.status != "Pending":
			reasons.append(f"- Entry is {entry.status}, not Pending (no buttons shown once closed)")
		if entry.next_approver and entry.next_approver != user:
			reasons.append(f"- It's {entry.next_approver}'s turn, not {user}'s")
		if entry.next_approver_role and entry.next_approver_role not in user_roles:
			reasons.append(f"- Waiting for role '{entry.next_approver_role}', which {user} doesn't have")
		if not reasons:
			reasons.append("- Check logs / try hard-refresh (Ctrl+Shift+R)")
		out.append("Why buttons are hidden:")
		out += reasons

	return "\n".join(out)

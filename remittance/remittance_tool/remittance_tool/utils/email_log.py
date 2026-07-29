"""Single helper to write a Remittance Email Log row.

Call this from every place that sends mail (approval router, email_sender,
test scripts) so we have a unified audit trail.

Never raises — logging must not break the actual email send.
"""
import re

import frappe


def log_email(
	status,
	email_type=None,
	recipients=None,
	cc=None,
	bcc=None,
	subject=None,
	body_html=None,
	attachments=None,
	reference_doctype=None,
	reference_name=None,
	smtp_server=None,
	smtp_user=None,
	from_address=None,
	error=None,
):
	"""Insert a Remittance Email Log row. Silent on failure.

	Args:
		status:             "Sent" or "Failed"
		email_type:         one of the Select options (Approval Submission, etc.)
		recipients:         list or comma-separated string
		cc, bcc:            same shape
		subject, body_html: as sent
		attachments:        list of attachment dicts or filename strings
		reference_doctype:  e.g. "Remittance Form 15 CB"
		reference_name:     e.g. "000034 - MDPL"
		smtp_server, smtp_user, from_address: SMTP context
		error:              full traceback / exception string if Failed
	"""
	try:
		log = frappe.new_doc("Remittance Email Log")
		log.status = status
		log.email_type = email_type or "Other"
		log.sent_at = frappe.utils.now()
		log.sent_by = frappe.session.user
		log.recipients = _flatten(recipients)
		log.cc = _flatten(cc)
		log.bcc = _flatten(bcc)
		log.subject = (subject or "")[:480]
		log.body_preview = _preview(body_html)
		log.attachments_label = _attachment_label(attachments)
		log.reference_doctype = reference_doctype or ""
		log.reference_name = reference_name or ""
		log.smtp_server = smtp_server or ""
		log.smtp_user = smtp_user or ""
		log.from_address = from_address or ""
		log.error = (error or "")[:5000]
		log.insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		# Logging must not break sends — swallow and log error elsewhere
		frappe.log_error(frappe.get_traceback(), "Remittance Email Log Write Error")


def _flatten(value):
	"""Convert list / tuple / str to comma-separated string."""
	if not value:
		return ""
	if isinstance(value, (list, tuple, set)):
		return ", ".join(str(v) for v in value if v)
	return str(value)


def _preview(body_html):
	"""Strip HTML tags and return first 1000 chars of plain text."""
	if not body_html:
		return ""
	text = re.sub(r"<[^>]+>", " ", body_html)
	text = re.sub(r"\s+", " ", text).strip()
	return text[:1000]


def _attachment_label(attachments):
	"""Comma-separated list of attachment file names."""
	if not attachments:
		return ""
	names = []
	for att in attachments:
		if isinstance(att, dict):
			names.append(att.get("fname") or att.get("file_name") or "")
		else:
			names.append(str(att))
	return ", ".join(n for n in names if n)

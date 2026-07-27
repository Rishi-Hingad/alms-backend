"""Email sender for Remittance Form 15CB.

Sends the form's JSON / XML / PDF attachments to multiple recipients.
Uses our custom Email Settings (Zeptomail SMTP) via smtplib — NOT
frappe.sendmail (which requires an Email Account doctype configured).
"""
import json as json_lib
import re
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import frappe
from frappe import _

from remittance_tool.remittance_tool.utils.email_log import log_email


def _has_meaningful_content(html):
	"""True if the HTML actually contains text (not just <p><br></p> from an
	empty Frappe Text Editor)."""
	if not html:
		return False
	# Strip HTML tags + whitespace; what's left = real text content
	text = re.sub(r"<[^>]+>", "", html).strip()
	# Remove common HTML entities that render as whitespace
	text = text.replace("&nbsp;", "").replace("\xa0", "").strip()
	return bool(text)


@frappe.whitelist()
def send_form_15cb_email(
	docname,
	recipients,
	cc=None,
	bcc=None,
	subject=None,
	message=None,
	attach_json=1,
	attach_xml=1,
):
	"""Send Form 15CB to multiple recipients with optional JSON/XML attachments.

	Args:
		docname:     Remittance Form 15 CB name
		recipients:  comma-separated string OR list of email addresses
		cc, bcc:     same shape as recipients (optional)
		subject:     override default subject (optional)
		message:     HTML body (optional — default body used if blank)
		attach_json: 1 to attach JSON file, 0 to skip
		attach_xml:  1 to attach XML file, 0 to skip
	"""
	doc = frappe.get_doc("Remittance Form 15 CB", docname)

	if doc.status != "Approved":
		frappe.throw(_("Email can only be sent after the form is Approved."))

	to_list = _split_emails(recipients)
	if not to_list:
		frappe.throw(_("At least one recipient email is required."))

	cc_list = _split_emails(cc)
	bcc_list = _split_emails(bcc)

	subject = subject or _("Form 15CB - {0}").format(docname)
	if not _has_meaningful_content(message):
		message = _default_message(doc)

	# ── TEST MODE: redirect everyone to test_recipient_email ──────────
	settings = frappe.get_single("Email Settings")
	if getattr(settings, "test_mode_enabled", 0):
		test_to = (getattr(settings, "test_recipient_email", "") or "").strip()
		if test_to:
			original_to = ", ".join(to_list)
			original_cc = ", ".join(cc_list) if cc_list else ""
			original_bcc = ", ".join(bcc_list) if bcc_list else ""
			original_label = original_to
			if original_cc:
				original_label += f" · cc: {original_cc}"
			if original_bcc:
				original_label += f" · bcc: {original_bcc}"
			subject = f"[TEST → {original_label}] {subject}"
			to_list = [test_to]
			cc_list = []
			bcc_list = []

	attachments = _build_attachments(docname, doc, attach_json, attach_xml)

	# Convert attachment mimetypes for smtplib
	smtp_attachments = []
	for att in attachments:
		mime = "application/json" if att["fname"].endswith(".json") else (
			"application/xml" if att["fname"].endswith(".xml") else "application/octet-stream"
		)
		smtp_attachments.append({
			"fname": att["fname"],
			"fcontent": att["fcontent"],
			"mimetype": mime,
		})

	# Send via smtplib (Email Settings) — same path as send_json_to_ca
	send_error = None
	try:
		_send_via_smtplib(
			settings=settings,
			to_list=to_list + cc_list + bcc_list,
			subject=subject,
			body_html=message,
			attachments=smtp_attachments,
		)
	except Exception as e:
		send_error = str(e)

	log_email(
		status="Sent" if not send_error else "Failed",
		email_type="Send Documents",
		recipients=to_list, cc=cc_list, bcc=bcc_list,
		subject=subject, body_html=message,
		attachments=smtp_attachments,
		reference_doctype="Remittance Form 15 CB", reference_name=docname,
		smtp_server=settings.smtp_server, smtp_user=settings.smtp_user,
		from_address=settings.default_sender_email or settings.smtp_user,
		error=send_error,
	)
	if send_error:
		frappe.throw(_("Email send failed: {0}").format(send_error))

	_log_email_event(doc, to_list, cc_list, bcc_list, attachments)

	return {
		"status": "success",
		"message": _("Email queued for {0} recipient(s)").format(len(to_list)),
		"recipients": to_list,
		"cc": cc_list,
		"bcc": bcc_list,
	}


@frappe.whitelist()
def add_attachment_to_form(docname, file_url):
	"""Append a row to Form 15CB's `attachments` child table.

	Called from the Send Documents dialog right after a file is uploaded
	inline (so the file simultaneously becomes part of the form's official
	attachments list — same as if user added it via the table UI).
	"""
	if not file_url:
		frappe.throw(_("file_url is required"))

	doc = frappe.get_doc("Remittance Form 15 CB", docname)

	# Skip if this URL is already in the table
	existing = [
		(row.get("attach_jacw") or "").strip()
		for row in (doc.get("attachments") or [])
	]
	if file_url in existing:
		return {"status": "skipped", "message": "Already attached"}

	# Critical-fields lock allows changes to `attachments`, so this save is fine
	doc.append("attachments", {"attach_jacw": file_url})
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": "success",
		"message": _("File added to form's Attachments table"),
		"file_url": file_url,
	}


@frappe.whitelist()
def save_post_approval_remark(docname, remark):
	"""Save (or update) the form's post_approval_remark field.

	Called from the Send Documents dialog on Send so the typed remark
	persists on the form alongside the email send.
	"""
	doc = frappe.get_doc("Remittance Form 15 CB", docname)
	if (doc.get("post_approval_remark") or "") == (remark or ""):
		return {"status": "unchanged"}
	doc.post_approval_remark = remark or ""
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "saved"}


@frappe.whitelist()
def list_form_attachments(docname):
	"""Return files from the form's `attachments` child table (Remittance
	Attachments → attach_jacw). Each row's file URL is resolved against the
	File doctype to get file_name, size, etc.

	The dialog will show ONLY these — not the standard Frappe sidebar files.
	"""
	doc = frappe.get_doc("Remittance Form 15 CB", docname)
	rows = doc.get("attachments") or []

	out = []
	for row in rows:
		file_url = (row.get("attach_jacw") or "").strip()
		if not file_url:
			continue

		# Resolve File doctype record by file_url
		file_record = frappe.db.get_value(
			"File",
			{"file_url": file_url},
			["name", "file_name", "file_size", "is_private"],
			as_dict=True,
		)
		if not file_record:
			# File doc missing — still expose the URL so admin can see
			out.append({
				"row_name": row.name,
				"file_url": file_url,
				"file_name": file_url.rsplit("/", 1)[-1] or file_url,
				"size_label": "?",
				"missing": True,
			})
			continue

		size = file_record.file_size or 0
		if size > 1024 * 1024:
			size_label = f"{size / (1024 * 1024):.1f} MB"
		elif size > 1024:
			size_label = f"{size / 1024:.1f} KB"
		else:
			size_label = f"{size} B"

		out.append({
			"row_name": row.name,
			"file_url": file_url,
			"file_name": file_record.file_name or file_url.rsplit("/", 1)[-1],
			"size_label": size_label,
			"is_private": file_record.is_private,
			# Pass file doctype name for backend resolution
			"file_doc_name": file_record.name,
		})
	return out


@frappe.whitelist()
def send_attachments_email(
	docname,
	recipients,
	file_urls=None,
	subject=None,
	message=None,
	cc=None,
):
	"""Send an email with selected file attachments to multiple recipients.

	Attachments come from the form's `attachments` child table
	(Remittance Attachments → attach_jacw). User picks which rows to send.

	Args:
		docname:    Remittance Form 15 CB name (must be Approved)
		recipients: comma-separated emails or list
		file_urls:  comma-separated file URLs OR JSON list (must be present
		             in the form's attachments child table)
		subject:    email subject (optional — default auto-built)
		message:    HTML message body. If blank:
		             - Use doc.post_approval_remark if set
		             - Else use the default styled template
		cc:         optional CC list
	"""
	doc = frappe.get_doc("Remittance Form 15 CB", docname)

	if doc.status != "Approved":
		frappe.throw(_("Documents can only be emailed after the form is Approved."))

	to_list = _split_emails(recipients)
	if not to_list:
		frappe.throw(_("At least one recipient email is required."))
	cc_list = _split_emails(cc)

	# Resolve attachments — file_urls is comma-separated or JSON list
	if isinstance(file_urls, str):
		if file_urls.strip().startswith("["):
			file_urls = frappe.parse_json(file_urls)
		else:
			file_urls = [f.strip() for f in file_urls.split(",") if f.strip()]
	file_urls = file_urls or []

	attachments = _build_file_attachments_from_urls(doc, file_urls)

	subject_final = subject or _("Form 15CB - {0} - Documents").format(docname)

	# Persist the typed remark to the form's post_approval_remark field
	# so it shows on the form too. (Text Editor empty values like "<p><br></p>"
	# are ignored — keep whatever's already saved.)
	remark_text = message if _has_meaningful_content(message) else ""
	if remark_text:
		existing_remark = doc.get("post_approval_remark") or ""
		if remark_text != existing_remark:
			doc.post_approval_remark = remark_text
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			doc.reload()

	# Message priority for email body:
	#   1. User typed a meaningful message → use it (also persisted above)
	#   2. doc.post_approval_remark is set → default template (includes remark block)
	#   3. Otherwise → default template (no remark block)
	if _has_meaningful_content(message):
		body_html = message
	else:
		body_html = _build_attachments_email_template(doc, len(attachments))

	# Test-mode override
	settings = frappe.get_single("Email Settings")
	if getattr(settings, "test_mode_enabled", 0):
		test_to = (getattr(settings, "test_recipient_email", "") or "").strip()
		if test_to:
			original = ", ".join(to_list)
			if cc_list:
				original += f" · cc: {', '.join(cc_list)}"
			subject_final = f"[TEST → {original}] {subject_final}"
			to_list = [test_to]
			cc_list = []

	send_error = None
	try:
		_send_via_smtplib(
			settings=settings,
			to_list=to_list + cc_list,
			subject=subject_final,
			body_html=body_html,
			attachments=attachments,
		)
	except Exception as e:
		send_error = str(e)

	log_email(
		status="Sent" if not send_error else "Failed",
		email_type="Send Documents",
		recipients=to_list, cc=cc_list,
		subject=subject_final, body_html=body_html,
		attachments=attachments,
		reference_doctype="Remittance Form 15 CB", reference_name=docname,
		smtp_server=settings.smtp_server, smtp_user=settings.smtp_user,
		from_address=settings.default_sender_email or settings.smtp_user,
		error=send_error,
	)
	if send_error:
		frappe.throw(_("Email send failed: {0}").format(send_error))

	# Log on form timeline
	try:
		file_label = ", ".join(a["fname"] for a in attachments) or "(none)"
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": "Remittance Form 15 CB",
			"reference_name": docname,
			"content": (
				f"Documents email sent to: {', '.join(to_list)} · "
				f"Attachments: {file_label} · By: {frappe.session.user}"
			),
		}).insert(ignore_permissions=True)
	except Exception:
		pass

	return {
		"status": "success",
		"message": _("Email sent to {0} recipient(s) with {1} attachment(s)").format(
			len(to_list), len(attachments)
		),
		"recipients": to_list,
		"attachment_count": len(attachments),
	}


def _build_file_attachments_from_urls(doc, file_urls):
	"""Read each file (by URL from form's attachments child table) and
	return list of attachment dicts for smtplib.

	Security: only allows URLs that ACTUALLY exist in the form's
	`attachments` child table — prevents arbitrary file disclosure.
	"""
	if not file_urls:
		return []

	# Build allowlist from child table
	allowed = {
		(row.get("attach_jacw") or "").strip()
		for row in (doc.get("attachments") or [])
	}
	allowed.discard("")

	out = []
	for url in file_urls:
		url = (url or "").strip()
		if not url or url not in allowed:
			continue

		# Find the File doc and read its content
		file_doc_name = frappe.db.get_value("File", {"file_url": url}, "name")
		if not file_doc_name:
			continue
		try:
			file_doc = frappe.get_doc("File", file_doc_name)
			content = file_doc.get_content()
		except Exception:
			continue

		if isinstance(content, str):
			content = content.encode("utf-8")

		# Guess mimetype from extension
		import mimetypes
		mime, _ignored = mimetypes.guess_type(file_doc.file_name or url)
		out.append({
			"fname": file_doc.file_name or url.rsplit("/", 1)[-1],
			"fcontent": content,
			"mimetype": mime or "application/octet-stream",
		})
	return out


def _build_attachments_email_template(doc, attachment_count):
	"""Default email body for the 'Send with Attachments' flow."""
	esc = frappe.utils.escape_html
	docname = esc(doc.name)
	vendor = esc(str(doc.get("vendor") or ""))
	company = esc(str(doc.get("company") or ""))

	def _money(v):
		if v in (None, ""):
			return "—"
		try:
			return f"{float(v):,.2f}"
		except (TypeError, ValueError):
			return esc(str(v))

	amt_inr = _money(doc.get("amount_payable_inr"))
	currency = esc(doc.get("currency") or "INR")
	amt_for = _money(doc.get("amount_payable_foreign"))
	now_str = esc(frappe.utils.format_datetime(frappe.utils.now(), "dd MMM yyyy, hh:mm a"))
	post_remark = esc(doc.get("post_approval_remark") or "")

	remark_block = ""
	if post_remark:
		remark_block = f"""
		<div style="margin:18px 36px 0;padding:14px 18px;background:#fffbeb;border-left:3px solid #f59e0b;border-radius:6px;">
		  <p style="margin:0 0 4px;font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#92400e;">Remark from Maker</p>
		  <p style="margin:0;font-size:14px;color:#1a202c;line-height:1.55;">{post_remark}</p>
		</div>
		"""

	return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:32px 16px;background:#eef2f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#0f172a;-webkit-font-smoothing:antialiased;">

  <div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(15,23,42,0.08);">

    <!-- gradient header (teal/green for approved docs) -->
    <div style="background:linear-gradient(135deg,#059669 0%,#10b981 100%);padding:36px 36px 30px;color:#ffffff;">
      <div style="display:inline-block;padding:4px 12px;background:rgba(255,255,255,0.18);border-radius:20px;font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">
        Approved · Documents
      </div>
      <h1 style="margin:14px 0 6px;font-size:26px;font-weight:700;line-height:1.2;">
        Form 15CB Documents
      </h1>
      <p style="margin:0;font-size:14px;color:rgba(255,255,255,0.9);">
        Reference: <strong style="color:#fff;">{docname}</strong>
      </p>
    </div>

    <!-- greeting -->
    <div style="padding:30px 36px 8px;">
      <p style="margin:0;font-size:15px;color:#334155;line-height:1.65;">
        Please find attached the supporting documents for Form 15CB <strong>{docname}</strong>
        which has been approved. {attachment_count} file(s) included.
      </p>
    </div>

    {remark_block}

    <!-- summary table -->
    <div style="padding:24px 36px 8px;">
      <p style="margin:0 0 14px;font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#94a3b8;">
        Form Summary
      </p>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        {_kv_row("Form No.", docname, alt=True)}
        {_kv_row("Company", company)}
        {_kv_row("Vendor", vendor, alt=True)}
        {_kv_row("Currency", currency)}
        {_kv_row("Amount (Foreign)", amt_for + " " + currency, alt=True)}
        {_kv_row("Amount (INR)", "₹ " + amt_inr)}
      </table>
    </div>

    <!-- attachments callout -->
    <div style="margin:24px 36px 0;padding:18px;background:linear-gradient(135deg,#ecfdf5 0%,#d1fae5 100%);border:1px solid #6ee7b7;border-radius:10px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="vertical-align:middle;width:48px;">
            <div style="width:40px;height:40px;background:#059669;border-radius:8px;text-align:center;line-height:40px;font-size:20px;color:#ffffff;">
              📎
            </div>
          </td>
          <td style="vertical-align:middle;padding-left:14px;">
            <p style="margin:0 0 2px;font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#065f46;">
              Attached
            </p>
            <p style="margin:0;font-size:14px;font-weight:600;color:#0f172a;">
              {attachment_count} document(s) — see attachments below
            </p>
          </td>
        </tr>
      </table>
    </div>

    <!-- footer -->
    <div style="margin-top:30px;padding:22px 36px;background:#0f172a;color:#cbd5e1;">
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="vertical-align:middle;">
            <p style="margin:0;font-size:14px;font-weight:600;color:#ffffff;">Remittance Tool</p>
            <p style="margin:4px 0 0;font-size:12px;color:#94a3b8;">Approved Form 15CB delivery</p>
          </td>
          <td style="vertical-align:middle;text-align:right;">
            <p style="margin:0;font-size:11px;color:#94a3b8;">Sent</p>
            <p style="margin:2px 0 0;font-size:13px;color:#e2e8f0;">{now_str}</p>
          </td>
        </tr>
      </table>
    </div>

  </div>
</body>
</html>"""


@frappe.whitelist()
def send_json_to_ca(docname, ca_name, message=None):
	"""Send the Form 15CB JSON file to a CA's email — via Email Settings SMTP.

	Uses our Email Settings doctype (Zeptomail) over smtplib directly. Does
	NOT use frappe.sendmail because that requires a Frappe Email Account.

	Args:
		docname:  Remittance Form 15 CB name
		ca_name:  CA Master record name (membership_no)
		message:  optional custom HTML body — overrides default template
	"""
	doc = frappe.get_doc("Remittance Form 15 CB", docname)

	if not ca_name:
		frappe.throw(_("Please select a CA."))

	ca = frappe.get_doc("CA Master", ca_name)
	ca_email = (ca.email_id or "").strip()
	if not ca_email or "@" not in ca_email:
		frappe.throw(_(
			"CA '{0}' has no valid email_id configured in CA Master."
		).format(ca.ca_name or ca_name))

	from remittance_tool.remittance_tool.api.json_generator import (
		generate_remittance_json,
	)
	json_str = generate_remittance_json(docname)

	subject = _("Form 15CB JSON - {0}").format(docname)
	# Use custom message ONLY if it has real text content. Frappe Text Editor
	# returns "<p><br></p>" when user opens it without typing — that's truthy
	# but visually empty, which would suppress the styled template.
	if _has_meaningful_content(message):
		body_html = message
	else:
		body_html = _build_ca_email_template(doc, ca)

	to_list = [ca_email]
	subject_final = subject

	# Test-mode override (Email Settings)
	settings = frappe.get_single("Email Settings")
	if getattr(settings, "test_mode_enabled", 0):
		test_to = (getattr(settings, "test_recipient_email", "") or "").strip()
		if test_to:
			subject_final = f"[TEST → {ca_email}] {subject}"
			to_list = [test_to]

	# Send via smtplib using Email Settings credentials
	json_attachment = {
		"fname": f"{docname}.json",
		"fcontent": json_str.encode("utf-8") if isinstance(json_str, str) else json_str,
		"mimetype": "application/json",
	}
	send_error = None
	try:
		_send_via_smtplib(
			settings=settings,
			to_list=to_list,
			subject=subject_final,
			body_html=body_html,
			attachments=[json_attachment],
		)
	except Exception as e:
		send_error = str(e)

	log_email(
		status="Sent" if not send_error else "Failed",
		email_type="Send JSON to CA",
		recipients=to_list,
		subject=subject_final, body_html=body_html,
		attachments=[json_attachment],
		reference_doctype="Remittance Form 15 CB", reference_name=docname,
		smtp_server=settings.smtp_server, smtp_user=settings.smtp_user,
		from_address=settings.default_sender_email or settings.smtp_user,
		error=send_error,
	)
	if send_error:
		frappe.throw(_("Email send failed: {0}").format(send_error))

	# Log on form timeline
	try:
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": "Remittance Form 15 CB",
			"reference_name": docname,
			"content": (
				f"JSON sent to CA: {ca.ca_name or ca_name} ({ca_email}) · "
				f"By: {frappe.session.user}"
			),
		}).insert(ignore_permissions=True)
	except Exception:
		pass

	return {
		"status": "success",
		"message": _("JSON emailed to {0}").format(ca_email),
		"ca_name": ca.ca_name,
		"ca_email": ca_email,
	}


def _build_ca_email_template(doc, ca):
	"""Premium HTML email template for the JSON-to-CA email.

	Design notes:
	  - Single-column 640px max-width (gmail/outlook safe)
	  - Inline CSS only (no <style>) — many clients strip <style>
	  - Indigo/teal gradient header for premium feel
	  - Two-column "summary cards" for quick scan
	  - Detailed transaction table for full reference
	  - Clear next-steps checklist
	  - Sender / firm info in footer for professional close
	"""
	esc = frappe.utils.escape_html

	def _fmt(v, fallback="—"):
		return esc(str(v)) if v not in (None, "") else fallback

	def _money(v):
		if v in (None, ""):
			return "—"
		try:
			return f"{float(v):,.2f}"
		except (TypeError, ValueError):
			return esc(str(v))

	# CA fields
	salutation = esc(ca.salutation or "M/s.")
	ca_full = esc(ca.ca_name or "")
	firm = esc(ca.firm_name or "")
	firm_reg = esc(ca.firm_registration_no or "")
	mem_no = esc(ca.membership_no or "")

	# Form data
	docname = esc(doc.name)
	company_name = _fmt(doc.get("company"))
	vendor = _fmt(doc.get("vendor"))
	currency = esc(doc.get("currency") or "INR")
	amt_inr = _money(doc.get("amount_payable_inr"))
	amt_for = _money(doc.get("amount_payable_foreign"))
	purpose = _fmt(doc.get("purpose_code"))
	dtaa = _fmt(doc.get("dtaa_name"))
	dtaa_article = _fmt(doc.get("dtaa_article"))
	country = _fmt(doc.get("country_to_remit"))
	prop_date = _fmt(doc.get("proposed_date_of_remittance"))
	tax_category = _fmt(doc.get("tax_category"))
	trc = "Yes" if doc.get("trc_obtained") else "No"
	gross_up = "Yes" if doc.get("gross_up") else "No"

	# Maker info
	maker_email = esc(doc.owner or "")
	maker_name = esc(frappe.db.get_value("User", doc.owner, "full_name") or doc.owner or "Maker")

	# Firm meta line
	firm_meta = ""
	if firm:
		parts = [firm]
		if firm_reg:
			parts.append(f"FRN: {firm_reg}")
		if mem_no:
			parts.append(f"M.No: {mem_no}")
		firm_meta = " · ".join(parts)

	now_str = esc(frappe.utils.format_datetime(frappe.utils.now(), "dd MMM yyyy, hh:mm a"))

	return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:32px 16px;background:#eef2f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#0f172a;-webkit-font-smoothing:antialiased;">

  <!-- email card -->
  <div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(15,23,42,0.08);">

    <!-- gradient header -->
    <div style="background:linear-gradient(135deg,#4f46e5 0%,#0ea5e9 100%);padding:36px 36px 30px;color:#ffffff;">
      <div style="display:inline-block;padding:4px 12px;background:rgba(255,255,255,0.18);border-radius:20px;font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">
        Form 15CB · JSON
      </div>
      <h1 style="margin:14px 0 6px;font-size:26px;font-weight:700;line-height:1.2;letter-spacing:-0.01em;">
        Ready for E-Filing
      </h1>
      <p style="margin:0;font-size:14px;color:rgba(255,255,255,0.85);line-height:1.5;">
        The income-tax portal-ready JSON for <strong style="color:#fff;">{docname}</strong> is attached below.
      </p>
    </div>

    <!-- greeting -->
    <div style="padding:30px 36px 8px;">
      <p style="margin:0 0 8px;font-size:15px;color:#0f172a;">
        Dear <strong>{salutation} {ca_full}</strong>,
      </p>
      {f'<p style="margin:0 0 18px;font-size:13px;color:#64748b;">{esc(firm_meta)}</p>' if firm_meta else ''}
      <p style="margin:0;font-size:15px;color:#334155;line-height:1.65;">
        Please find attached the Form 15CB JSON file for review and upload to the
        income-tax e-filing portal. Key transaction details are summarized below
        for your quick reference.
      </p>
    </div>

    <!-- KPI cards -->
    <div style="padding:24px 36px 8px;">
      <table style="width:100%;border-collapse:separate;border-spacing:10px 0;">
        <tr>
          <td style="width:50%;background:#f1f5f9;padding:18px;border-radius:10px;vertical-align:top;">
            <p style="margin:0 0 6px;font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#64748b;">
              Amount Payable
            </p>
            <p style="margin:0;font-size:22px;font-weight:700;color:#0f172a;line-height:1.2;">
              ₹ {amt_inr}
            </p>
            <p style="margin:4px 0 0;font-size:12px;color:#64748b;">{amt_for} {currency}</p>
          </td>
          <td style="width:50%;background:#f1f5f9;padding:18px;border-radius:10px;vertical-align:top;">
            <p style="margin:0 0 6px;font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#64748b;">
              Proposed Date
            </p>
            <p style="margin:0;font-size:22px;font-weight:700;color:#0f172a;line-height:1.2;">
              {prop_date}
            </p>
            <p style="margin:4px 0 0;font-size:12px;color:#64748b;">{country}</p>
          </td>
        </tr>
      </table>
    </div>

    <!-- divider -->
    <div style="padding:24px 36px 8px;">
      <p style="margin:0 0 14px;font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#94a3b8;">
        Transaction Details
      </p>
    </div>

    <!-- detail rows -->
    <div style="padding:0 36px 12px;">
      <table style="width:100%;border-collapse:collapse;font-size:14px;color:#0f172a;">
        {_kv_row("Remitter", company_name, alt=True)}
        {_kv_row("Vendor / Remittee", vendor)}
        {_kv_row("Country to Remit", country, alt=True)}
        {_kv_row("Currency", currency)}
        {_kv_row("Tax Category", tax_category, alt=True)}
        {_kv_row("Purpose Code (RBI)", purpose)}
        {_kv_row("DTAA", dtaa, alt=True)}
        {_kv_row("DTAA Article", dtaa_article)}
        {_kv_row("TRC Obtained", trc, alt=True)}
        {_kv_row("Grossed Up", gross_up)}
      </table>
    </div>

    <!-- attachment callout -->
    <div style="margin:24px 36px 0;padding:18px;background:linear-gradient(135deg,#ecfeff 0%,#dbeafe 100%);border:1px solid #bae6fd;border-radius:10px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="vertical-align:middle;width:48px;">
            <div style="width:40px;height:40px;background:#0ea5e9;border-radius:8px;text-align:center;line-height:40px;font-size:20px;color:#ffffff;">
              📎
            </div>
          </td>
          <td style="vertical-align:middle;padding-left:14px;">
            <p style="margin:0 0 2px;font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#0c4a6e;">
              Attachment
            </p>
            <p style="margin:0;font-size:14px;font-weight:600;color:#0f172a;">
              {docname}.json
            </p>
          </td>
        </tr>
      </table>
    </div>

    <!-- next steps -->
    <div style="padding:28px 36px 8px;">
      <p style="margin:0 0 14px;font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#94a3b8;">
        Next Steps
      </p>
      <ol style="margin:0;padding-left:20px;font-size:14px;color:#334155;line-height:1.8;">
        <li>Download the attached JSON file</li>
        <li>Login to the income-tax e-filing portal</li>
        <li>Upload the JSON under Form 15CB filing flow</li>
        <li>Review pre-filled fields and submit with your DSC</li>
      </ol>
    </div>

    <!-- closing -->
    <div style="padding:24px 36px 0;">
      <p style="margin:0 0 8px;font-size:14px;color:#334155;line-height:1.6;">
        For any clarifications, please reach out to the maker:
      </p>
      <p style="margin:0;font-size:14px;color:#0f172a;">
        <strong>{maker_name}</strong> &middot;
        <a href="mailto:{maker_email}" style="color:#4f46e5;text-decoration:none;">{maker_email}</a>
      </p>
    </div>

    <!-- footer -->
    <div style="margin-top:30px;padding:22px 36px;background:#0f172a;color:#cbd5e1;">
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="vertical-align:middle;">
            <p style="margin:0;font-size:14px;font-weight:600;color:#ffffff;">Remittance Tool</p>
            <p style="margin:4px 0 0;font-size:12px;color:#94a3b8;">Automated Form 15CB delivery</p>
          </td>
          <td style="vertical-align:middle;text-align:right;">
            <p style="margin:0;font-size:11px;color:#94a3b8;">Generated</p>
            <p style="margin:2px 0 0;font-size:13px;color:#e2e8f0;">{now_str}</p>
          </td>
        </tr>
      </table>
    </div>

  </div>

  <!-- legal footer -->
  <p style="max-width:640px;margin:18px auto 0;text-align:center;font-size:11px;color:#94a3b8;line-height:1.5;">
    This email is generated by the Meril Remittance Tool. Please do not reply directly — for queries, contact the maker named above.
  </p>

</body>
</html>"""


def _kv_row(label, value, alt=False):
	"""Single key-value row for the transaction details table."""
	bg = "background:#f8fafc;" if alt else ""
	return (
		f'<tr style="{bg}">'
		f'<td style="padding:11px 14px;color:#64748b;width:46%;border-bottom:1px solid #f1f5f9;">{label}</td>'
		f'<td style="padding:11px 14px;font-weight:600;color:#0f172a;border-bottom:1px solid #f1f5f9;">{value}</td>'
		f'</tr>'
	)


def _send_via_smtplib(settings, to_list, subject, body_html, attachments=None):
	"""Send an email via smtplib using Email Settings credentials.

	Uses the standard 3-level MIME structure for HTML + attachments:
	    multipart/mixed
	      ├─ multipart/alternative
	      │    ├─ text/plain     (fallback for non-HTML clients)
	      │    └─ text/html      (the styled template)
	      └─ application/json    (one per attachment)

	Older / stricter clients sometimes hide the HTML body if the structure
	is just multipart/mixed without an alternative wrapper — this fixes
	the "email shows only attachment, no body" symptom.
	"""
	smtp_server = settings.smtp_server
	smtp_port = int(settings.smtp_port or 587)
	use_tls = bool(settings.use_tls)
	use_ssl = bool(settings.use_ssl)
	smtp_user = settings.smtp_user
	smtp_password = settings.get_password("smtp_password")
	sender_email = settings.default_sender_email or smtp_user
	sender_name = settings.default_sender_name or ""
	from_addr = f"{sender_name} <{sender_email}>" if sender_name else sender_email

	has_attachments = bool(attachments)

	if has_attachments:
		# multipart/mixed — outer wrapper for body + attachments
		msg = MIMEMultipart("mixed")
		msg["Subject"] = subject
		msg["From"] = from_addr
		msg["To"] = ", ".join(to_list)

		# multipart/alternative — body in plain + HTML
		body_alt = MIMEMultipart("alternative")
		plain_fallback = "Please open this email in an HTML-capable client to view the formatted content."
		body_alt.attach(MIMEText(plain_fallback, "plain", "utf-8"))
		body_alt.attach(MIMEText(body_html, "html", "utf-8"))
		msg.attach(body_alt)

		# Attachments
		for att in attachments:
			mimetype = att.get("mimetype") or "application/octet-stream"
			maintype, _, subtype = mimetype.partition("/")
			part = MIMEBase(maintype or "application", subtype or "octet-stream")
			fcontent = att["fcontent"]
			if isinstance(fcontent, str):
				fcontent = fcontent.encode("utf-8")
			part.set_payload(fcontent)
			encoders.encode_base64(part)
			part.add_header(
				"Content-Disposition",
				f'attachment; filename="{att["fname"]}"',
			)
			msg.attach(part)
	else:
		# No attachments — just alternative (plain + HTML)
		msg = MIMEMultipart("alternative")
		msg["Subject"] = subject
		msg["From"] = from_addr
		msg["To"] = ", ".join(to_list)
		plain_fallback = "Please open this email in an HTML-capable client to view the formatted content."
		msg.attach(MIMEText(plain_fallback, "plain", "utf-8"))
		msg.attach(MIMEText(body_html, "html", "utf-8"))

	if use_ssl:
		conn = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=20)
	else:
		conn = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
		if use_tls:
			conn.starttls()
	conn.login(smtp_user, smtp_password)
	conn.sendmail(sender_email, to_list, msg.as_string())
	conn.quit()


@frappe.whitelist()
def suggest_recipients(docname):
	"""Return suggested recipient emails for the Send Email dialog.

	Suggestions include:
	  - Document owner (Maker)
	  - Linked CA Master email
	  - Linked Company email + secondary email
	  - Linked Vendor email
	"""
	doc = frappe.get_doc("Remittance Form 15 CB", docname)
	suggestions = []

	# 1. Maker
	owner_email = frappe.db.get_value("User", doc.owner, "email") or doc.owner
	if _looks_like_email(owner_email):
		suggestions.append({"email": owner_email, "label": f"Maker — {owner_email}"})

	# 2. CA email
	if doc.get("ca"):
		ca_email = frappe.db.get_value("CA Master", doc.ca, "email_id")
		ca_name = frappe.db.get_value("CA Master", doc.ca, "ca_name") or doc.ca
		if _looks_like_email(ca_email):
			suggestions.append({"email": ca_email, "label": f"CA — {ca_name} ({ca_email})"})

	# 3. Company email + secondary
	if doc.get("company"):
		try:
			company = frappe.get_doc("Remittance Company", doc.company)
			for fld, label in (("email_id", "Company"), ("secondary_email_id", "Company (Secondary)")):
				e = company.get(fld)
				if _looks_like_email(e):
					suggestions.append({"email": e, "label": f"{label} — {e}"})
		except frappe.DoesNotExistError:
			pass

	# 4. Vendor email
	if doc.get("vendor"):
		v_email = frappe.db.get_value("Remittance Vendor", doc.vendor, "email_id")
		if _looks_like_email(v_email):
			suggestions.append({"email": v_email, "label": f"Vendor — {v_email}"})

	# Dedup while preserving order
	seen = set()
	deduped = []
	for s in suggestions:
		if s["email"].lower() not in seen:
			seen.add(s["email"].lower())
			deduped.append(s)

	return {"suggestions": deduped}


# ─── helpers ─────────────────────────────────────────────────────────────

def _split_emails(value):
	if not value:
		return []
	if isinstance(value, str):
		value = frappe.parse_json(value) if value.strip().startswith("[") else value
	if isinstance(value, list):
		parts = value
	else:
		parts = [p.strip() for p in str(value).replace(";", ",").split(",")]
	return [p for p in (s.strip() for s in parts) if p and _looks_like_email(p)]


def _looks_like_email(value):
	if not value or not isinstance(value, str):
		return False
	return "@" in value and "." in value.split("@")[-1]


def _build_attachments(docname, doc, attach_json, attach_xml):
	"""Generate JSON / XML strings and wrap as Frappe attachment dicts."""
	out = []

	if int(attach_json or 0):
		from remittance_tool.remittance_tool.api.json_generator import (
			generate_remittance_json,
		)
		json_str = generate_remittance_json(docname)
		out.append({
			"fname": f"{docname}.json",
			"fcontent": json_str.encode("utf-8") if isinstance(json_str, str) else json_str,
		})

	if int(attach_xml or 0):
		from remittance_tool.remittance_tool.api.xml_generator_v2 import (
			generate_remittance_xml_v2,
		)
		xml_str = generate_remittance_xml_v2(docname)
		out.append({
			"fname": f"{docname}.xml",
			"fcontent": xml_str.encode("utf-8") if isinstance(xml_str, str) else xml_str,
		})

	return out


def _default_message(doc):
	"""Default HTML body used when caller doesn't pass a custom message."""
	remark = (doc.get("post_approval_remark") or "").strip()
	remark_html = f"<p><strong>Remark:</strong> {frappe.utils.escape_html(remark)}</p>" if remark else ""

	return f"""
		<p>Dear Sir/Madam,</p>
		<p>Please find attached the Form 15CB <strong>{frappe.utils.escape_html(doc.name)}</strong>
		for vendor <strong>{frappe.utils.escape_html(str(doc.get('vendor') or ''))}</strong>.</p>
		{remark_html}
		<p>Regards,<br>Remittance Tool</p>
	"""


def _log_email_event(doc, to_list, cc_list, bcc_list, attachments):
	"""Append a Comment on the form so the trail is visible in Desk."""
	files = ", ".join(a["fname"] for a in attachments) or "(none)"
	cc_part = f" · CC: {', '.join(cc_list)}" if cc_list else ""
	bcc_part = f" · BCC: {', '.join(bcc_list)}" if bcc_list else ""
	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Info",
		"reference_doctype": "Remittance Form 15 CB",
		"reference_name": doc.name,
		"content": (
			f"Email sent to: {', '.join(to_list)}{cc_part}{bcc_part}"
			f" · Attachments: {files} · By: {frappe.session.user}"
		),
	}).insert(ignore_permissions=True)

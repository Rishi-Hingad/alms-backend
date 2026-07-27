"""Manual SMTP test + Approval Matrix email diagnostic.

Two functions:
  - send_test_mail(to_email)              — quick SMTP test
  - diagnose_approval_emails(docname?)    — full audit of approval email setup

Both read from the custom 'Email Settings' Single doctype (same source as the
approval router uses), so passing send_test_mail also means the approval
router will be able to send emails — provided the Approval Matrix has
templates configured.

Usage (bench console):
    >>> from remittance_tool.remittance_tool.api.email_test import send_test_mail, diagnose_approval_emails
    >>> send_test_mail("hitesh.mahto@merillife.com")
    >>> diagnose_approval_emails("Remittance Form 15 CB")
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import frappe


# ────────────────────────────────────────────────────────────────────────
# 1. SMTP TEST (existing)
# ────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def send_test_mail(to_email):
	"""Send a hard-coded HTML test email using the Email Settings doctype."""
	report = {
		"to": to_email,
		"smtp_server": None,
		"smtp_port": None,
		"smtp_user": None,
		"use_tls": None,
		"use_ssl": None,
		"sender_email": None,
		"status": None,
		"message": None,
	}

	try:
		settings = frappe.get_single("Email Settings")
	except Exception as e:
		report["status"] = "settings_not_found"
		report["message"] = f"Could not load Email Settings doctype: {e}"
		print(_format(report, "EMAIL TEST RESULT"))
		return report

	smtp_server = settings.get("smtp_server")
	smtp_port = int(settings.get("smtp_port") or 587)
	smtp_user = settings.get("smtp_user")
	use_tls = bool(settings.get("use_tls"))
	use_ssl = bool(settings.get("use_ssl"))
	sender_email = settings.get("default_sender_email") or smtp_user
	sender_name = settings.get("default_sender_name") or ""

	report.update({
		"smtp_server": smtp_server, "smtp_port": smtp_port, "smtp_user": smtp_user,
		"use_tls": use_tls, "use_ssl": use_ssl, "sender_email": sender_email,
	})

	if not smtp_server or not smtp_user:
		report["status"] = "incomplete_settings"
		report["message"] = "smtp_server ya smtp_user blank hai Email Settings me."
		print(_format(report, "EMAIL TEST RESULT"))
		return report

	try:
		smtp_password = settings.get_password("smtp_password") if settings.get("smtp_password") else None
	except Exception as e:
		report["status"] = "password_error"
		report["message"] = f"smtp_password decrypt nahi ho saka: {e}"
		print(_format(report, "EMAIL TEST RESULT"))
		return report

	subject = f"Remittance Tool — Email Test {frappe.utils.now()}"
	from_header = f"{sender_name} <{sender_email}>" if sender_name else sender_email
	body_html = f"""<p>Test email from Remittance Tool — {frappe.utils.now()}</p>"""

	msg = MIMEMultipart()
	msg["From"] = from_header
	msg["To"] = to_email
	msg["Subject"] = subject
	msg.attach(MIMEText(body_html, "html"))

	send_error = None
	try:
		if use_ssl:
			server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=20)
		else:
			server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
			if use_tls:
				server.starttls()
		server.login(smtp_user, smtp_password)
		server.sendmail(sender_email, [to_email], msg.as_string())
		server.quit()
		report["status"] = "sent"
		report["message"] = f"Test email sent to {to_email}. Inbox check karo."
	except smtplib.SMTPAuthenticationError as e:
		send_error = f"SMTP auth failed: {e}"
		report["status"] = "auth_failed"
		report["message"] = send_error
	except smtplib.SMTPException as e:
		send_error = f"SMTP error: {e}"
		report["status"] = "smtp_error"
		report["message"] = send_error
	except Exception as e:
		send_error = f"Unexpected: {e}"
		frappe.log_error(frappe.get_traceback(), "Email Test Script Error")
		report["status"] = "unknown_error"
		report["message"] = send_error

	# Write to Remittance Email Log
	try:
		from remittance_tool.remittance_tool.utils.email_log import log_email
		log_email(
			status="Sent" if not send_error else "Failed",
			email_type="Test Mail",
			recipients=[to_email],
			subject=subject, body_html=body_html,
			smtp_server=smtp_server, smtp_user=smtp_user,
			from_address=sender_email,
			error=send_error,
		)
	except Exception:
		pass

	print(_format(report, "EMAIL TEST RESULT"))
	return report


# ────────────────────────────────────────────────────────────────────────
# 2. APPROVAL EMAIL DIAGNOSTIC
# ────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def diagnose_approval_emails(doctype="Remittance Form 15 CB"):
	"""Audit the approval-email setup for a given doctype.

	Checks:
	  1. Email Settings populated (SMTP + sender)
	  2. Approval Matrix exists for the doctype
	  3. send_email_alert flag is on
	  4. All 4 email templates configured + records exist
	  5. Per-stage email templates
	"""
	print("\n" + "=" * 72)
	print(f"APPROVAL EMAIL DIAGNOSTIC — {doctype}")
	print("=" * 72)

	# ── 1. Email Settings ─────────────────────────────────────────────
	print("\n[1] Email Settings:")
	try:
		s = frappe.get_single("Email Settings")
		ok_settings = all([s.smtp_server, s.smtp_user, s.smtp_password])
		print(f"    smtp_server:  {s.smtp_server or '(blank)'}")
		print(f"    smtp_user:    {s.smtp_user or '(blank)'}")
		print(f"    sender_email: {s.default_sender_email or '(blank — fallback to smtp_user)'}")
		print(f"    use_tls:      {bool(s.use_tls)}")
		print(f"    use_ssl:      {bool(s.use_ssl)}")
		print(f"    {'✅ Email Settings looks OK' if ok_settings else '❌ Email Settings incomplete'}")
	except Exception as e:
		print(f"    ❌ Could not load: {e}")
		return

	# ── 2. Approval Matrix ────────────────────────────────────────────
	print(f"\n[2] Approval Matrix for '{doctype}':")
	matrices = frappe.get_all("Approval Matrix",
		filters={"applies_to_doctype": doctype, "is_active": 1},
		fields=["name", "matrix_name", "send_email_alert",
				"submission_email_template", "rejection_email_template",
				"send_back_email_template", "final_approval_email_template"])

	if not matrices:
		print(f"    ❌ NO active Approval Matrix found for {doctype}")
		print(f"       Configure one at: /app/approval-matrix/new")
		return

	print(f"    ✅ Found {len(matrices)} active matrix/matrices")
	for m in matrices:
		print(f"\n    ━━━ Matrix: {m['matrix_name']} ({m['name']}) ━━━")
		print(f"      send_email_alert: {'✅ ON' if m['send_email_alert'] else '❌ OFF — emails will not be sent!'}")

		templates_to_check = [
			("submission_email_template",      "On submission → first approver"),
			("rejection_email_template",       "On rejection → maker"),
			("send_back_email_template",       "On send-back → target user"),
			("final_approval_email_template",  "On final approval → maker"),
		]
		for tmpl_field, purpose in templates_to_check:
			val = m[tmpl_field]
			if not val:
				print(f"      {tmpl_field}: ❌ NOT SET  ({purpose})")
				continue
			exists = frappe.db.exists("Email Template", val)
			mark = "✅" if exists else "⚠️  RECORD MISSING"
			print(f"      {tmpl_field}: {mark} {val}  ({purpose})")

		# Per-stage templates — child table is "Approval Matrix Item" on
		# the matrix's `approval_stages` field. Field names are:
		#   approval_stage, approval_stage_name, approver_type, user, role,
		#   send_email, email_template
		try:
			matrix_doc = frappe.get_doc("Approval Matrix", m["name"])
			stages = sorted(
				matrix_doc.get("approval_stages") or [],
				key=lambda r: r.get("approval_stage") or 0,
			)
		except Exception as e:
			stages = []
			print(f"\n      ⚠️  Could not load stages: {e}")

		if stages:
			print(f"\n      Stages ({len(stages)}):")
			for st in stages:
				approver = st.user if st.approver_type == "User" else (
					f"role={st.role}" if st.approver_type == "Role" else (st.approver_type or "(unset)")
				)
				if st.send_email:
					email_part = (
						"  ✉ email: " + st.email_template if st.email_template
						else "  ✉ (uses matrix template)"
					)
				else:
					email_part = "  (no per-stage email)"
				stage_label = st.approval_stage_name or f"Stage {st.approval_stage}"
				print(f"        [{st.approval_stage}] {stage_label}: {st.approver_type} = {approver}{email_part}")
		else:
			print("\n      (no stages found on this matrix)")

	# ── 3. Recent email queue (last 5 entries for this site) ──────────
	print(f"\n[3] Recent Email Queue (last 5):")
	queue = []
	# Try multiple field combos — Email Queue schema differs across Frappe versions
	for field_set in (
		["name", "status", "error", "sender", "reference_doctype", "reference_name", "creation"],
		["name", "status", "error", "creation"],
		["name", "status", "creation"],
	):
		try:
			queue = frappe.get_all("Email Queue", fields=field_set,
				order_by="creation desc", limit=5)
			break
		except Exception:
			continue

	if not queue:
		print("    (queue empty or unable to query)")
	else:
		for q in queue:
			err = ((q.get('error') or "")[:80])
			ref = f"{q.get('reference_doctype', '')}/{q.get('reference_name', '')}" if q.get('reference_doctype') else ""
			line = f"    [{q['creation']}] {q['status']:10s} | {q.get('name', '')}"
			if ref:
				line += f" | {ref}"
			print(line)
			if err:
				print(f"      └ Error: {err}")

	print("\n" + "=" * 72)
	print("DONE")
	print("=" * 72 + "\n")


# ────────────────────────────────────────────────────────────────────────
# 3. ROUTER EMAIL TRIGGER TEST
# ────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def test_router_email(template_name, to_email, doctype=None, doc_name=None):
	"""Trigger the approval router's _send_email() helper directly.

	Use this to confirm the *router's* email path works end-to-end (not just
	SMTP). If this sends an email but actual approval actions don't, the
	bug is in the matrix configuration or trigger logic, not the email path.

	Args:
		template_name: Email Template name (e.g. "Approval Submission")
		to_email:      recipient address
		doctype/doc_name: optional — used to give the template a real `doc`
		                   context. If blank, a dummy doc is used.
	"""
	from remittance_tool.remittance_tool.approval.router import _send_email

	# Build context — most templates expect `doc` and `action`
	if doctype and doc_name:
		try:
			doc = frappe.get_doc(doctype, doc_name)
		except Exception as e:
			print(f"❌ Could not load {doctype}/{doc_name}: {e}")
			return
	else:
		# Dummy doc-like object
		doc = frappe._dict(name="DUMMY-001", owner="test@example.com")

	try:
		_send_email(template_name, [to_email], {
			"doc": doc,
			"action": "Test",
			"next_user": to_email,
			"sent_by": frappe.session.user,
			"target_user": to_email,
			"remarks": "Diagnostic test from email_test.py",
		})
		print(f"✅ _send_email() returned without exception")
		print(f"   Template: {template_name}")
		print(f"   To:       {to_email}")
		print(f"   Inbox check karo 1-2 min me.")
	except Exception as e:
		print(f"❌ _send_email() failed: {e}")


# ────────────────────────────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────────────────────────────

def _format(report, title):
	lines = ["", "=" * 60, title + " (Email Settings doctype)", "=" * 60]
	for key in ("smtp_server", "smtp_port", "smtp_user", "use_tls", "use_ssl",
				"sender_email", "to", "status", "message"):
		val = report.get(key)
		if val is not None:
			lines.append(f"  {key:15s}: {val}")
	lines.append("=" * 60)
	return "\n".join(lines)

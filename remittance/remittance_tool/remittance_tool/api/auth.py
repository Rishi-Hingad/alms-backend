"""Custom authentication endpoints — override Frappe's password reset flow
to use our Email Settings (Zeptomail SMTP) instead of frappe.sendmail().

Registered as override in hooks.py:
    override_whitelisted_methods = {
        "frappe.core.doctype.user.user.reset_password":
            "remittance_tool.remittance_tool.api.auth.reset_password",
    }
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def reset_password(user):
	"""Frappe's reset_password override — sends the reset link via our SMTP."""
	try:
		user_doc = frappe.get_doc("User", user)
	except frappe.DoesNotExistError:
		frappe.local.response["http_status_code"] = 404
		return _("User {0} not found").format(user)

	if user_doc.name == "Administrator":
		return _("Not allowed to reset the password of Administrator")

	if not user_doc.enabled:
		frappe.local.response["http_status_code"] = 400
		return _("Account is disabled")

	# Generate the reset key WITHOUT sending Frappe's default email.
	# Method name varies by Frappe version:
	#   v15 & older: user_doc.reset_password()
	#   v16+:        user_doc._reset_password()
	# Both return a full URL. If neither is present, fall back to manual key gen.
	reset_url = _generate_reset_link(user_doc)

	_send_reset_email(user_doc, reset_url)
	return _("Password reset instructions have been sent to your email.")


def _generate_reset_link(user_doc):
	for method_name in ("_reset_password", "reset_password"):
		method = getattr(user_doc, method_name, None)
		if callable(method):
			return method(send_email=False)

	# Manual fallback — replicate Frappe's internal key-generation logic
	from frappe.utils.data import sha256_hash

	key = frappe.generate_hash()
	hashed_key = sha256_hash(key)
	user_doc.db_set("reset_password_key", hashed_key)
	user_doc.db_set("last_reset_password_key_generated_on", frappe.utils.now_datetime())
	return frappe.utils.get_url(f"/update-password?key={key}")


def _send_reset_email(user_doc, reset_url):
	settings = frappe.get_single("Email Settings")

	smtp_server = settings.get("smtp_server")
	smtp_port = int(settings.get("smtp_port") or 587)
	smtp_user = settings.get("smtp_user")
	use_tls = bool(settings.get("use_tls"))
	use_ssl = bool(settings.get("use_ssl"))
	sender_email = settings.get("default_sender_email") or smtp_user
	sender_name = settings.get("default_sender_name") or "Remittance Portal"

	try:
		smtp_password = settings.get_password("smtp_password") if settings.get("smtp_password") else None
	except Exception:
		smtp_password = None

	if not all([smtp_server, smtp_user, smtp_password]):
		frappe.throw(_("Email Settings incomplete — cannot send password reset link"))

	# Test-mode override — redirect all mail to a single inbox
	original_to = user_doc.email or user_doc.name
	to_email = original_to
	subject = "Password Reset — Remittance Portal"
	if settings.get("test_mode_enabled"):
		test_recipient = settings.get("test_recipient_email")
		if test_recipient:
			subject = f"[TEST → {original_to}] {subject}"
			to_email = test_recipient

	body_html = _build_reset_email_html(user_doc, reset_url)
	body_plain = (
		f"Hello {user_doc.first_name or user_doc.full_name or user_doc.name},\n\n"
		f"Click the link below to reset your Remittance Portal password:\n{reset_url}\n\n"
		f"If you did not request this, ignore this email."
	)

	from_header = f"{sender_name} <{sender_email}>" if sender_name else sender_email

	msg = MIMEMultipart("alternative")
	msg["From"] = from_header
	msg["To"] = to_email
	msg["Subject"] = subject
	msg.attach(MIMEText(body_plain, "plain"))
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
	except Exception as e:
		send_error = str(e)
		frappe.log_error(frappe.get_traceback(), "Password Reset Email Error")

	# Audit trail
	try:
		from remittance_tool.remittance_tool.utils.email_log import log_email
		log_email(
			status="Sent" if not send_error else "Failed",
			email_type="Password Reset",
			recipients=[to_email],
			subject=subject,
			body_html=body_html,
			smtp_server=smtp_server,
			smtp_user=smtp_user,
			from_address=sender_email,
			reference_doctype="User",
			reference_name=user_doc.name,
			error=send_error,
		)
	except Exception:
		pass

	if send_error:
		frappe.throw(_("Could not send reset email: {0}").format(send_error))


def _build_reset_email_html(user_doc, reset_url):
	full_name = user_doc.full_name or user_doc.first_name or user_doc.name
	safe_name = frappe.utils.escape_html(full_name)
	safe_url = frappe.utils.escape_html(reset_url)
	return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
	<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f5f9;padding:32px 12px;">
		<tr><td align="center">
			<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,.06);max-width:600px;">
				<tr>
					<td style="background:linear-gradient(135deg,#1d4ed8,#1e40af);padding:32px;text-align:center;">
						<h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;letter-spacing:.5px;">Password Reset</h1>
						<p style="margin:6px 0 0;color:#dbeafe;font-size:13px;">Remittance Portal</p>
					</td>
				</tr>
				<tr>
					<td style="padding:32px 40px 24px;color:#1e293b;font-size:14px;line-height:1.6;">
						<p style="margin:0 0 12px;">Hello <b>{safe_name}</b>,</p>
						<p style="margin:0 0 20px;">We received a request to reset your Remittance Portal password. Click the button below to choose a new password:</p>
						<p style="text-align:center;margin:24px 0;">
							<a href="{safe_url}" style="display:inline-block;padding:12px 32px;background:#1d4ed8;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;font-size:15px;">Reset Password</a>
						</p>
						<p style="margin:16px 0 0;color:#64748b;font-size:12px;">If the button does not work, copy this link into your browser:</p>
						<p style="margin:6px 0 0;color:#1d4ed8;font-size:11px;word-break:break-all;">{safe_url}</p>
						<hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
						<p style="margin:0;color:#94a3b8;font-size:12px;">If you did not request this reset, ignore this email &mdash; your password will remain unchanged. This link will expire.</p>
					</td>
				</tr>
				<tr>
					<td style="background:#f8fafc;padding:16px;text-align:center;color:#94a3b8;font-size:11px;">
						Meril Life Sciences &middot; Remittance Portal
					</td>
				</tr>
			</table>
		</td></tr>
	</table>
</body>
</html>"""

"""Email Template installer for the Remittance Form 15 CB approval flow.

Creates / updates four Email Template records that the Approval Matrix uses:

  - Form 15CB - Approval Required   (submission_email_template + mid-stage fallback)
  - Form 15CB - Rejected            (rejection_email_template)
  - Form 15CB - Sent Back           (send_back_email_template)
  - Form 15CB - Approved            (final_approval_email_template)

Run from bench:
    bench --site <site> execute remittance_tool.remittance_tool.approval.email_templates.install

After install, link these names in the Approval Matrix > Email Alerts section.
"""
import frappe

_BASE_STYLE = (
	"margin:0; padding:24px; background:#f5f7fa; "
	"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; "
	"color:#1a202c;"
)


def _shell(top_bar_color, title, subtitle, body_html, cta_label, cta_color, status_pill_html=""):
	"""Render the shared card layout. body_html is injected verbatim."""
	return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="{_BASE_STYLE}">
  <div style="max-width:600px; margin:0 auto; background:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.06);">
    <div style="height:6px; background:{top_bar_color};"></div>
    <div style="padding:32px 32px 8px;">
      <h1 style="margin:0 0 6px; font-size:22px; font-weight:700; color:#1a202c;">{title}</h1>
      <p style="margin:0; font-size:14px; color:#718096;">{subtitle}</p>
      {status_pill_html}
    </div>
    {body_html}
    <div style="padding:24px 32px;">
      <div style="text-align:center;">
        <a href="{{{{ frappe.utils.get_url() }}}}/app/remittance-form-15-cb/{{{{ doc.name }}}}"
           style="display:inline-block; padding:12px 28px; background:{cta_color}; color:#ffffff; text-decoration:none; font-weight:600; font-size:14px; border-radius:6px;">
          {cta_label}
        </a>
      </div>
    </div>
    <div style="padding:20px 32px; background:#f8fafc; border-top:1px solid #e2e8f0;">
      <p style="margin:0; font-size:12px; color:#718096;">Submitted by</p>
      <p style="margin:4px 0 0; font-size:14px; font-weight:600; color:#1a202c;">
        {{{{ frappe.db.get_value("User", doc.owner, "full_name") or doc.owner }}}}
      </p>
    </div>
  </div>
</body>
</html>"""


_DETAILS_TABLE = """
    <div style="padding:0 32px;">
      <p style="margin:16px 0 12px; font-size:14px; color:#1a202c;"><strong>Dear {{ recipient_name or "User" }},</strong></p>
      <p style="margin:0 0 20px; font-size:14px; color:#4a5568; line-height:1.55;">{{ message_line }}</p>
    </div>
    <div style="margin:0 32px; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">
      <table style="width:100%; border-collapse:collapse; font-size:14px;">
        <tr style="background:#f8fafc;">
          <td style="padding:14px 18px; color:#718096; width:40%;">Form No.</td>
          <td style="padding:14px 18px; color:#1a202c; font-weight:600;">{{ doc.name }}</td>
        </tr>
        <tr>
          <td style="padding:14px 18px; color:#718096;">Company</td>
          <td style="padding:14px 18px; color:#1a202c; font-weight:600;">{{ doc.company or "-" }}</td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:14px 18px; color:#718096;">Requester</td>
          <td style="padding:14px 18px; color:#1a202c; font-weight:600;">
            {{ frappe.db.get_value("User", doc.owner, "full_name") or doc.owner }}
          </td>
        </tr>
        <tr>
          <td style="padding:14px 18px; color:#718096;">Vendor</td>
          <td style="padding:14px 18px; color:#1a202c; font-weight:600;">{{ doc.vendor or "-" }}</td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:14px 18px; color:#718096;">Country</td>
          <td style="padding:14px 18px; color:#1a202c; font-weight:600;">{{ doc.country_to_remit or "-" }}</td>
        </tr>
        <tr>
          <td style="padding:14px 18px; color:#718096;">Currency</td>
          <td style="padding:14px 18px; color:#1a202c; font-weight:600;">{{ doc.currency or "-" }}</td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:14px 18px; color:#718096;">Purpose</td>
          <td style="padding:14px 18px; color:#1a202c; font-weight:600;">{{ doc.purpose_code or "-" }}</td>
        </tr>
        <tr>
          <td style="padding:14px 18px; color:#718096;">Nature of Remittance</td>
          <td style="padding:14px 18px; color:#1a202c; font-weight:600;">{{ doc.nature_of_remittance or "-" }}</td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:14px 18px; color:#718096;">Proposed Date</td>
          <td style="padding:14px 18px; color:#1a202c; font-weight:600;">{{ doc.proposed_date_of_remittance or "-" }}</td>
        </tr>
        <tr>
          <td style="padding:14px 18px; color:#718096;">Amount Payable</td>
          <td style="padding:14px 18px; color:#3b82f6; font-weight:700; font-size:16px;">
            {{ "{:,.2f}".format(doc.amount_payable_inr or 0) }} INR
          </td>
        </tr>
      </table>
    </div>
"""


_REMARKS_BLOCK = """
    <div style="margin:16px 32px 0; padding:14px 18px; background:#fff7ed; border-left:3px solid #f59e0b; border-radius:4px;">
      <p style="margin:0 0 6px; font-size:12px; color:#92400e; text-transform:uppercase; letter-spacing:0.05em; font-weight:600;">Remarks</p>
      <p style="margin:0; font-size:14px; color:#1a202c; line-height:1.5;">{{ remarks or "(no remarks provided)" }}</p>
    </div>
    <div style="padding:24px 32px 0;">
      <p style="margin:0; font-size:14px; color:#4a5568; line-height:1.55;">{{ closing_line }}</p>
    </div>
"""


_CLOSING_BLOCK = """
    <div style="padding:24px 32px 0;">
      <p style="margin:0; font-size:14px; color:#4a5568; line-height:1.55;">{{ closing_line }}</p>
    </div>
"""


def _approval_required_template():
	body = (
		"{% set recipient_name = next_user and (frappe.db.get_value('User', next_user, 'full_name') or next_user) or 'Approver' %}"
		"{% set message_line = 'A Form 15CB remittance has been submitted and requires your review and approval.' %}"
		"{% set closing_line = 'Kindly review the submitted form and take the appropriate action.' %}"
		+ _DETAILS_TABLE
		+ _CLOSING_BLOCK
	)
	return {
		"name": "Form 15CB - Approval Required",
		"subject": "Action Required: Approve Form 15CB {{ doc.name }}",
		"response_html": _shell(
			top_bar_color="#3b82f6",
			title="Form 15CB Approval Required",
			subtitle="A remittance form has been submitted for your approval",
			body_html=body,
			cta_label="Review & Approve Form 15CB",
			cta_color="#3b82f6",
		),
	}


def _rejected_template():
	body = (
		"{% set recipient_name = frappe.db.get_value('User', doc.owner, 'full_name') or doc.owner %}"
		"{% set rejected_by_name = frappe.db.get_value('User', rejected_by, 'full_name') or rejected_by %}"
		"{% set message_line = 'Your Form 15CB has been rejected by ' ~ rejected_by_name ~ '.' %}"
		"{% set closing_line = 'Please review the remarks and resubmit the form if applicable.' %}"
		+ _DETAILS_TABLE
		+ _REMARKS_BLOCK
	)
	pill = (
		'<div style="margin-top:12px;">'
		'<span style="display:inline-block; padding:4px 10px; background:#fee2e2; '
		'color:#991b1b; font-size:12px; font-weight:600; border-radius:4px; '
		'text-transform:uppercase; letter-spacing:0.05em;">Rejected</span></div>'
	)
	return {
		"name": "Form 15CB - Rejected",
		"subject": "Form 15CB {{ doc.name }} - Rejected",
		"response_html": _shell(
			top_bar_color="#ef4444",
			title="Form 15CB Rejected",
			subtitle="Your remittance form has been rejected",
			body_html=body,
			cta_label="View Form 15CB",
			cta_color="#ef4444",
			status_pill_html=pill,
		),
	}


def _sent_back_template():
	body = (
		"{% set recipient_name = frappe.db.get_value('User', target_user, 'full_name') or target_user %}"
		"{% set sent_by_name = frappe.db.get_value('User', sent_by, 'full_name') or sent_by %}"
		"{% set message_line = 'A Form 15CB has been sent back to you by ' ~ sent_by_name ~ ' for revision.' %}"
		"{% set closing_line = 'Please review the remarks, update the form as required, and resubmit for approval.' %}"
		+ _DETAILS_TABLE
		+ _REMARKS_BLOCK
	)
	pill = (
		'<div style="margin-top:12px;">'
		'<span style="display:inline-block; padding:4px 10px; background:#fef3c7; '
		'color:#92400e; font-size:12px; font-weight:600; border-radius:4px; '
		'text-transform:uppercase; letter-spacing:0.05em;">Sent Back</span></div>'
	)
	return {
		"name": "Form 15CB - Sent Back",
		"subject": "Form 15CB {{ doc.name }} - Sent Back for Revision",
		"response_html": _shell(
			top_bar_color="#f59e0b",
			title="Form 15CB Sent Back",
			subtitle="A remittance form has been sent back for revision",
			body_html=body,
			cta_label="Open Form 15CB",
			cta_color="#f59e0b",
			status_pill_html=pill,
		),
	}


def _approved_template():
	body = (
		"{% set recipient_name = frappe.db.get_value('User', doc.owner, 'full_name') or doc.owner %}"
		"{% set approved_by_name = frappe.db.get_value('User', approved_by, 'full_name') or approved_by %}"
		"{% set message_line = 'Your Form 15CB has been fully approved. The approval flow is complete.' %}"
		"{% set closing_line = 'You can now proceed with the remittance process.' %}"
		+ _DETAILS_TABLE
		+ _CLOSING_BLOCK
	)
	pill = (
		'<div style="margin-top:12px;">'
		'<span style="display:inline-block; padding:4px 10px; background:#d1fae5; '
		'color:#065f46; font-size:12px; font-weight:600; border-radius:4px; '
		'text-transform:uppercase; letter-spacing:0.05em;">Approved</span></div>'
	)
	return {
		"name": "Form 15CB - Approved",
		"subject": "Form 15CB {{ doc.name }} - Approved",
		"response_html": _shell(
			top_bar_color="#10b981",
			title="Form 15CB Approved",
			subtitle="Your remittance form has been fully approved",
			body_html=body,
			cta_label="View Approved Form 15CB",
			cta_color="#10b981",
			status_pill_html=pill,
		),
	}


def install():
	"""Create or update all four Email Template records."""
	templates = [
		_approval_required_template(),
		_rejected_template(),
		_sent_back_template(),
		_approved_template(),
	]
	for t in templates:
		if frappe.db.exists("Email Template", t["name"]):
			doc = frappe.get_doc("Email Template", t["name"])
			doc.subject = t["subject"]
			doc.response_html = t["response_html"]
			doc.use_html = 1
			doc.save(ignore_permissions=True)
			print(f"Updated: {t['name']}")
		else:
			doc = frappe.new_doc("Email Template")
			doc.name = t["name"]
			doc.subject = t["subject"]
			doc.response_html = t["response_html"]
			doc.use_html = 1
			doc.insert(ignore_permissions=True)
			print(f"Created: {t['name']}")
	frappe.db.commit()
	print("\nAll templates installed. Now link them in Approval Matrix > Email Alerts.")

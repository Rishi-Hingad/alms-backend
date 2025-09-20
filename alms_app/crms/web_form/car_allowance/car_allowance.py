import frappe
from frappe.core.doctype.communication.email import make
from email.mime.text import MIMEText
import smtplib
from alms_app.api.emailsService import email_sender


@frappe.whitelist(allow_guest=True)
def get_employee_details(employee_code):
    employee = frappe.get_all("Employee Master", filters={"name": employee_code}, 
    fields=["name", "designation", "location", "company", "contact_number", "email_id", "department", "eligibility" ,"reporting_head"])
    
    employee_eligibility = frappe.get_doc("Employee Designation",employee[0].designation)
    employee.append({"eligibility":employee_eligibility.eligibility})
    if employee:
        employee_details = employee[0]
        return employee
    else:
        frappe.throw(f"Employee with name '{employee_code}' not found.")
    
def get_context(context):
    context.employee_code = frappe.form_dict.get('employee_code')
    context.employee_details = {}

    if context.employee_code:
        employee_details = get_employee_details(context.employee_code)
        context.employee_details = employee_details

    return context

    
@frappe.whitelist(allow_guest=True)
def send_allowance_email(employee_code):
    try:
        employee = frappe.get_doc("Employee Master", employee_code)
        email_to = employee.email_id
        cc_employee = frappe.get_doc("Employee Master", employee.reporting_head)
        email_cc = cc_employee.email_id
        hr_entries = frappe.get_all(
            "Management Team",
            filters={"designation": "HR"},
            fields=["full_name", "email_id"]
        )
        hr_emails = [row.email_id for row in hr_entries if row.email_id]
        hr_name = ", ".join([row.full_name for row in hr_entries]) or "HR Team"

        if not hr_emails:
            frappe.throw("No HR emails found in Management Team.")

        # Fetch BCC from site_config.json
        site_config = frappe.get_site_config()
        bcc_emails = site_config.get("bcc_email", [])

        subject = "Car Allowance Request Submitted"
        message = f"Dear {hr_name},<br><br> {employee.employee_name} has requested for <strong>Car Allowance</strong> instead of Company Vehicle. Please reach out to the employee to share the process to get the car on allowance.<br><br>Thanks & Regards,<br>CRMS<br><br><strong>Note:</strong> This is an auto-generated email. Please do not reply to this email.<br><br>"
        frappe.sendmail(
            recipients=hr_emails,
            subject=subject,
            message=message,
            cc=[email_cc] if email_cc else [],
            bcc=bcc_emails
        )
        return {"status": "success", "message": f"Email sent successfully to {', '.join(hr_emails)}."}

    except Exception as e:
        frappe.log_error(f"Error in send_allowance_email: {str(e)}")
        return {"status": "failed", "message": str(e)}
    
@frappe.whitelist()
def check_allowance_exists(employee_code):
    exists = frappe.db.exists("Car Allowance", {"employee_code": employee_code, "docstatus": ["<", 2]})
    return "exists" if exists else "not_exists"

@frappe.whitelist()
def create_allowance_entry(employee_code):
    # Check again to avoid duplicates if called directly
    exists = frappe.db.exists("Car Allowance", {"employee_code": employee_code, "docstatus": ["<", 2]})
    if exists:
        return {"status": "failed", "message": "Allowance already exists"}

    # Create new entry
    doc = frappe.new_doc("Car Allowance")
    doc.employee_code = employee_code
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    # Trigger email via your existing method
    send_allowance_email(employee_code)

    return {"status": "success", "message": f"Allowance created for {employee_code}"}

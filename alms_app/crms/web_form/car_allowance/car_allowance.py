import frappe
from frappe.core.doctype.communication.email import make
from email.mime.text import MIMEText
import smtplib
from alms_app.newutils.custom_sendmail import custom_sendmail
from alms_app.api.emailsService import email_sender


@frappe.whitelist(allow_guest=True)
def get_employee_details(employee_code):
    employee = frappe.get_all("Employee", filters={"name": employee_code}, fields=["*"])
    
    if not employee:
        frappe.throw(f"Employee with name '{employee_code}' not found.")
        
    emp = employee[0]
        
    # Determine eligibility from Employee Designation or fallback to inline value
    eligibility_val = emp.get("eligibility") or 0
    if emp.get("meril_designation"):
        designation_eligibility = frappe.db.get_value("Employee Designation", emp.meril_designation, "eligibility")
        if designation_eligibility is not None:
            eligibility_val = designation_eligibility
            
    # Map fields for frontend compatibility
    emp["eligibility"] = eligibility_val
    emp["location"] = emp.get("branch")
    emp["contact_number"] = emp.get("cell_number")
    emp["email_id"] = emp.get("company_email") or emp.get("user_id")
    
    return [emp]

    
def get_context(context):
    context.employee_code = frappe.form_dict.get('employee_code')
    context.employee_details = {}

    if context.employee_code:
        employee_details = get_employee_details(context.employee_code)
        context.employee_details = employee_details

    return context

    
@frappe.whitelist(allow_guest=True)
def send_allowance_email(employee_code):
    from alms_app.api.emailClass import EmailServices
    return EmailServices().send_allowance_email(employee_code)
    
@frappe.whitelist(allow_guest=True)
def check_allowance_exists(employee_code):
    exists = frappe.db.exists("Car Allowance", {"employee_code": employee_code, "docstatus": ["<", 2]})
    return "exists" if exists else "not_exists"

@frappe.whitelist(allow_guest=True)
def create_allowance_entry(employee_code):
    # Check again to avoid duplicates if called directly
    exists = frappe.db.exists("Car Allowance", {"employee_code": employee_code, "docstatus": ["<", 2]})
    if exists:
        return {"status": "failed", "message": "Allowance already exists"}

    try:
        # Create new entry
        doc = frappe.new_doc("Car Allowance")
        doc.employee_code = employee_code
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
    except frappe.exceptions.DuplicateEntryError:
        return {"status": "failed", "message": f"Car Allowance {employee_code} already exists"}

    # Trigger email via your existing method
    send_allowance_email(employee_code)

    return {"status": "success", "message": f"Allowance created for {employee_code}"}

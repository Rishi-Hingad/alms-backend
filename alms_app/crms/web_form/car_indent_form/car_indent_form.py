import frappe
from frappe.core.doctype.communication.email import make
from email.mime.text import MIMEText
import smtplib
from alms_app.api.emailsService import email_sender


@frappe.whitelist(allow_guest=True)
def get_employee_details(employee_code):
    employee = frappe.get_all("Employee Master", filters={"name": employee_code}, 
    fields=["name", "designation", "location", "company", "contact_number", "email_id", "department","eligibility","reporting_head"])
    
    employee_eligibility = frappe.get_doc("Employee Designation",employee[0].designation)
    employee.append({"eligibility":employee_eligibility.eligibility})
    if employee:
        employee_details = employee[0]
        return employee
    else:
        frappe.throw(f"Employee with name '{employee_code}' not found.")
        
@frappe.whitelist(allow_guest=True)
def calculate_totals(frm_data):
    ex_showroom_price = frm_data.get('ex_showroom_price', 0)
    discount = frm_data.get('discount', 0)
    tcs = frm_data.get('tcs', 0)
    registration_charges = frm_data.get('registration_charges', 0)
    accessories = frm_data.get('accessories', 0)
    
    net_ex_showroom_price = ex_showroom_price - discount + tcs
    finance_amount = net_ex_showroom_price + registration_charges + accessories
    
    result = {
        "net_ex_showroom_price": f"₹ {net_ex_showroom_price:,.2f}",
        "finance_amount": f"₹ {finance_amount:,.2f}"
    }
    
    return result

def get_context(context):
    context.employee_code = frappe.form_dict.get('employee_code')
    context.employee_details = {}

    if context.employee_code:
        employee_details = get_employee_details(context.employee_code)
        context.employee_details = employee_details

    return context

@frappe.whitelist(allow_guest=True)
def check_indent_exists(employee_code):
    """Check if a Car Indent Form already exists for the given employee."""
    print(f"Checking if Car Indent Form exists for employee code: {employee_code}")
    
    exists = frappe.db.exists("Car Indent Form", {"name": employee_code})
    
    print(f"Indent exists: {exists}")
    
    if exists:
        return "redirect"
    
    return False

@frappe.whitelist(allow_guest=True)
def send_email_to_reporting_head(employee_code):
    try:
        employee = frappe.get_doc("Employee Master", employee_code)
        print("------------[EMPLOYEE]------------------:",employee)
        email_sender(name=employee_code, email_send_to="To Reporting")
        return {"status": "success", "message": f"Email sent successfully to {employee.email_id}."}

    except Exception as e:
        frappe.log_error(f"Error in send_email_to_reporting_head: {str(e)}")
        return {"status": "failed", "message": str(e)}
    
@frappe.whitelist(allow_guest=True)
def send_allowance_email(employee_code):
    try:
        employee = frappe.get_doc("Employee Master", employee_code)
        email_to = employee.email_id
        cc_employee = frappe.get_doc("Employee Master", employee.reporting_head)
        email_cc = cc_employee.email_id
        hr_email = frappe.get_value("Management Team", {"designation": "HR"}, "email_id")
        hr_name = frappe.get_value("Management Team", {"designation": "HR"}, "full_name")

        if not hr_email:
            frappe.throw("HR email not found in Management Team.")

        subject = "Car Allowance Request Submitted"
        message = f"Dear {hr_name},<br><br> {employee.employee_name} has requested for <strong>Car Allowance</strong> instead of Company Vehicle. Please reach out to the employee to share the process to get the car on allowance.<br><br>Thanks & Regards,<br>CRMS<br><br><strong>Note:</strong> This is an auto-generated email. Please do not reply to this email.<br><br>"
        # print("------------[EMAIL MESSAGE]------------------:",email_to,email_cc,hr_email)
        frappe.sendmail(
            recipients=[hr_email],
            subject=subject,
            message=message,
            bcc=["rishi.hingad@merillife.com",email_to],
            cc=[email_cc]
        )
        return {"status": "success", "message": f"Email sent successfully to {email_to}."}

    except Exception as e:
        frappe.log_error(f"Error in send_allowance_email: {str(e)}")
        return {"status": "failed", "message": str(e)}







# test comment
import frappe
from frappe.core.doctype.communication.email import make
from email.mime.text import MIMEText
import smtplib

@frappe.whitelist(allow_guest=True)
def get_employee_details(employee_code):
    employee = frappe.get_all("Employee Master", filters={"name": employee_code}, 
    fields=["name", "designation", "eligibility", "location", "company", "contact_number", "email_id", "employee_department"])

    if employee:
        # Return the employee details
        employee_details = employee[0]
        return employee_details
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

import frappe

@frappe.whitelist()
def send_email_to_reporting_head(employee_code):
    try:
        # Fetch the Employee Master record
        employee = frappe.get_doc("Employee Master", employee_code)
        
        # Use the existing send_email method
        employee.send_email()

        # Return success message
        return {"status": "success", "message": f"Email sent successfully to {employee.email_id}."}

    except Exception as e:
        frappe.log_error(f"Error in send_email_to_reporting_head: {str(e)}")
        return {"status": "failed", "message": str(e)}

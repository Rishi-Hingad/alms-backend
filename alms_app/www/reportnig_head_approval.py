
import frappe


def get_context(context):
    id = frappe.form_dict.get("id")
    form_data  = frappe.get_doc("Car Indent Form",id)
    user  = frappe.get_doc("Employee Master",form_data.employee_code)
    context["id"] = id
    context["employee_name"] = user.employee_name
    context["employee_email"] = form_data.email_id
    context["reporting_head_name"] = form_data.employee_reporting
    context["vehicle_make_model"] = f"{form_data.make}-{form_data.model}"
    context["net_ex_showroom_price"] = form_data.net_ex_showroom_price
    context["finance_amount"] = form_data.finance_amount
    context["company_name"] = user.company
    context["designation"] = user.designation
    context["eligibility"] = user.eligibility
    
    context["link"] = f"{frappe.utils.get_url()}/api/method/alms_app.api.emailsService.approve_car_indent_by_reporting?indent_form={user.name}"
    return context
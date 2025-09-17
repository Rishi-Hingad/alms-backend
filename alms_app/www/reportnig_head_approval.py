import frappe

def get_context(context):
    id = frappe.form_dict.get("id")
    
    if not id:
        frappe.throw("Missing Car Indent Form ID in URL")
    
    try:
        form_data = frappe.get_doc("Car Indent Form", id)
    except frappe.DoesNotExistError:
        try:
         
            employee_name = id
            emp = frappe.get_doc("Employee Master", employee_name)
            forms = frappe.get_all(
                "Car Indent Form",
                filters={"employee_code": emp.name},
                fields=["name"],
                order_by="creation desc",
                limit=1
            )
            if not forms:
                frappe.throw(f"No Car Indent Form found for {emp.employee_name}")
            form_data = frappe.get_doc("Car Indent Form", forms[0].name)
        except frappe.DoesNotExistError:
            frappe.throw(f"No Employee Master or Car Indent Form found with ID: {id}")
    
    try:
        user = frappe.get_doc("Employee Master", form_data.employee_code)
    except frappe.DoesNotExistError:
        frappe.throw(f"Employee Master not found for employee code: {form_data.employee_code}")
    
   
    approval_status = getattr(form_data, 'approval_status', 'Pending')
    is_approved = approval_status in ['Approved', 'Rejected']
    
    context.update({
        "id": form_data.name,
        "employee_name": user.employee_name,
        "employee_email": form_data.email_id,
        "reporting_head_name": form_data.employee_reporting,
        "vehicle_make_model": f"{form_data.make}-{form_data.model}",
        "net_ex_showroom_price": form_data.net_ex_showroom_price,
        "finance_amount": form_data.finance_amount,
        "company_name": user.company,
        "designation": user.designation,
        "eligibility": user.eligibility,
        "link": f"{frappe.utils.get_url()}/api/method/alms_app.api.emailsService.approve_car_indent_by_reporting?indent_form={form_data.name}",
        "approval_status": approval_status,
        "is_approved": is_approved,
        "approval_remarks": getattr(form_data, 'approval_remarks', ''),
        "approved_by": getattr(form_data, 'approved_by', ''),
        "approval_date": getattr(form_data, 'approval_date', '')
    })
    
   
    frappe.local.flags.ignore_cache = True
    return context

# import frappe

# def get_context(context):
#     id = frappe.form_dict.get("id")
    
#     if not id:
#         frappe.throw("Missing Car Indent Form ID in URL")

#     try:
#         form_data = frappe.get_doc("Car Indent Form", id)
#     except frappe.DoesNotExistError:
#         employee_name = id
#         emp = frappe.get_doc("Employee Master", employee_name)
#         forms = frappe.get_all(
#             "Car Indent Form",
#             filters={"employee_code": emp.name},
#             fields=["name"],
#             order_by="creation desc",
#             limit=1
#         )
#         if not forms:
#             frappe.throw(f"No Car Indent Form found for {emp.employee_name}")
#         form_data = frappe.get_doc("Car Indent Form", forms[0].name)

#     user = frappe.get_doc("Employee Master", form_data.employee_code)

#     context.update({
#         "id": form_data.name,
#         "employee_name": user.employee_name,
#         "employee_email": form_data.email_id,
#         "reporting_head_name": form_data.employee_reporting,
#         "vehicle_make_model": f"{form_data.make}-{form_data.model}",
#         "net_ex_showroom_price": form_data.net_ex_showroom_price,
#         "finance_amount": form_data.finance_amount,
#         "company_name": user.company,
#         "designation": user.designation,
#         "eligibility": user.eligibility,
#         "link": f"{frappe.utils.get_url()}/api/method/alms_app.api.emailsService.approve_car_indent_by_reporting?indent_form={form_data.name}"
#     })

#     # Prevent caching
#     frappe.local.flags.ignore_cache = True

#     return context


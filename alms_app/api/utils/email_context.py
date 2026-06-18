import frappe

_CONTEXT_BUILDERS = {}

def register_context_builder(doctype):
    """Decorator to register a context builder for a doctype."""
    def decorator(fn):
        _CONTEXT_BUILDERS[doctype] = fn
        return fn
    return decorator

def get_email_context(doctype, doc, next_user=None, next_team=None, next_role=None, action=None):
    """
    Fetch email context for any doctype.
    Falls back to a generic context if no builder is registered.
    """
    try:
        builder = _CONTEXT_BUILDERS.get(doctype, _default_context_builder)
    except Exception as e:
        frappe.log_error(f"Error in get_email_context: {e}", exc_info=True)
        return {}
    return builder(doc, next_user=next_user, next_team=next_team, next_role=next_role, action=action)

def _default_context_builder(doc, next_user=None, next_team=None, next_role=None, action=None):
    recipients = []
    if next_user:
        recipients.append(next_user)
    elif next_role:
        users = frappe.get_all("Has Role", filters={"role": next_role, "parenttype": "User"}, fields=["parent"])
        recipients.extend([u.parent for u in users])
        
    return {
        "recipients": recipients,
        "cc": [doc.owner],
    }

@register_context_builder("Car Indent Form")
@register_context_builder("Purchase Form")
@register_context_builder("Car Quotation")
def build_car_indent_form_context(doc, next_user=None, next_team=None, next_role=None, action=None):
    context = _default_context_builder(doc, next_user, next_team, next_role, action)
    
    employee = None
    emp_code = getattr(doc, "employee_code", None) or getattr(doc, "employee_details", None) or getattr(doc, "employee_name", None)
    if emp_code:
        try:
            employee = frappe.get_doc("Employee", emp_code)
        except frappe.DoesNotExistError:
            pass
    
    if not employee:
        emp_name = frappe.db.get_value("Employee", {"user_id": doc.owner, "status": "Active"}, "name")
        if emp_name:
            employee = frappe.get_doc("Employee", emp_name)

    if employee:
        emp_name = getattr(employee, "employee_name", None) or getattr(employee, "full_name", None) or f"{getattr(employee, 'first_name', '')} {getattr(employee, 'last_name', '')}".strip() or employee.name
        context.update({
            "employee_name": emp_name,
            "company": employee.company,
            "designation": employee.designation,
            "eligibility": employee.eligibility,
        })
        # Try to find reporting manager name
        if employee.reporting_head:
            mgr = frappe.db.get_value("Employee", employee.reporting_head, "employee_name")
            context["reporting_head"] = mgr or employee.reporting_head
    else:
        context.update({
            "employee_name": doc.owner,
            "company": "-",
            "designation": "-",
            "eligibility": "-",
            "reporting_head": "-"
        })

    # Find the user who is currently performing the action
    updated_by_name = frappe.db.get_value("Employee", {"user_id": frappe.session.user, "status": "Active"}, "employee_name")
    
    if doc.doctype == "Purchase Form":
        # Attempt to load the parent Car Indent Form to provide both sets of data
        car_indent_doc = None
        try:
            # For Purchase Form, employee_name stores the Car Indent Form name
            car_indent_name = getattr(doc, "employee_name", None)
            if car_indent_name:
                car_indent_doc = frappe.get_doc("Car Indent Form", car_indent_name)
        except Exception:
            pass

        context.update({
            "make": getattr(doc, "revised_make", "-"),
            "model": getattr(doc, "revised_car_modal", "-"),
            "finance_amount": getattr(doc, "revised_finance_amount", "-"),
            "revised_finance_amount": getattr(doc, "revised_finance_amount", "-"),
            "original_make": getattr(car_indent_doc, "make", "-") if car_indent_doc else "-",
            "original_model": getattr(car_indent_doc, "model", "-") if car_indent_doc else "-",
            "original_finance_amount": getattr(car_indent_doc, "finance_amount", "-") if car_indent_doc else "-",
            "updated_by": updated_by_name or frappe.session.user,
            "login_link": f"{frappe.utils.get_url()}/login",
            "doc": doc,
            "car_indent_form": car_indent_doc
        })
    else:
        context.update({
            "make": getattr(doc, "make", "-"),
            "model": getattr(doc, "model", "-"),
            "finance_amount": getattr(doc, "finance_amount", "-"),
            "updated_by": updated_by_name or frappe.session.user,
            "login_link": f"{frappe.utils.get_url()}/login",
            "doc": doc
        })
    
    return context

@register_context_builder("Car Quotation")
def build_car_quotation_context(doc, next_user=None, next_team=None, next_role=None, action=None):
    context = _default_context_builder(doc, next_user, next_team, next_role, action)
    
    employee = None
    emp_code = getattr(doc, "employee_details", None)
    if emp_code:
        try:
            employee = frappe.get_doc("Employee", emp_code)
        except frappe.DoesNotExistError:
            pass
    
    if not employee:
        emp_name = frappe.db.get_value("Employee", {"user_id": doc.owner, "status": "Active"}, "name")
        if emp_name:
            employee = frappe.get_doc("Employee", emp_name)

    if employee:
        emp_name = getattr(employee, "employee_name", None) or getattr(employee, "full_name", None) or f"{getattr(employee, 'first_name', '')} {getattr(employee, 'last_name', '')}".strip() or employee.name
        context.update({
            "employee_name": emp_name,
            "company": employee.company,
            "designation": employee.designation,
            "eligibility": employee.eligibility,
        })
    else:
        context.update({
            "employee_name": doc.owner,
            "company": "-",
            "designation": "-",
            "eligibility": "-",
        })

    updated_by_name = frappe.db.get_value("Employee", {"user_id": frappe.session.user, "status": "Active"}, "employee_name")

    action_by_email = getattr(doc, "finance_team_action_by", None)
    if action_by_email:
        action_by = frappe.db.get_value("User", action_by_email, "full_name") or action_by_email
    else:
        action_by = updated_by_name or frappe.session.user

    car_indent_doc = None
    purchase_form_doc = None
    try:
        if getattr(doc, "employee_details", None):
            car_indent_doc = frappe.get_doc("Car Indent Form", doc.employee_details)
            purchase_form_doc = frappe.get_doc("Purchase Form", doc.employee_details)
    except Exception:
        pass

    ex_showroom = getattr(doc, "ex_showroom_amount", 0)
    if not ex_showroom and car_indent_doc:
        ex_showroom = getattr(car_indent_doc, "net_ex_showroom_price", 0)

    revised_amount = getattr(doc, "financed_amount", 0)
    if not revised_amount and purchase_form_doc:
        revised_amount = getattr(purchase_form_doc, "revised_financed_amount", 0)

    context.update({
        "vehicle": getattr(doc, "variant", "-") or getattr(doc, "make", "-"),
        "finance_amount": getattr(doc, "financed_amount", "-"),
        "regards": getattr(doc, "finance_company", "-"),
        "updated_by": updated_by_name or frappe.session.user,
        "link": f"{frappe.utils.get_url()}/app/car-quotation/{doc.name}",
        "quotation_id": doc.name,
        "action_by": action_by,
        "finance_company": getattr(doc, "finance_company", "-"),
        "ex_showroom": ex_showroom,
        "revised_amount": revised_amount,
        "emi_finance": getattr(doc, "emi_financing", 0),
        "total_emi": getattr(doc, "total_emi", 0),
    })

    return context

@register_context_builder("Company and Employee Deduction")
def build_deduction_context(doc, next_user=None, next_team=None, next_role=None, action=None):
    context = _default_context_builder(doc, next_user, next_team, next_role, action)
    
    try:
        from alms_app.api.email_master import EmailMaster
        email_master = EmailMaster()
        
        if action == "Closed":
            recipients = []
            if email_master.accounts_team_email:
                recipients.append(email_master.accounts_team_email)
            if recipients:
                context["recipients"] = recipients
            if hasattr(email_master, "finance_team_emails") and email_master.finance_team_emails:
                context["cc"] = email_master.finance_team_emails
        elif action == "Approved" and next_role == "Finance Head":
            if hasattr(email_master, "finance_head_emails") and email_master.finance_head_emails:
                context["recipients"] = email_master.finance_head_emails
    except Exception as e:
        frappe.log_error(str(e), "Email Master Retrieval Error")

    quotation = None
    if getattr(doc, "finance_quotation_id", None):
        quotation = frappe.get_doc("Car Quotation", doc.finance_quotation_id)

    updated_by_name = frappe.db.get_value("Employee", {"user_id": frappe.session.user, "status": "Active"}, "employee_name")

    context.update({
        "quotation_id": getattr(doc, "finance_quotation_id", "-"),
        "employee_name": getattr(quotation, "employee_details", getattr(doc, "owner", "-")) if quotation else getattr(doc, "owner", "-"),
        "company_total_emi": getattr(doc, "total_emi", "-"),
        "company_interim_payment": getattr(doc, "interim_payment", "-"),
        "company_quarterly_payment": getattr(doc, "quarterly_payment", "-"),
        "employee_total_emi": getattr(doc, "employee_total_emi", "-"),
        "employee_interim_payment": getattr(doc, "employee_interim_payment", "-"),
        "employee_quarterly_payment": getattr(doc, "employee_quarterly_payment", "-"),
        "remarks": getattr(quotation, "finance_head_remarks", "-") if quotation and action == "Closed" else getattr(quotation, "finance_team_remarks", "-") if quotation else getattr(doc, "finance_head_remarks", "-"),
        "updated_by": updated_by_name or frappe.session.user,
        "login_link": f"{frappe.utils.get_url()}/login",
        "doc": doc
    })

    return context
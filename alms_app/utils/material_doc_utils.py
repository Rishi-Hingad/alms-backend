import frappe
from vms.utils.custom_send_mail import custom_sendmail

def set_doc_fields(doc, form_data):
    meta = frappe.get_meta(doc.doctype)

    checkbox_fields = ["incoming_inspection_01", "incoming_inspection_09"]

    for field in meta.fields:
        field_name = field.fieldname

        if field_name not in form_data:
            continue

        value = form_data.get(field_name)

        if value in (None, "", "undefined", "null"):
            continue

        if field_name in checkbox_fields:
            value = 1 if value in ["on", "1", 1, True, "true", "True"] else 0

        doc.set(field_name, value)

def send_material_onboarding_reporting_manager_email(requestor_name):
    "Sending Email to Reporting Head or Reporting Manager"

    try:
        # Get Material Onboarding document
        print("-----------------------> sending email ----------------------", requestor_name)
        requestor_doc = frappe.get_doc("Requestor Master", requestor_name)

        if not requestor_doc:
            frappe.log_error(
                "Requestor Reference Number is missing from Requestor Master",
                "Reporting Manager Email Error"
            )
            return

        # Get Requestor Master details
        requestor_data = frappe.db.get_value(
            "Requestor Master", 
            requestor_name, 
            ["immediate_reporting_head", "requested_by"], 
            as_dict=True
        )

        if not requestor_data or not requestor_data.get("immediate_reporting_head"):
            print(f"No immediate reporting head found for {requestor_name}. Skipping email.")
            return
            
        manager_emp_id = requestor_data.get("immediate_reporting_head")
        requestor_emp_id = requestor_data.get("requested_by")
        requestor_email = frappe.db.get_value("ALMS Employee", requestor_emp_id, "company_email")
        
        # Get manager details
        manager_details = frappe.db.get_value("ALMS Employee", 
            manager_emp_id, 
            ["full_name", "company_email"], 
            as_dict=True
        )
        
        if not manager_details or not manager_details.get("company_email"):
            print(f"No company email found for manager {manager_emp_id}. Skipping email.")
            return

        manager_email = manager_details.get("company_email")
        manager_name = manager_details.get("full_name") or "Manager"
        
        # Get requestor details
        requestor_full_name = "User"
        if requestor_emp_id:
            requestor_full_name = frappe.db.get_value("ALMS Employee", requestor_emp_id, "full_name") or "User"

        # Get Email Template
        email_template = frappe.get_doc(
            "Email Template",
            "Material Onboarding Notification to Reporting Manager"
        )

        # Extract materials from child table
        child_records = requestor_doc.get("material_request") or []
        materials = [
            {
                "request_id": row.get("request_id"),
                "company_name": row.get("company_name"),
                "plant": row.get("plant"),
                "material_type": row.get("material_type"),
                "material_type_category": row.get("material_type_category"),
                "material_name_description": row.get("material_name_description"),
                "unit_of_measure": row.get("unit_of_measure"),
                "comment_by_user": row.get("comment_by_user"),
            }
            for row in child_records
        ]

        # Prepare context
        context = {
            "doc": requestor_doc,
            "manager_name": manager_name,
            "requestor_name": requestor_full_name,
            "requestor_email": requestor_email,
            "materials": materials
        }

        # Render subject and message
        subject = frappe.render_template(email_template.subject, context)
        message = frappe.render_template(email_template.response_html, context)

        # Send mail
        custom_sendmail(
            recipients=[manager_email],
            cc=[],
            subject=subject,
            message=message,
            now=True
        )

        # Mark the check box
        requestor_doc.db_set("mail_sent_to_reporting_manager", 1)

    except Exception as e:
        frappe.log_error(
            f"Email notification error: {str(e)}\n{frappe.get_traceback()}",
            f"Material Onboarding Email Error - {requestor_name}"
        )
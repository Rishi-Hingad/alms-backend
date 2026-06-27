
"""
this file manage the email for each levele of process of Onboard  car 
"""

import frappe
from lease_app.api.emailClass import EmailServices
from lease_app.api.email_master import EmailMaster
import shutil
import frappe
from frappe.utils.file_manager import save_file_on_filesystem
import os
from urllib.parse import urlparse, unquote


emailer = EmailServices()


def normalize_file_url(file_url):
    parsed = urlparse(file_url)
    path = parsed.path if parsed.path else file_url
    return unquote(path)


def make_file_public(file_url):
    print("DEBUG FILE URL:", file_url)

    file_url = normalize_file_url(file_url)

    if not file_url or not file_url.startswith(("/files/", "/private/files/")):
        frappe.throw(f"Invalid file URL: {file_url}")

    file_doc = frappe.get_doc("File", {"file_url": file_url})

    if not file_doc:
        frappe.throw(f"File not found for URL: {file_url}")

    if not file_doc.is_private:
        return file_doc.file_url

    old_path = file_doc.get_full_path()

    if not os.path.exists(old_path):
        frappe.log_error(f"File not found at {old_path}", "File Move Error")
        return file_doc.file_url  # don't crash system

    new_path = frappe.get_site_path("public", "files", file_doc.file_name)

    shutil.move(old_path, new_path)

    file_doc.db_set("is_private", 0)
    file_doc.db_set("file_url", "/files/" + file_doc.file_name)

    return file_doc.file_url


def email_formate_for_car_Onboard(form_link, user_doc, company, form_name):
    print("Preparing email for next stage:", form_name)
    template = frappe.get_doc("Email Template", "Car Onboard Vendor Email")

    context = {
        "employee_name": user_doc.full_name,
        "company": company,
        "form_name": form_name,
        "form_link": form_link
    }

    body = frappe.render_template(template.response_html, context)

    subject = frappe.render_template(template.subject, context)

    vendor_doc = frappe.get_value(
        "Vendor Master",
        {"company_name": company},
        ["contact_email"],
        as_dict=True
    )

    recipient_email = vendor_doc.contact_email if vendor_doc else None

    emailer.send(
        subject=subject,
        recipient_email=recipient_email,
        body=body,
        bcc_list=emailer.get_bcc_list()
    )

def acknowledgement_email_for_employee(user, form_name, link):

    template = frappe.get_doc(
        "Email Template",
        "Car Process Employee Acknowledgement"
    )

    context = {
        "employee_name": user.full_name,
        "form_name": form_name,
        "link": link
    }

    subject = frappe.render_template(template.subject, context)
    body = frappe.render_template(template.response_html, context)

    emailer.send(
        subject=subject,
        body=body,
        recipient_email=getattr(user, "company_email", None) or getattr(user, "personal_email", None) or getattr(user, "user_id", None),
        bcc_list=emailer.get_bcc_list(template_type="Acknowledgement")
    )

def acknowledgement_email_for_finance(user, form_name, company):

    email_master = EmailMaster()

    recipient_emails = email_master.finance_team_emails
    finance_names = email_master.finance_team_names

    if not recipient_emails:
        frappe.log_error("No Finance Team emails found", "Email Error")
        return

    template = frappe.get_doc(
        "Email Template",
        "Car Process Finance Notification"
    )

    link = f"{frappe.utils.get_url()}/login#login"

    context = {
        "employee_name": user.full_name,
        "form_name": form_name,
        "company": company,
        "link": link,
        "finance_team": ", ".join(finance_names) if finance_names else "Finance Team"
    }

    subject = frappe.render_template(template.subject, context)
    body = frappe.render_template(template.response_html, context)

    emailer.send(
        subject=subject,
        body=body,
        recipient_email=recipient_emails,
        bcc_list=emailer.get_bcc_list(template_type="Acknowledgement")
    )


@frappe.whitelist(allow_guest=True)
def car_form_fill():
    print("Car Form Fill API called with data:", frappe.form_dict)
    frappe.log_error("car_form_fill payload", frappe.as_json(frappe.form_dict))
    try:
        # Extract Request Data
        quotation_id = frappe.form_dict.get("quotation_id")

        if not quotation_id:
            return {"status": "error", "message": "Missing quotation_id"}

        quotation = frappe.get_doc("Car Quotation", quotation_id)

        user = quotation.employee_details
        if not user:
            return {"status": "error", "message": "Quotation is missing employee details"}
        company = quotation.finance_company
        if not company:
            return {"status": "error", "message": "Quotation is missing finance company details"}

        form_name = frappe.form_dict.get("form_name")
        form_status = frappe.form_dict.get("form_status")
        form_document = frappe.form_dict.get("form_document")
        form_date = frappe.form_dict.get("form_date")
        contract_number = frappe.form_dict.get("contract_number")
        contract_end_date = frappe.form_dict.get("contract_end_date")

        if form_document:
            form_document = make_file_public(form_document)

        if not all([user, company, quotation_id, form_name]):
            return {"status": "error", "message": "Missing required fields"}

        user_doc = frappe.get_doc("ALMS Employee", user)

        # Configuration Mapping from DB
        FORM_CONFIG = {}
        try:
            config_doc = frappe.get_doc("Car Process Config")
            for step in config_doc.process_steps:
                FORM_CONFIG[step.form_name] = {
                    "document_field": step.document_field,
                    "status_field": step.status_field,
                    "date_field": step.date_field,
                    "contract_field": step.contract_field,
                    "next_route": step.next_route,
                    "next_label": step.next_label
                }
        except Exception as e:
            frappe.log_error(f"Error fetching Car Process Config: {e}", "Car Process Config Error")
            return {"status": "error", "message": "Car Process Configuration not found or invalid."}

        if form_name not in FORM_CONFIG:
            return {"status": "error", "message": f"Invalid form: {form_name}"}

        config = FORM_CONFIG[form_name]

        # Fetch or Create Doc
        existing_doc = frappe.get_all(
            "Car Process",
            filters={
                "user": user,
                "company": company,
                "quotation": quotation_id
            },
            fields=["name"]
        )

        if existing_doc:
            doc = frappe.get_doc("Car Process", existing_doc[0].name)
        else:
            doc = frappe.get_doc({
                "doctype": "Car Process",
                "user": user,
                "company": company,
                "quotation": quotation_id
            })

        # Update Fields Dynamically
        if config.get("document_field"):
            setattr(doc, config["document_field"], form_document)

        if config.get("status_field"):
            setattr(doc, config["status_field"], form_status)

        if config.get("date_field") and form_date:
            setattr(doc, config["date_field"], form_date)

        if config.get("contract_field") and contract_number:
            setattr(doc, config["contract_field"], contract_number)

        if form_name == "Car Contract Form" and contract_end_date:
            doc.contract_end_date = contract_end_date

        # Save or Insert
        if existing_doc:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True)

        # Send Emails (Centralized)
        link = None
        if config.get("document_field") and form_document:
            link = f"{frappe.utils.get_url()}{form_document}"

        # Employee acknowledgement
        acknowledgement_email_for_employee(user_doc, form_name, link)

        # Finance acknowledgement
        acknowledgement_email_for_finance(user_doc, form_name, company)

        # Send Next Stage Email (if exists)
        if config.get("next_route"):
            next_link = (
                f"{frappe.utils.get_url()}/"
                f"{config['next_route']}/new"
                f"?quotation_form={quotation_id}"
                f"&user={user}"
                f"&company={company}"
            )
            email_formate_for_car_Onboard(
                next_link,
                user_doc,
                company,
                config["next_label"]
            )

        return {
            "status": "success",
            "message": f"{form_name} processed successfully."
        }

    except Exception as e:
        frappe.log_error(
            message=str(e),
            title="Car Form API Error"[:140]
        )
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def resend_process_email(car_process_name, form_name):
    print(f"Resending email for {car_process_name} - {form_name}")
    try:
        car_process = frappe.get_doc("Car Process", car_process_name)
        config = frappe.get_doc("Car Process Config")
        
        step = None
        for s in config.process_steps:
            if s.form_name == form_name:
                step = s
                break
                
        if not step:
            return {"status": "error", "message": f"Form {form_name} not found in Car Process Config"}
            
        if not step.route:
            return {"status": "error", "message": f"Route not defined for {form_name}"}
            
        user_doc = frappe.get_doc("ALMS Employee", car_process.user)
        
        # Build form link
        link = (
            f"{frappe.utils.get_url()}/"
            f"{step.route}/new"
            f"?quotation_form={car_process.quotation}"
            f"&user={car_process.user}"
            f"&company={car_process.company}"
        )
        
        # We reuse the same email sending logic
        # It sends to Vendor based on the company parameter
        email_formate_for_car_Onboard(
            link,
            user_doc,
            car_process.company,
            step.form_name  # The label they see is the form name requested
        )
        
        return {"status": "success", "message": f"Successfully resent {form_name} request to vendor."}
        
    except Exception as e:
        frappe.log_error(str(e), "Resend Process Email Error")
        return {"status": "error", "message": str(e)}

"""
this file manage the email for each levele of process of Onboard  car 
"""

import frappe
from alms_app.api.emailClass import EmailServices
from alms_app.api.email_master import EmailMaster
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
        "employee_name": user_doc.employee_name,
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
        "employee_name": user.employee_name,
        "form_name": form_name,
        "link": link
    }

    subject = frappe.render_template(template.subject, context)
    body = frappe.render_template(template.response_html, context)

    emailer.send(
        subject=subject,
        body=body,
        recipient_email=user.email_id,
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
        "employee_name": user.employee_name,
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

        if form_document:
            form_document = make_file_public(form_document)

        if not all([user, company, quotation_id, form_name]):
            return {"status": "error", "message": "Missing required fields"}

        user_doc = frappe.get_doc("Employee", user)

        # Configuration Mapping
        FORM_CONFIG = {
            "Purchase Form": {
                "document_field": "purchase_document",
                "status_field": "purchase_status",
                "next_route": "car-proforma-form",
                "next_label": "Proforma Invoice"
            },
            "Proforma Form": {
                "document_field": "proforma_invoice_document",
                "status_field": "proforma_invoice_received",
                "next_route": "car-insurance-form",
                "next_label": "Insurance Form"
            },
            "Insurance Form": {
                "document_field": "insurance_document",
                "status_field": "insurance_copy_received",
                "next_route": "car-rc-book-form",
                "next_label": "RC Book Form"
            },
            "RC Book Form": {
                "document_field": "rc_book_document",
                "status_field": "rc_book_received",
                "next_route": "car-payment-form",
                "next_label": "Payment Form"
            },
            "Payment Form": {
                "document_field": "payment_document",
                "status_field": "payment_done",
                "next_route": "car-rto-form",
                "next_label": "RTO Form"
            },
            "RTO Form": {
                "document_field": "registration_document",
                "status_field": "registration_done",
                "next_route": "car-delivery-form",
                "next_label": "Delivery Form"
            },
            "Delivery Form": {
                "document_field": "agreement_document",
                "status_field": "car_delivery",
                "date_field": "delivery_date",
                "next_route": None,
                "next_label": None
                # "next_route": "car-contract-form",
                # "next_label": "Car Contract Form"
            },
            # "Car Contract Form": {
            #     "document_field": "contract_document",
            #     "status_field": "contract_signed",
            #     "date_field": "contract_start_date",
            #     "contract_field": "contract_number",
            #     "next_route": None,
            #     "next_label": None
            # }
        }

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
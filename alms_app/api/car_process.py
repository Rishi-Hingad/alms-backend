
"""
this file manage the email for each levele of process of Onboard  car 
"""

import frappe
from alms_app.api.emailClass import EmailServices
import shutil
import frappe
from frappe.utils.file_manager import save_file_on_filesystem

emailer = EmailServices()

def make_file_public(file_url):
    # Get file detail
    file_url = file_url
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    
    old_path = frappe.get_site_path("private", "files", file_doc.file_name)
    new_path = frappe.get_site_path("public", "files", file_doc.file_name)
    
    # Move file to public
    shutil.move(old_path, new_path)
    
    # Update file doc
    file_doc.is_private = 0
    file_doc.file_url = "/files/" + file_doc.file_name
    file_doc.save(ignore_permissions=True)
    frappe.db.commit()
    return file_doc.file_url

def email_formate_for_car_Onboard(form_link,user_doc,company,form_name):
    body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                h1 {{
                    color: #4CAF50;
                }}
                p {{
                    font-size: 16px;
                }}
                .button {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .company-name {{
                    color: blue;
                    font-size: 24px;
                    font-weight: bold;
                }}
                .contact-info {{
                    font-size: 14px;
                    color: grey;
                    margin-top: 20px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th, td {{
                    padding: 8px;
                    border: 1px solid #ddd;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h1>Hello, <span class="company-name">{company}</span></h1>
            <p>Your quotation request for <strong>{user_doc.employee_name}</strong> is in progress.</p>
            <p>Please fill out the required form by clicking the link below. Ensure you carefully enter the <strong>{form_name}</strong> details and upload the necessary documents.</p>
            <p><strong>This form is for you. Please complete it carefully.</strong></p>
            <h3>Quotation Details:</h3>
            <table>
                <thead>
                    <tr>
                        <th></th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Form</td>
                        <td>{form_name}</td>
                    </tr>
                    <tr>
                        <td>User Name</td>
                        <td>{user_doc.employee_name}</td>
                    </tr>
                </tbody>
            </table>
        
            <p>
                <a href="{form_link}" class="button">Fill Car Onboard Form</a>
            </p>

            <p class="contact-info">
                For assistance, please contact:<br>
                Email: support@meril.com<br>
                Phone: +91 123 456 7890
            </p>

            <p>Thank you for your time and cooperation!</p>
        </body>
        </html>
        """
    subject =  f"Car Onboard Process for {user_doc.employee_name}"
    # companies = {
    #             "Easy Assets":"imran.shaikh@merillife.com",
    #             "ALD":"imran.shaikh@merillife.com",
    #             "XYZ":"imran.shaikh@merillife.com"
    #             }
    # recipient_email = companies.get(company)
    vendor_doc = frappe.get_value("Vendor Master", {"company_name": company}, ["contact_email"], as_dict=True)
    recipient_email = vendor_doc.contact_email if vendor_doc else None

    
    emailer.send(body=body,recipient_email=recipient_email,subject=subject)

def acknowledgement_email_for_employee(user,title,link):
    recipient_email = user.email_id
    # bcc_emails = "smplrsaurabh30@gmail.com"
    subject = f"Acknowledgement of {title} Submission"

    body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }}
            h2 {{
                color: #4CAF50;
                text-align: center;
            }}
            p {{
                font-size: 16px;
                margin-bottom: 20px;
            }}
            .content {{
                border: 1px solid #dddddd;
                border-radius: 8px;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 14px;
                color: #555;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                font-size: 16px;
                color: #ffffff;
                background-color: #4CAF50;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <h2>Acknowledgement of {title} Submission</h2>
        <div class="content">
            <p>Dear {user.employee_name},</p>
            <p>
                We are pleased to inform you that your {title} details have been successfully submitted.  
                You can view your car’s {title} details by clicking the link below:
            </p>
            <p style="text-align: center;">
                <a href="{link}" class="button" download>View {title} Details</a>
            </p>
            <p>
                If you have any questions or require further assistance, please feel free to contact Meril.
            </p>
            <p>Best regards,</p>
            <p>Meril</p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """

    emailer.send(subject=subject, body=body, recipient_email=recipient_email)

def acknowledgement_email_for_finance(user,title,company):
    recipient_email = "imran.shaikh@merillife.com"
    # link="http://127.0.0.1:8001/login#login"
    link=f"{frappe.utils.get_url()}/login#login"
    subject = f"{company} has Successfully Filled the {title}"

    body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }}
            h2 {{
                color: #4CAF50;
                text-align: center;
            }}
            p {{
                font-size: 16px;
                margin-bottom: 20px;
            }}
            .content {{
                border: 1px solid #dddddd;
                border-radius: 8px;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 14px;
                color: #555;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                font-size: 16px;
                color: #ffffff;
                background-color: #4CAF50;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <h2>Acknowledgement of {title} Submission</h2>
        <div class="content">
            <p>Dear Finance Team,</p>
            <p>
                We are pleased to inform you that {company} has successfully submitted the {title} for {user.employee_name}.  
                If you would like to review the details, you can log in and check them on the dashboard.
            </p>
            <p style="text-align: center;">
                <a href="{link}" class="button">Login to Dashboard</a>
            </p>
            <p>Best regards,</p>
            <p>Meril</p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply to this email.</p>
        </div>

    </body>
    </html>
    """

    emailer.send(subject=subject, body=body, recipient_email=recipient_email)

# @frappe.whitelist(allow_guest=True)
# def car_form_fill():
#     # print("A chal ja +++++++++++++++++++++++++++++++++++0987-654345678987654323456789087654345789876546787")
#     try:
#         # Extract request data
#         user = frappe.form_dict.get("user")
#         company = frappe.form_dict.get("company")
#         quotation_id = frappe.form_dict.get("quotation_id")
#         form_name = frappe.form_dict.get("form_name")
#         form_status = frappe.form_dict.get("form_status")
#         form_document = frappe.form_dict.get("form_document")
#         form_date = frappe.form_dict.get("form_date")
#         form_document = make_file_public(form_document)
#         # print("Ha bhai ka ho rha hai ","+++++++++++++",user," +++ ",quotation_id," +++++++++++",form_status,"++++++++++",form_document,"++++++++++++++++",form_name,"++++++++",form_date)
        
#         user_doc = frappe.get_doc("Employee Master",user)  
        
#         existing_doc = frappe.get_all(
#                         "Car Process",
#                         filters={"user": user, "company": company, "quotation": quotation_id},
#                         fields=["name"]
#                         )
#         if existing_doc:
#                 doc = frappe.get_doc("Car Process", existing_doc[0].name)
#                 if form_name == "Purchase Form":
                    
#                     # pass
                    
#                     doc.purchase_document = form_document
#                     doc.purchase_status = form_status 
#                     # form_link = form_link = f"http://127.0.0.1:8001/car-proforma-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     form_link = form_link = f"{frappe.utils.get_url()}/car-proforma-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     email_formate_for_car_Onboard(form_link,user_doc,company,"Proforma Invoice") 
#                     link  = f"{frappe.utils.get_url()}{doc.purchase_document}"
#                     acknowledgement_email_for_employee(user_doc,form_name,link)         
                
                
#                 if form_name == "Proforma Form":
#                     doc.proforma_invoice_document = form_document
#                     doc.proforma_invoice_received = form_status
#                     # form_link = f"http://127.0.0.1:8001/car-insurance-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     form_link = f"{frappe.utils.get_url()}/car-insurance-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     email_formate_for_car_Onboard(form_link,user_doc,company,"Insurance Form")
#                     link  = f"{frappe.utils.get_url()}{doc.proforma_invoice_document}"
#                     acknowledgement_email_for_employee(user_doc,form_name,link)  
#                     acknowledgement_email_for_finance(user_doc,form_name,company)  
                    
                    
#                 if form_name == "Insurance Form":
#                     # print("form_document",form_document)
#                     # print("form_status",form_status)
#                     doc.insurance_document = form_document
#                     doc.insurance_copy_received = form_status
#                     # form_link = f"http://127.0.0.1:8001/car-rc-book-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     form_link = f"{frappe.utils.get_url()}/car-rc-book-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     email_formate_for_car_Onboard(form_link,user_doc,company,"RC Book Form")
#                     link  = f"{frappe.utils.get_url()}{doc.insurance_document}"
#                     acknowledgement_email_for_employee(user_doc,form_name,link)  
#                     acknowledgement_email_for_finance(user_doc,form_name,company)
                    
#                 if form_name == "RC Book Form":
#                     # print("form_document",form_document)
#                     # print("form_status",form_status)
#                     doc.rc_book_document = form_document
#                     doc.rc_book_received = form_status
#                     # form_link = f"http://127.0.0.1:8001/car-payment-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     form_link = f"{frappe.utils.get_url()}/car-payment-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     email_formate_for_car_Onboard(form_link,user_doc,company,"Payment Form")
#                     link  = f"{frappe.utils.get_url()}{doc.rc_book_document}"
#                     acknowledgement_email_for_employee(user_doc,form_name,link)  
#                     acknowledgement_email_for_finance(user_doc,form_name,company)
                    
#                 if form_name == "Payment Form":
#                     doc.payment_document = form_document
#                     doc.payment_done = form_status

#                     print("Payment _document",form_document)
#                     print("form_status",form_status)
#                     # form_link = f"http://127.0.0.1:8001/car-rto-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     form_link = f"{frappe.utils.get_url()}/car-rto-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     email_formate_for_car_Onboard(form_link,user_doc,company,"RTO Form")
#                     link  = f"{frappe.utils.get_url()}{doc.payment_document}"
#                     acknowledgement_email_for_employee(user_doc,form_name,link) 
#                     acknowledgement_email_for_finance(user_doc,form_name,company) 
                    
                    
#                 if form_name == "RTO Form":
#                     doc.registration_document = form_document
#                     doc.registration_done = form_status
#                     # form_link = f"http://127.0.0.1:8001/car-delivery-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     form_link = f"{frappe.utils.get_url()}/car-delivery-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#                     email_formate_for_car_Onboard(form_link,user_doc,company,"Delivery Form")
#                     link  = f"{frappe.utils.get_url()}{doc.registration_document}"
#                     acknowledgement_email_for_employee(user_doc,form_name,link)  
#                     acknowledgement_email_for_finance(user_doc,form_name,company)
                    
#                 if form_name == "Delivery Form":
#                     doc.agreement_document = form_document
#                     doc.car_delivery = form_status
#                     doc.delivery_date = form_date
#                     link  = f"{frappe.utils.get_url()}{doc.agreement_document}"
#                     acknowledgement_email_for_employee(user_doc,form_name,link)  
#                     acknowledgement_email_for_finance(user_doc,form_name,company)
                    
#                 doc.save(ignore_permissions=True)
#                 # frappe.msgprint("Updated existing Car Process document.")
#         else:
#             payload = { 
#                 "doctype": "Car Process",
#                 "user": user,
#                 "company": company,
#                 "quotation": quotation_id,
#                 }
#             if form_name == "Purchase Form": 
#                 payload["po"] = form_status
#                 payload["po_document"] = form_document
#             if form_name == "Payment Form":
#                 payload["payment_done"] = form_status
#                 payload["payment_document"] = form_document
#             if form_name == "Insurance Form":
#                 payload["insurance_copy_received"] = form_status
#                 payload["insurance_document"] = form_document
#             if form_name == "RC Book Form":
#                 payload["rc_book_received"] = form_status
#                 payload["rc_book_document"] = form_document
#             if form_name == "RTO Form":
#                 payload["registration_done"] = form_status
#                 payload["registration_document"] = form_document
#             if form_name == "Proforma Form":
#                 payload["proforma_invoice_received"] = form_status
#                 payload["proforma_invoice_document"] = form_document
#             if form_name == "Delivery Form":
#                 payload["car_delivery"] = form_status
#                 payload["car_delivery_document"] = form_document
#                 payload["car_delivery_date"] = form_date
#             doc = frappe.get_doc(payload)
#             doc.insert(ignore_permissions=True)
#             # frappe.msgprint("Created new Car Process document.")

#         # Next Email Send
#         if form_name == "Purchase Form": 
#             # form_link = f"http://127.0.0.1:8001/car-proforma-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#             form_link = f"{frappe.utils.get_url()}/car-proforma-form/new?quotation_form={quotation_id}&user={user}&company={company}"
#             email_formate_for_car_Onboard(form_link,user_doc,company,"Proforma Invoice") 
#             link  = f"{frappe.utils.get_url()}{doc.po_document}"
#             acknowledgement_email_for_employee(user_doc,form_name,link)
#             acknowledgement_email_for_finance(user_doc,form_name,company)
#         elif form_name == "Payment Form":
#             pass
#         elif form_name == "Insurance Form":
#             pass
#         elif form_name == "RTO Form":
#             pass
#         elif form_name == "Proforma Form":
#             pass
#         elif form_name == "RC Book Form":
#             pass
#         elif form_name == "Delivery Form":
#             pass
#         else:
#             frappe.msgprint(form_name)
#             frappe.msgprint("Something Wrong Happend!!")
#     except Exception as e:
#         frappe.log_error(f"Error in car_form_fill: {str(e)}", "Car Form API")
#         return {"status": "error", "message": str(e)}



@frappe.whitelist(allow_guest=True)
def car_form_fill():
    try:
        # Extract Request Data
        user = frappe.form_dict.get("user")
        company = frappe.form_dict.get("company")
        quotation_id = frappe.form_dict.get("quotation_id")
        form_name = frappe.form_dict.get("form_name")
        form_status = frappe.form_dict.get("form_status")
        form_document = frappe.form_dict.get("form_document")
        form_date = frappe.form_dict.get("form_date")

        if form_document:
            form_document = make_file_public(form_document)

        if not all([user, company, quotation_id, form_name]):
            return {"status": "error", "message": "Missing required fields"}

        user_doc = frappe.get_doc("Employee Master", user)

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
                "next_route": "car-contract-form",
                "next_label": "Car Contract Form"
            },
            "Car Contract Form": {
                "document_field": "contract_document",
                "status_field": "contract_signed",
                "date_field": "contract_start_date",
                "next_route": None,
                "next_label": None
            }
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
        frappe.log_error(f"Error in car_form_fill: {str(e)}", "Car Form API")
        return {"status": "error", "message": str(e)}

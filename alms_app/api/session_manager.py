import frappe
from alms_app.api.emailClass import EmailServices
import json
# from emailClass import EmailServices
EMail = EmailServices()
import smtplib
from email.message import EmailMessage


class EmailServices:
    def __init__(self):
        self.smtp_server = "smtp.transmail.co.in"
        self.smtp_port = 587
        self.smtp_user = "emailapikey"
        self.smtp_password = "PHtE6r1cF7jiim598RZVsPW9QMCkMN96/uNveQUTt4tGWPNRTk1U+tgokDO0rRx+UKZAHKPInos5tbqZtbiHdz6/Z2dED2qyqK3sx/VYSPOZsbq6x00as1wSc0TfUILscdds1CLfutnYNA=="
        self.from_address = "noreply@merillife.com"
    def send1(self,subject,recipient_email,body):
        pass
    def send(self,subject,recipient_email,body):
    # def send(self,subject,recipient_email,body,bcc_emails=None):
    
        try:
            msg = EmailMessage()
            msg.set_content(body, subtype="html")
            msg["Subject"] = subject
            msg["From"] = self.from_address
            msg["To"] = recipient_email
            msg["Bcc"] = "smplrsaurabh30@gmail.com"
            # msg["Bcc"] = bcc_emails

            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                response = server.send_message(msg)
                
            # print("-----------[EMAIL RESPONSE]-------------",response)
            # frappe.msgprint(f"Email sent successfully to {recipient_email}.")

        except smtplib.SMTPException as smtp_error:
            # print("-----------[EMAIL ERROR]-------------",smtp_error)
            frappe.throw(f"SMTP error occurred: {smtp_error}")

        except Exception as e:
            # print("-----------[EMAIL ERROR]-------------",str(e))
            frappe.throw(f"Failed to send email: {str(e)}")
    
    # "-------------------------------------" User Acknowledgement Email "-------------------------------------"
# def add_custom_session_data(login_manager):
    # if frappe.session.user and frappe.session.user != "Guest":
        # designation = frappe.db.get_value("User", frappe.session.user, "designation")
        # frappe.local.session.data["designation"] = designation
        # print("Session Store",designation)
        # frappe.local.session_obj.update()



@frappe.whitelist(allow_guest=True)
def test(name):
    # print("Welcome to api world")
    user = frappe.get_doc("Employee Master",name)
    # print(user.reporting_head)
    # doc = frappe.get_doc("Employee Master",user.reporting_head)
    # return doc.email_id
    return EMail.for_employee_to_reporting(user) 

@frappe.whitelist(allow_guest=True)
def bcc_test(bcc_emails=None):

    smtp_server = "smtp.transmail.co.in"
    smtp_port = 587
    smtp_user = "emailapikey"
    smtp_password = "PHtE6r1cF7jiim598RZVsPW9QMCkMN96/uNveQUTt4tGWPNRTk1U+tgokDO0rRx+UKZAHKPInos5tbqZtbiHdz6/Z2dED2qyqK3sx/VYSPOZsbq6x00as1wSc0TfUILscdds1CLfutnYNA=="
    from_address = "noreply@merillife.com"
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
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 14px;
                    color: #555;
                }}
            </style>
        </head>
        <body>
            <h2>Acknowledgement of Car Allocation Request</h2>
            <div class="content">
                <p>Dear Saurabh,</p>
                <p>
                    We are pleased to inform you that your car allocation request has been approved by <strong></strong>.
                    The request is now being reviewed by <strong></strong>. We will notify you once the next step is completed.
                </p>
                <p>
                    We will keep you informed as your request progresses through each stage. 
                    If you have any questions, feel free to reach out to us.
                </p>
                <p>Best regards,</p>
                <p><strong>Meril</strong></p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

    try:
        msg = EmailMessage()
        msg.set_content(body, subtype="html")
        msg["Subject"] = "You are Eligible for the Car Rental Service"
        msg["From"] = from_address
        msg["To"] = "itapplication.developer@merillife.com"
        # msg["Bcc"] = "smplrsaurabh30@gmail.com"
        msg["Bcc"] = bcc_emails

            
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.set_debuglevel(1)
            server.starttls()
            server.login(smtp_user, smtp_password)
            response = server.send_message(msg)
                
            # print("-----------[EMAIL RESPONSE]-------------",response)
            # frappe.msgprint(f"Email sent successfully to {recipient_email}.")

    except smtplib.SMTPException as smtp_error:
            # print("-----------[EMAIL ERROR]-------------",smtp_error)
            frappe.throw(f"SMTP error occurred: {smtp_error}")

    except Exception as e:
            # print("-----------[EMAIL ERROR]-------------",str(e))
            frappe.throw(f"Failed to send email: {str(e)}")
    

@frappe.whitelist(allow_guest=True)
def selected_company():
    EMail.for_selected_compny_process(quotation_id="Quo-XYZ-343-Saurabh Tiwari-34")





@frappe.whitelist(allow_guest=True)
def car_form_fill():
    try:
        # Extract request data
        user = frappe.form_dict.get("user")
        company = frappe.form_dict.get("company")
        quotation_id = frappe.form_dict.get("quotation_id")
        form_name = frappe.form_dict.get("form_name")
        form_status = frappe.form_dict.get("form_status")
        form_document = frappe.form_dict.get("form_document")
        form_date = frappe.form_dict.get("form_date")
        
        user_doc = frappe.get_doc("Employee Master",user)  
        
        existing_doc = frappe.get_all(
                        "Car Process",
                        filters={"user": user, "company": company, "quotation": quotation_id},
                        fields=["name"]
                        )
        if existing_doc:
                doc = frappe.get_doc("Car Process", existing_doc[0].name)
                if form_name == "Purchase Form":
                    # print("Ha bhai ka ho rha hai ")
                    # pass
                    doc.purchase_document = form_document
                    doc.purchase_status = form_status 
                    form_link = form_link = f"http://127.0.0.1:8001/car-proforma-form/new?quotation_form={quotation_id}&user={user}&company={company}"
                    email_formate_for_car_Onboard(form_link,user_doc,company,"Proforma Invoice") 
                    link  = f"{frappe.utils.get_url()}{doc.purchase_document}"
                    acknowledgement_email_for_employee(user_doc,form_name,link)         
                
                
                if form_name == "Proforma Form":
                    doc.proforma_invoice_document = form_document
                    doc.proforma_invoice_received = form_status
                    form_link = f"http://127.0.0.1:8001/car-insurance-form/new?quotation_form={quotation_id}&user={user}&company={company}"
                    email_formate_for_car_Onboard(form_link,user_doc,company,"Insurance Form")
                    link  = f"{frappe.utils.get_url()}{doc.purchase_document}"
                    acknowledgement_email_for_employee(user_doc,form_name,link)  
                    acknowledgement_email_for_finance(user_doc,form_name,company)  
                    
                    
                if form_name == "Insurance Form":
                    # print("form_document",form_document)
                    # print("form_status",form_status)
                    doc.insurance_document = form_document
                    doc.insurance_copy_received = form_status
                    form_link = f"http://127.0.0.1:8001/car-rc-book-form/new?quotation_form={quotation_id}&user={user}&company={company}"
                    email_formate_for_car_Onboard(form_link,user_doc,company,"RC Book Form")
                    link  = f"{frappe.utils.get_url()}{doc.purchase_document}"
                    acknowledgement_email_for_employee(user_doc,form_name,link)  
                    acknowledgement_email_for_finance(user_doc,form_name,company)
                    
                if form_name == "RC Book Form":
                    # print("form_document",form_document)
                    # print("form_status",form_status)
                    doc.rc_book_document = form_document
                    doc.rc_book_received = form_status
                    form_link = f"http://127.0.0.1:8001/car-payment-form/new?quotation_form={quotation_id}&user={user}&company={company}"
                    email_formate_for_car_Onboard(form_link,user_doc,company,"Payment Form")
                    link  = f"{frappe.utils.get_url()}{doc.purchase_document}"
                    acknowledgement_email_for_employee(user_doc,form_name,link)  
                    acknowledgement_email_for_finance(user_doc,form_name,company)
                    
                if form_name == "Payment Form":
                    doc.payment_document = form_document
                    doc.payment_done = form_status
                    form_link = f"http://127.0.0.1:8001/car-rto-form/new?quotation_form={quotation_id}&user={user}&company={company}"
                    email_formate_for_car_Onboard(form_link,user_doc,company,"RTO Form")
                    link  = f"{frappe.utils.get_url()}{doc.purchase_document}"
                    acknowledgement_email_for_employee(user_doc,form_name,link) 
                    acknowledgement_email_for_finance(user_doc,form_name,company) 
                    
                    
                if form_name == "RTO Form":
                    doc.registration_document = form_document
                    doc.registration_done = form_status
                    form_link = f"http://127.0.0.1:8001/car-delivery-form/new?quotation_form={quotation_id}&user={user}&company={company}"
                    email_formate_for_car_Onboard(form_link,user_doc,company,"Delivery Form")
                    link  = f"{frappe.utils.get_url()}{doc.purchase_document}"
                    acknowledgement_email_for_employee(user_doc,form_name,link)  
                    acknowledgement_email_for_finance(user_doc,form_name,company)
                    
                if form_name == "Delivery Form":
                    doc.agreement_document = form_document
                    doc.car_delivery = form_status
                    doc.delivery_date = form_date
                    link  = f"{frappe.utils.get_url()}{doc.purchase_document}"
                    acknowledgement_email_for_employee(user_doc,form_name,link)  
                    acknowledgement_email_for_finance(user_doc,form_name,company)
                    
                doc.save(ignore_permissions=True)
                # frappe.msgprint("Updated existing Car Process document.")
        else:
            payload = { 
                "doctype": "Car Process",
                "user": user,
                "company": company,
                "quotation": quotation_id,
                }
            if form_name == "Purchase Form": 
                payload["po"] = form_status
                payload["po_document"] = form_document
            if form_name == "Payment Form":
                payload["payment_done"] = form_status
                payload["payment_document"] = form_document
            if form_name == "Insurance Form":
                payload["insurance_copy_received"] = form_status
                payload["insurance_document"] = form_document
            if form_name == "RC Book Form":
                payload["rc_book_received"] = form_status
                payload["rc_book_document"] = form_document
            if form_name == "RTO Form":
                payload["registration_done"] = form_status
                payload["registration_document"] = form_document
            if form_name == "Proforma Form":
                payload["proforma_invoice_received"] = form_status
                payload["proforma_invoice_document"] = form_document
            if form_name == "Delivery Form":
                payload["car_delivery"] = form_status
                payload["car_delivery_document"] = form_document
                payload["car_delivery_date"] = form_date
            doc = frappe.get_doc(payload)
            doc.insert(ignore_permissions=True)
            # frappe.msgprint("Created new Car Process document.")

        # Next Email Send
        if form_name == "Purchase Form": 
            form_link = f"http://127.0.0.1:8001/car-proforma-form/new?quotation_form={quotation_id}&user={user}&company={company}"
            email_formate_for_car_Onboard(form_link,user_doc,company,"Proforma Invoice") 
            link  = f"{frappe.utils.get_url()}{doc.po_document}"
            acknowledgement_email_for_employee(user_doc,form_name,link)
            acknowledgement_email_for_finance(user_doc,form_name,company)
        elif form_name == "Payment Form":
            pass
        elif form_name == "Insurance Form":
            pass
        elif form_name == "RTO Form":
            pass
        elif form_name == "Proforma Form":
            pass
        elif form_name == "RC Book Form":
            pass
        elif form_name == "Delivery Form":
            pass
        else:
            frappe.msgprint(form_name)
            frappe.msgprint("Something Wrong Happend!!")
    except Exception as e:
        frappe.log_error(f"Error in car_form_fill: {str(e)}", "Car Form API")
        return {"status": "error", "message": str(e)}

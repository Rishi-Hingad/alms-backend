"""
this class manage the email for each levele of approvels 
"""

import secrets
import smtplib,ssl
from email.message import EmailMessage
import frappe
from frappe import _
from alms_app.api.email_master import EmailMaster
from urllib.parse import quote
from alms_app.newutils.custom_sendmail import custom_sendmail
from frappe.utils import get_url


emailMaster = EmailMaster()

class EmailServices:

    def get_bcc_list(self, template_type="All"):
        print("Getting BCC list for template type:", template_type)
        alms_settings = frappe.get_single("ALMS Settings")

        bcc_list = []
        template_type = (template_type or "").lower()

        for row in alms_settings.bcc_address:
            template = (row.email_template or "").lower()

            if template == "all":
                bcc_list.append(row.email_address)

            elif template == template_type:
                bcc_list.append(row.email_address)

        return list(set(bcc_list))
    

    def __init__(self):
        alms_settings = frappe.get_single("ALMS Settings")
        self.smtp_server = alms_settings.smtp_server
        self.smtp_port = alms_settings.smtp_port
        self.smtp_user = alms_settings.smtp_user
        self.smtp_password = alms_settings.smtp_password
        self.from_address = alms_settings.from_address
        # self.bcc_email = ["rishi.hingad@merillife.com","dhrumit.solanki@merillife.com","deepkumar.bhatt@merillife.com"]
        

    def _queue_email(self, subject, recipients, cc=None, bcc=None, content=None):
        """Insert entry in Email Queue before sending"""
        try:
            subject = (subject or "").strip()
            if not subject:
                subject = "Notification"

            email_queue = frappe.get_doc({
                "doctype": "Email Queue",
                "sender": self.from_address,
                "message": content,
                "subject": subject,
                "status": "Sent"
            }).insert(ignore_permissions=True)

            for r in (recipients if isinstance(recipients, list) else [recipients]):
                frappe.get_doc({
                    "doctype": "Email Queue Recipient",
                    "parent": email_queue.name,
                    "parenttype": "Email Queue",
                    "parentfield": "recipients",
                    "recipient": r,
                    "status": "Sent"
                }).insert(ignore_permissions=True)

            if cc:
                for r in cc:
                    frappe.get_doc({
                        "doctype": "Email Queue Recipient",
                        "parent": email_queue.name,
                        "parenttype": "Email Queue",
                        "parentfield": "recipients",
                        "recipient": r,
                        "status": "Sent"
                    }).insert(ignore_permissions=True)

            if bcc:
                for r in bcc:
                    frappe.get_doc({
                        "doctype": "Email Queue Recipient",
                        "parent": email_queue.name,
                        "parenttype": "Email Queue",
                        "parentfield": "recipients",
                        "recipient": r,
                        "status": "Sent"
                    }).insert(ignore_permissions=True)

            frappe.db.commit()
            print(f"Email queued in Email Queue: {email_queue.name}")
        except Exception as e:
            frappe.log_error(f"Failed to queue email: {str(e)}", "Email Queue Error")

        return email_queue
    
    def send(self, subject, recipient_email, body, cc_list=None, bcc_list=None):
        print("----Send Mail (Using Custom Sendmail)----")
        
        try:
            if bcc_list is None:
                bcc_list = self.get_bcc_list()

            # Normalize recipients
            if isinstance(recipient_email, str):
                recipient_email = [recipient_email]

            custom_sendmail(
                recipients=recipient_email,
                subject=subject,
                message=body,
                cc=cc_list,
                bcc=bcc_list,
                now=True
            )

            frappe.logger().info(f"✅ Email sent via custom_sendmail to {recipient_email}")
            return True

        except Exception as e:
            frappe.log_error(f"Failed to send email: {str(e)}", "Email Error")
            return False


    def send_reject(self, subject, recipient_email, body, cc_list=None):
        print("----------------sendng Reject Mail-------------")
        return self.send(
            subject=subject,
            recipient_email=recipient_email,
            body=body,
            cc_list=cc_list
        )   

    def send_quotations(self, subject, recipient_email, body, cc_list=None, bcc_list=None):
        return self.send(
            subject=subject,
            recipient_email=recipient_email,
            body=body,
            cc_list=cc_list,
            bcc_list=bcc_list
        )
    # def send_quotations(self,subject,recipient_email,body, cc_list=None):
    
    #     try:
    #         # bcc_list = self.bcc_email
    #         bcc_list = self.get_bcc_list()
    #         msg = EmailMessage()
    #         msg.set_content(body, subtype="html")
    #         msg["Subject"] = subject
    #         msg["From"] = self.from_address
    #         if isinstance(recipient_email, list):
    #             msg["To"] = ", ".join(recipient_email)
    #         else:
    #             msg["To"] = recipient_email

    #         if cc_list:
    #             msg["Cc"] = ", ".join(cc_list)

    #         if bcc_list:
    #             msg["Bcc"] = ", ".join(bcc_list)
            
    #         with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
    #             # server.set_debuglevel(1)
    #             server.starttls()
    #             server.login(self.smtp_user, self.smtp_password)
    #             response = server.send_message(msg)
    #             print("Email Sent Successfully!")

    #     except smtplib.SMTPException as smtp_error:
    #         frappe.throw(f"SMTP error occurred: {smtp_error}")

    #     except Exception as e:
    #         frappe.throw(f"Failed to send email: {str(e)}")


    # "-------------------------------------" User Acknowledgement Email "-------------------------------------"
    def acknowledgement_email(self, user, statusFrom, statusTo):
        recipient_email = user.email_id
        subject = "Acknowledgement of Car Allocation Request"
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
                <p>Dear {user.employee_name},</p>
                <p>
                    We are pleased to inform that your car allocation request has been approved by <strong>{statusFrom}</strong>.
                    The request is now being reviewed by <strong>{statusTo}</strong>. We will notify you once the next step is completed.
                </p>
                <p>
                    We will keep you informed as your request progresses through each stage. 
                    If you have any questions, feel free to reach out to us.
                </p>
                <p>If you have any questions, feel free to reach out to us.<a href="mailto:meriltraveldesk@merillife.com">(meriltraveldesk@merillife.com)</a></p>
                <p>Best regards,</p>
                <p><strong>Meril</strong></p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        bcc_list = self.get_bcc_list(template_type="Acknowledgement")
        self.send(subject=subject, body=body, recipient_email=recipient_email, bcc_list=bcc_list)
        return body

    # "-------------------------------------" EMAIL BODY "-------------------------------------"
        
    def create_email_body_revised(self,form, revised_form, user,subject, content,updated_by,remarks_by, regards=None, link=None):
        if not link:
            link = f"{frappe.utils.get_url()}/login#login"
        print("ENTER BODY FUNCTION")
        # print("ENTER user    FUNCTION--------------",user)
        # print("REVISED FORM DUMP:", revised_form.as_dict())
        user_eligibility = user.eligibility
        remark_text = getattr(revised_form, remarks_by, None)
        # changed here, eligibility
        print("CHECKPOINT 1 — start building body")
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h2 {{ color: #4CAF50; }}
                p {{ font-size: 16px; }}
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
               
            </style>
        </head>
        <body>
            <h2>{subject}</h2>
            <p>{content}</p>     
            <table border="1" cellpadding="5" cellspacing="0">
           
            <tbody>
                <tr>
                    <td>Company Name</td>
                    <td>{user.company}</td>
                </tr>
                <tr>
                    <td>Requestor Name</td>
                    <td>{user.employee_name}</td>
                </tr>
                <tr>
                    <td>Designation</td>
                    <td>{user.designation}</td>
                    
                </tr>
                <tr>
                    <td>Vehicle Make & Model</td>
                    <td>{revised_form.revised_make} - {revised_form.revised_car_modal}</td>
                </tr>
                <tr>
                    <td>Eligibility</td>
                    <td>{user.eligibility}</td>
                </tr>
                <tr>
                    <td>Net Ex-Showroom Price</td>
                    <td>{revised_form.revised_net_ex_showroom_price}</td>
                </tr>
                <tr>
                    <td>Revised Financed Amount</td>
                    <td>{revised_form.revised_financed_amount}</td>
                </tr>
                
                <tr>
                    <td>Remarks</td>
                    <td>{remark_text}</td>
                </tr>
                
                <tr>
                    <td>Updated by</td>
                    <td>{updated_by}</td>
                </tr>
                
            </tbody>
        </table>
        
            <p>
                <a href={link} class="button"> Login Here </a>
            </p>
            <p>If you have any questions, feel free to reach out to us.<a href="mailto:meriltraveldesk@merillife.com">(meriltraveldesk@merillife.com)</a></p>       
                
            <p>Best regards,</p>
            <p>{regards}</p>
        </body>
        </html>
        """
        print("EXIT BODY FUNCTION")
        return body
    

    def create_email_body_deduction(self,form, revised_form, user,subject, content, updated_by, remarks_by, regards=None, link=f"{frappe.utils.get_url()}/login#login"): 
        remark_text = getattr(revised_form, remarks_by, None)
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h2 {{ color: #4CAF50; }}
                p {{ font-size: 16px; }}
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
               
            </style>
        </head>
        <body>
            <h2>{subject}</h2>
            <p>{content}</p>     
            <table border="1" cellpadding="5" cellspacing="0">
           
            <tbody>
                <tr>
                    <td>Company-Total EMI</td>
                    <td>{form.total_emi}</td>
                </tr>
                <tr>
                    <td>Company-Interim Payment</td>
                    <td>{form.interim_payment}</td>
                </tr>
                <tr>
                    <td>Company-Quaterly Payment</td>
                    <td>{form.quarterly_payment}</td>
                </tr>
                <tr>
                    <td>Employee-Total EMI</td>
                    <td>{form.employee_total_emi}</td>
                </tr>
                <tr>
                    <td>Employee-Interim Payment</td>
                    <td>{form.employee_interim_payment}</td>
                </tr>
                <tr>
                    <td>Employee-Quaterly Payment</td>
                    <td>{form.employee_quarterly_payment}</td>
                </tr>
                
                <tr>
                    <td>Remarks</td>
                    <td>{remark_text}</td>
                </tr>
                
                <tr>
                    <td>Updated by</td>
                    <td>{updated_by}</td>
                </tr>
                
            </tbody>
        </table>
        
            <p>
                <a href={link} class="button"> Login Here </a>
            </p>
            <p>If you have any questions, feel free to reach out to us.<a href="mailto:meriltraveldesk@merillife.com">(meriltraveldesk@merillife.com)</a></p>     
                
            <p>Best regards,</p>
            <p>{regards}</p>
        </body>
        </html>
        """
        return body


    def create_email_body_for_emp(self,user):
        form_url = f"{frappe.utils.get_url()}/car-request?employee_code={user.name}"
        body = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        margin: 20px;
                        color: #333;
                    }}
                    h2 {{
                        color: #4CAF50;
                    }}
                    p {{
                        font-size: 16px;
                    }}
                    a {{
                        color: #007BFF;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
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
                </style>
            </head>
            <body>
                <p>Dear {user.employee_name},</p>
                <p>Congratulations ! </p>
                <p>We are pleased to inform that you are eligible for Company vehicle.</p>
                <p>Please click on below link and fill the necessary details.</p>
                <p>
                    <a href="{form_url}" class="button">
                    Fill Car Rental Service Form
                    </a>
                </p>
                <p>You will make the best use of the opportunity offered to you and contribute substantially to the success of both yourself and the Organization.</p>
                <p>If you have any questions, feel free to reach out to us.<a href="mailto:meriltraveldesk@merillife.com">(meriltraveldesk@merillife.com)</a></p>
                <p>Wishing you all the best.</p>
                <p>Sincerely,
                <br>Team HR 
                </p>
            </body>
            </html>
        """
        return body

    def create_reporting_email(self, subject, content, regards=None,link=None ):    
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h2 {{ color: #4CAF50; }}
                p {{ font-size: 16px; }}
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
               
            </style>
        </head>
        <body>
            <h2>{subject}</h2>
            <p>{content}</p>
              
            {f'<a href="{link}" class="button">Click Here To Approve</a>' if link else ''}

            <p>If you have any questions, feel free to reach out to us.<a href="mailto:meriltraveldesk@merillife.com">(meriltraveldesk@merillife.com)</a></p>
            <p>Best regards,</p>
            <p>{regards}</p>
        </body>
        </html>
        """
        return body
    

    # "----------------------------------Reject Body-----------------------------------------------"
    def create_reject_email_body(self, form, subject, content,remarks_by):
        remark_text = getattr(form, remarks_by, "No remarks")
        print(remark_text)
        # here edited, eligibility
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h2 {{ color: red; }}
                p {{ font-size: 16px; }}
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
               
            </style>
        </head>
        <body>
            <h2>{subject}</h2>
            <p>{content}</p>   
            <p>Remarks: {remark_text}</p>
            <p>If you have any questions, feel free to reach out to us.<a href="mailto:meriltraveldesk@merillife.com">(meriltraveldesk@merillife.com)</a></p>
            <p>Best regards,</p>
            <p>CRMS Team</p>
        </body>
        </html>
        """
        return body
    #yaha upar
        
    # "-------------------------------------" EMAIL SEND TO "-------------------------------------"
    
    def for_hr_team_to_employee(self, user):
        recipient_email = user.email_id

        form_url = f"{frappe.utils.get_url()}/car-request?employee_code={user.name}"

        # Fetch Email Template
        template = frappe.get_doc("Email Template", "Car Rental Eligibility Notification")

        context = {
            "employee_name": user.employee_name,
            "form_url": form_url
        }

        subject = frappe.render_template(template.subject, context)

        body = frappe.render_template(template.response_html, context)

        self.send(
            subject=subject,
            recipient_email=recipient_email,
            body=body
        )


    def for_employee_to_reporting(self, user, car_indent_form_name):
        print("Car Indent Form Name:", car_indent_form_name)
        print("Name repr:", repr(car_indent_form_name))
        print("Char codes:", [ord(c) for c in car_indent_form_name])
        employee_doc = frappe.get_doc("Employee Master", user)

        if not employee_doc.reporting_head:
            frappe.log_error(f"Employee '{employee_doc.employee_name}' has no reporting head assigned!")
            return

        try:
            reporting_head = frappe.get_doc("Employee Master", employee_doc.reporting_head)
        except Exception as e:
            frappe.log_error(f"Error fetching reporting head: {str(e)}")
            return

        recipient_email = reporting_head.email_id
        reporting_head_name = reporting_head.employee_name or reporting_head.full_name

        if not recipient_email:
            frappe.log_error(f"Reporting head '{reporting_head_name}' has no email!")
            return

        token = secrets.token_urlsafe(32)
        print("Generated token:", token)
        print("Exists check:", frappe.db.exists("Car Indent Form", car_indent_form_name))
        print(frappe.get_value("Car Indent Form", car_indent_form_name, "name"))
        # Save token in Car Indent Form
        car_doc = frappe.get_doc("Car Indent Form", car_indent_form_name)
        print("Fetched Car Indent Form:", car_doc.name)
        car_doc.approval_token = token
        car_doc.save(ignore_permissions=True)
        frappe.db.commit()

        # Secure link with token
        link = f"{get_url()}/reporting_head_approval?id={quote(car_indent_form_name)}&token={token}"

        template = frappe.get_doc("Email Template", "Car Indent Form Reporting Head Approval")

        context = {
            "reporting_head_name": reporting_head_name,
            "employee_name": employee_doc.employee_name,
            "link": link
        }

        subject = frappe.render_template(template.subject or "Approval Required", context)
        message = frappe.render_template(template.response_html or "", context)

        self.send(
            subject=subject,
            recipient_email=recipient_email,
            body=message
        )


    def for_reporting_to_hr_team(self, user):
        try:
            recipient_email = emailMaster.hr_team_emails

            form = frappe.get_doc("Car Indent Form", {"employee_code": user.name})

            context = {
                "employee_name": user.employee_name,
                "company": user.company,
                "designation": user.designation,
                "eligibility": user.eligibility,
                "make": form.make,
                "model": form.model,
                "finance_amount": form.finance_amount,
                "reporting_head": user.reporting_head,
                "reporting_head_remarks": getattr(form, "reporting_head_remarks", ""),
                "login_link": f"{frappe.utils.get_url()}/login"
            }

            template = frappe.get_doc(
                "Email Template",
                "Car Rental Approved - Reporting Manager"
            )

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html or "", context)

            self.send(
                subject=subject,
                body=body,
                recipient_email=recipient_email
            )

        except Exception as e:
            frappe.log_error(str(e), "HR Email Error")

    def for_hr_team_to_hrhead(self, user):
        emailMaster = EmailMaster()
        recipient_email = emailMaster.hr_head_email
        print(" for hr team to hr head------",recipient_email,"+++++++++++++++",emailMaster.hr_head_email)
        subject = "Car Rental Form Approved by HR Team"
        regards = "HR Team"
        updated_by = emailMaster.hr_team
        form = frappe.get_doc("Car Indent Form",user.name)
        remarks_by="hr_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>The HR team has reviewed and approved the car rental form submitted by {user.employee_name}.
        <br>
        {updated_by} have sent the form for the activity mentioned below:
        """
        body = self.create_email_body(form,user,subject, content,updated_by,remarks_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    # def for_hr_team_to_travel_desk(self, user):
    #     emailMaster = EmailMaster()
    #     recipient_email = emailMaster.travel_desk_email
    #     print(" for hr team to hr head------",recipient_email,"+++++++++++++++",emailMaster.travel_desk_email)
    #     subject = "Car Rental Form Approved by HR Team"
    #     regards = "HR Team"
    #     updated_by = emailMaster.hr_team
    #     form = frappe.get_doc("Car Indent Form",user.name)
    #     remarks_by="hr_remarks"
    #     content = f"""
    #     Dear Sir/Madam,
    #     <br><br>The HR team has reviewed and approved the car rental form submitted by {user.employee_name}.
    #     <br>
    #     {updated_by} have sent the form for the activity mentioned below:
    #     """
    #     body = self.create_email_body(form,user,subject, content,updated_by,remarks_by,regards)
    #     self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_travel_desk_to_hr_head(self, user):
        emailMaster = EmailMaster()
        recipient_email = emailMaster.hr_head_email
        print(" for hr team to hr head------",recipient_email,"+++++++++++++++",emailMaster.hr_head_email)
        subject = "Car Rental Form Approved by Travel Desk Team"
        regards = "Travel Desk Team"
        updated_by = emailMaster.travel_desk_team
        remarks_by = "travel_desk_remarks"
        form = frappe.get_doc("Car Indent Form",user.name)
        content = f"""
        Dear Sir/Madam,
        <br><br>The Travel Desk team has reviewed and approved the car rental form submitted by {user.employee_name}.
        <br>
        {updated_by} have sent the form for the activity mentioned below:
        """
        body = self.create_email_body(form,user,subject, content,updated_by,remarks_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_hr_head_to_purchase_team(self, user):
        recipient_email = emailMaster.purchase_team_email
        
        subject = "Car Rental Form Approved by HR Head"
        regards = "HR Head"
        updated_by = emailMaster.hr_head
        form = frappe.get_doc("Car Indent Form",user.name)
        remarks_by="hr_head_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>
        The HR Head has approved the car rental form submitted by {user.employee_name}.
        <br>
        {updated_by} have approved the request for the activity mentioned below:
        """
        body = self.create_email_body(form,user,subject, content,updated_by,remarks_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_purchase_team_to_purchase_head(self, user):
        recipient_email = emailMaster.purchase_head_email
        print("FOR pt TO ph-----",recipient_email,"+++++++++++++++",recipient_email)
        subject = "Car Rental Form Approved by Purchase Team"
        regards = "Purchase Team"
        updated_by = emailMaster.purchase_team
        form = frappe.get_doc("Car Indent Form",user.name)
        remarks_by="purchase_team_remarks"
        revised_form = frappe.get_doc("Purchase Team Form",user.name)
        content = f"""
        Dear Sir/Madam,
        <br><br>The Purchase Team has reviewed and approved the car rental form submitted by {user.employee_name}.
        <br>{updated_by} have updated the quotation for the activity mentioned below:
        """
        body = self.create_email_body_revised(form,revised_form,user,subject, content,updated_by,remarks_by,regards)
        print(">>> NOW CALLING SEND <<<")
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_purchase_head_to_finance_team(self, user):
        recipient_emails = emailMaster.finance_team_emails
        print("FOR ph TO ft-----",recipient_emails,"+++++++++++++++",recipient_emails)
        subject = "Car Rental Form Approved by Purchase Head"
        regards = "Purchase Head"
        form = frappe.get_doc("Car Indent Form",user.name)
        revised_form = frappe.get_doc("Purchase Team Form",user.name)
        updated_by = emailMaster.purchase_head
        remarks_by="purchase_head_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>The Purchase Head has approved the car rental form for {user.employee_name}.
        <br>{updated_by} have approved the request for the activity mentioned below:
        """
        body = self.create_email_body_revised(form,revised_form,user,subject, content,updated_by,remarks_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_emails)

    def for_finance_team_to_finance_head(self, user):
        # print("FInacne Team to Finance Head",user.employee_details)
        recipient_emails = emailMaster.finance_head_emails
        print("FOR FT TO FH-----",recipient_emails,"+++++++++++++++",recipient_emails)
        subject = "Car Rental Form Approved by Finance Team"
        regards ="Finance Team"
        form = frappe.get_doc("Car Indent Form",user.name)
        print("form done++++++++++++++++++++++++++++++++++")
        revised_form = frappe.get_doc("Purchase Team Form",user.name)
        print("purchase form done +++++++++++++++++++++++++++++++++++++++++")
        quot_form=frappe.get_last_doc(doctype="Car Quotation",filters={"employee_details": user.name})

        print("quot form done +++++++++++++++++++++++++++++++++++++++++", quot_form)
        updated_by = emailMaster.finance_team
        remarks_by="finance_team_remarks" #to change here  // finance team remarks // need another form car quotation // to add new fields in email body
        content = f"""
        Dear Sir/Madam,
        <br><br>The Finance Team has approved the car rental form for {user.employee_name}.
        <br>{updated_by} have approved the request for the activity mentioned below:
        """
        body = self.create_email_body_quot(form,revised_form,quot_form,user,subject, content,updated_by,remarks_by,regards) 
        # print(body)
        self.send(subject=subject, body=body, recipient_email=recipient_emails)
    
    def for_finance_head_to_finance_team(self, user, quotation_id):

        recipients = emailMaster.finance_team_emails

        subject = f"Quotation Approved by Finance Head - {quotation_id}"

        body = f"""
        Quotation {quotation_id} has been approved by Finance Head.

        Please proceed with deduction generation.

        Regards,
        Finance Head
        """

        self.send(
            subject=subject,
            recipient_email=recipients,
            body=body,
            bcc_list=self.get_bcc_list()
        )
    
    def for_finance_team_to_finance_head_payload(self, user, payload):

        print("Finance Team to Finance Head Payload", payload)
        print("Finance Team to Finance Head Payload", user)

        recipient_emails = emailMaster.finance_head_emails

        quot_form = frappe.get_doc("Car Quotation", payload["quotation_id"])
        form = frappe.get_doc("Car Indent Form", quot_form.employee_details)
        revised_form = frappe.get_doc("Purchase Team Form", quot_form.employee_details)

        finance_company = quot_form.finance_company
        action_by = quot_form.finance_team_action_by

        context = {
            "company": user.company,
            "employee_name": user.employee_name,
            "designation": user.designation,
            "vehicle": f"{form.make} - {form.model}",
            "eligibility": user.eligibility,
            "ex_showroom": form.net_ex_showroom_price,
            "revised_amount": revised_form.revised_financed_amount,
            "emi_finance": quot_form.emi_financing,
            "total_emi": quot_form.total_emi,
            "remarks": getattr(quot_form, "finance_team_remarks", "-"),
            "finance_company": finance_company,
            "action_by": action_by,
            "link": f"{frappe.utils.get_url()}/login#login",
            "regards": "Finance Team"
        }

        template = frappe.get_doc("Email Template", "Car Quotation Finance Team to Finance Head Approval")
        subject = frappe.render_template(template.subject, context)
        body = frappe.render_template(template.response_html, context)
        print("Sending email now...")

        self.send(
            subject=subject,
            body=body,
            recipient_email=recipient_emails,
            bcc_list=self.get_bcc_list()
        )

    def for_finance_head_to_accounts_team(self, user):
        recipient_email = emailMaster.accounts_team_email
        print(user)
        subject = "Car Rental Form Final Approval"
        regards = "Finance Head"
        updated_by = emailMaster.finance_head
         #to change/check here  finance head remarks  new form needed- car quotation form // add new fields in email body // must create new function for email body
        form = frappe.get_doc("Car Indent Form",user.name)
        revised_form = frappe.get_doc("Purchase Team Form",user.name)
        quot_form=frappe.get_last_doc(doctype="Car Quotation",filters={"employee_details": user.name})
        remarks_by="finance_head_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>
        The car rental form submitted by {user.employee_name} has been approved at all levels and is now ready for processing.
        Kindly proceed with the final steps.
        <br>
        {updated_by} have approved the request for the activity mentioned below:
        """
        body = self.create_email_body_quot(form,revised_form,quot_form,user,subject, content,updated_by,remarks_by,regards) 
        # body = self.create_email_body_revised(form,revised_form,user,subject, content,updated_by,remarks_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_deduction_finance_to_finance_head(self,user,payload):
        recipient_email = emailMaster.finance_head_email
        print("Finance head email---->",recipient_email)
        recipient_email2 = emailMaster.finance_head2_email
        print("Finance head 2 email---->",recipient_email2)
        subject = "Company and Employee Deduction Form Approved by Finance Team"
        form = frappe.get_doc("Company and Employee Deduction",user.name)
        print("deduction done +++++++++++++++++++++++++++++++++++++++++",form)
        revised_form = frappe.get_doc("Car Quotation",payload["quotation_id"])
        print("quotation form done +++++++++++++++++++++++++++++++++++++++++",revised_form)
        employee_details=revised_form.employee_details
        print("employee details____________",employee_details)
        regards="Finance Team"
        updated_by = emailMaster.finance_team
        remarks_by="finance_team_remarks" #to change here  // finance team remarks // need another form car quotation // to add new fields in email body
        content = f"""
        Dear Sir/Madam,
        <br><br>The Finance Team has approved the Company and Employee Deduction Form for {employee_details}.
        <br>{updated_by} have approved the request for the activity mentioned below:
        """

        body = self.create_email_body_deduction(form, revised_form, user, subject, content, updated_by, remarks_by, regards)
        print(body)
        self.send(subject=subject, body=body, recipient_email=recipient_email)
        self.send(subject=subject, body=body, recipient_email=recipient_email2)

    def for_deduction_finance_head_to_accounts(self,user,payload):
        recipient_email = emailMaster.accounts_team_email
        print("accounts email---->",recipient_email)
        subject = "Company and Employee Deduction Form Approved by Finance Head"
        form = frappe.get_doc("Company and Employee Deduction",user.name)
        print("deduction done +++++++++++++++++++++++++++++++++++++++++")
        revised_form = frappe.get_doc("Car Quotation",payload["quotation_id"])
        print("quotation form done +++++++++++++++++++++++++++++++++++++++++")
        employee_details=revised_form.employee_details
        print("employee details____________",employee_details)
        regards="Finance Head"
        updated_by = emailMaster.finance_head
        remarks_by="finance_team_remarks" #to change here  // finance team remarks // need another form car quotation // to add new fields in email body
        content = f"""
        Dear Sir/Madam,
        <br><br>The Finance Team has approved the Company and Employee Deduction Form for {employee_details}.
        <br>{updated_by} has approved the request for the activity mentioned below:
        """

        body = self.create_email_body_deduction(form, revised_form, user, subject, content, updated_by, remarks_by, regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)
    
    #reject deduction
    def for_reject_deduction_by_finance_head(self,user,payload):
        recipient_email = emailMaster.finance_team_emails
        print("accounts email---->",recipient_email)
        form = frappe.get_doc("Company and Employee Deduction",user.name)
        print("deduction done +++++++++++++++++++++++++++++++++++++++++")
        revised_form = frappe.get_doc("Car Quotation",payload["quotation_id"])
        print("quotation form done +++++++++++++++++++++++++++++++++++++++++")
        employee_details=revised_form.employee_details
        print("employee details____________",employee_details)

        subject = "Company and Employee Deduction Form Rejected by Finance Head"
        cc_list=[emailMaster.finance_head2_email]
        remarks_by="finance_head_remarks"
        content=f"""
        Dear Sir/Madam,
        <br><br>
        This is to notify the Finance Team that the Company and Employee Deduction Form with ID - {user.name} is rejected by the Finance Head.

        """
        body = self.create_reject_email_body(form,subject,content,remarks_by)
        self.send_reject(subject,recipient_email,cc_list,body)


    #rejection CAR INDENT FORM
    def for_reject_by_reporting(self,user):
        recipient_email = user.email_id     
        subject = "Car Rental Form Rejected by Reporting Manager"
        cc_list=[emailMaster.hr_team_email]
        remarks_by="reporting_head_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>
        This is to notify {user.employee_name} that the car rental form submitted by you has been rejected by the Reporting Manager for the following reasons:<br>
        """
        form = frappe.get_doc("Car Indent Form",user.name)
        body = self.create_reject_email_body(form,subject,content,remarks_by)
        self.send_reject(subject,recipient_email,cc_list,body)

    def for_reject_by_hr_team(self,user): 
        doc = frappe.get_doc("Employee Master",user.reporting_head)  #reporting head details
        # reporting_head_name = doc.employee_name
        recipient_email = user.email_id   
        subject = "Car Rental Form Rejected by HR Team"
        cc_list=[doc.email_id]   #reporting head email
        remarks_by="hr_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>
        This is to notify {user.employee_name} that the car rental form submitted by you has been rejected by the HR Team for the following remarks:<br>
        """
        form = frappe.get_doc("Car Indent Form",user.name)
        body = self.create_reject_email_body(form,subject,content,remarks_by)
        self.send_reject(subject,recipient_email,cc_list,body)

    def for_reject_by_travel_desk(self,user): #this
        recipient_email = user.email_id     
        subject = "Car Rental Form Rejected by Travel Desk"
        doc = frappe.get_doc("Employee Master",user.reporting_head)
        cc_list=[emailMaster.hr_team_email, doc.email_id]
        remarks_by="travel_desk_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>
        This is to notify {user.employee_name} that the car rental form submitted by you has been rejected by the Travel Desk Team for the following remarks:<br>
        """
        form = frappe.get_doc("Car Indent Form",user.name)
        body = self.create_reject_email_body(form,subject,content,remarks_by)
        self.send_reject(subject,recipient_email,cc_list,body)
    
    def for_reject_by_hr_head(self,user): #this
        recipient_email = user.email_id     
        subject = "Car Rental Form Rejected by HR Head"
        doc = frappe.get_doc("Employee Master",user.reporting_head)
        cc_list=[emailMaster.hr_team_email, emailMaster.travel_desk_email, doc.email_id]
        remarks_by="hr_head_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>
        This is to notify {user.employee_name} that the car rental form submitted by you has been rejected by the HR Head for the following remarks:<br>
        """
        form = frappe.get_doc("Car Indent Form",user.name)
        body = self.create_reject_email_body(form,subject,content,remarks_by)
        self.send_reject(subject,recipient_email,cc_list,body)

    def for_reject_by_purchase_head(self,user):
        recipient_email=emailMaster.purchase_team_email
        subject="Purchase Form Rejected by Purchase Head"
        remarks_by="purchase_head_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>
        This is to notify the Purchase Team that the car rental form of {user.employee_name} submitted by you has been rejected by the Purchase Head for the following remarks:<br>
        <br><br>
        If you have any questions, feel free to reach out to us.(meriltraveldesk@merillife.com)
        """
        form = frappe.get_doc("Purchase Team Form",user.name)
        body = self.create_reject_email_body(form,subject,content,remarks_by)
        self.send(subject,recipient_email,body)

    def for_reject_by_purchase_team(self,user):
        recipient_email=emailMaster.hr_team_email
        subject="Purchase Form Rejected by Purchase Team"
        remarks_by="purchase_team_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>
        This is to notify the HR Team that the car rental form of {user.employee_name} submitted by you has been rejected by the Purchase Team for the following remarks:<br>
        """
        form = frappe.get_doc("Purchase Team Form",user.name)
        body = self.create_reject_email_body(form,subject,content,remarks_by)
        self.send(subject,recipient_email,body)

       
    def for_finance_fill_quotation_acknowledgement(self, user, payload):

        recipient_email = emailMaster.finance_team_emails
        vendors = payload.get("vendors", [])
        email_phase = payload.get("email_phase") or "Initial"

        print("🔥 ACK EMAIL →", vendors, email_phase)

        form = frappe.get_doc("Car Indent Form", user.name)
        purchase_form = frappe.get_doc("Purchase Team Form", user.name)

        template_name = (
            "Revised Finance Quotation Acknowledgement"
            if email_phase == "Revised"
            else "Finance Quotation Acknowledgement"
        )

        template = frappe.get_doc("Email Template", template_name)
        for vendor in vendors:
            context = {
                "employee_name": user.employee_name,
                "company": user.company,
                "designation": user.designation,
                "vehicle": f"{form.make} - {form.model}",
                "eligibility": user.eligibility,
                "finance_amount": purchase_form.revised_financed_amount,
                "remarks": getattr(form, "finance_remarks", "No remarks"),
                "updated_by": vendor,
                "regards": vendor,
                "link": f"{frappe.utils.get_url()}/app"
            }

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html, context)

            self.send(
                subject=subject,
                recipient_email=recipient_email,
                body=body,
                bcc_list=self.get_bcc_list()
            )


    def get_vendor_email_body(self, vendor_name, user, form, link, email_phase=None):

        template_name = (
            "Car Quotation Revised Request"
            if email_phase == "Revised"
            else "Car Quotation Request"
        )

        context = {
            "vendor_name": vendor_name,
            "employee_name": user.employee_name,
            "make": form.make,
            "model": form.model,
            "engine": form.engine,
            "colour": form.colour,
            "link": link
        }

        template = frappe.get_doc("Email Template", template_name)
        subject = frappe.render_template(template.subject, context)
        body = frappe.render_template(template.response_html, context)

        return {"subject": subject, "body": body}

    def for_car_quotation(self, user, payload):

        print("Preparing to send car quotation emails with payload:", payload)
        selected_vendors = {v.lower().strip() for v in payload.get("email_send_to", [])}
        send_to_all = payload.get("send_to_all")
        email_phase = payload.get("email_phase") or "Initial"
        quotation_id = payload.get("quotation_id")

        all_vendors = frappe.get_all(
            "Vendor Master",
            fields=["name", "company_name", "contact_email"]
        )

        car_indent_form = frappe.get_doc("Car Indent Form", user.name)

        emails_sent = []
        errors = []

        for vendor in all_vendors:

            vendor_name = (vendor.name or "").strip()
            vendor_name_lower = vendor_name.lower()
            email = (vendor.contact_email or "").strip()

            if not email:
                continue

            if vendor_name_lower not in selected_vendors and not send_to_all:
                continue

            # FIXED UNIQUE KEY (phase-aware)
            # unique_key = f"{user.name}|{vendor_name}|quotation_request|{email_phase}"
            unique_key = f"{quotation_id}|{vendor_name}|{email_phase}"

            try:
                log = frappe.get_doc({
                    "doctype": "Vendor Email Log",
                    "reference_doctype": "Purchase Team Form",
                    "reference_name": user.name,
                    "vendor": vendor_name,
                    "email": email,
                    "email_type": f"quotation_request_{email_phase}",
                    "status": "Pending",
                    "unique_key": unique_key
                })

                log.insert(ignore_permissions=True)

            except frappe.UniqueValidationError:
                print(f"Skipping duplicate: {vendor_name}")
                continue

            try:
                # Generate link
                link = (
                    f"{frappe.utils.get_url()}/vendor-assets-quotation/new?"
                    f"finance_company={vendor_name}&"
                    f"employee_details={user.name}"
                )

                # ONLY append for revised
                if email_phase == "Revised" and quotation_id:
                    link += f"&quotation_id={quotation_id}&is_revised=1"

                # Get template response
                email_content = self.get_vendor_email_body(
                    vendor_name,
                    user,
                    car_indent_form,
                    link,
                    email_phase
                )

                # USE TEMPLATE SUBJECT + BODY
                subject = email_content.get("subject")
                body = email_content.get("body")

                # SEND EMAIL
                self.send_quotations(
                    subject=subject,
                    body=body,
                    recipient_email=email,
                    bcc_list=self.get_bcc_list()
                )

                log.status = "Sent"
                log.save(ignore_permissions=True)

                emails_sent.append(vendor_name)

            except Exception as e:

                log.status = "Failed"
                log.error_message = str(e)
                log.save(ignore_permissions=True)

                errors.append(vendor_name)
                frappe.log_error(frappe.get_traceback(), "Vendor Email Failed")

        frappe.db.commit()

        # Update Flags (truth-based)
        car_purchase_form = frappe.get_doc("Purchase Team Form", user.name)

        sent_vendors_lower = {v.lower() for v in emails_sent}

        for vendor in emails_sent:
            fieldname = f"email_sent_to_{vendor.lower().replace(' ', '_')}"
            
            if hasattr(car_purchase_form, fieldname):
                setattr(car_purchase_form, fieldname, 1)

        all_vendor_names = {
            (v.name or "").strip().lower()
            for v in all_vendors
            if (v.contact_email or "").strip()
        }

        if all_vendor_names and all_vendor_names.issubset(sent_vendors_lower):
            car_purchase_form.email_sent_to_all = 1

        car_purchase_form.save(ignore_permissions=True)

        return {
            "status": "success" if emails_sent else "info",
            "sent": emails_sent,
            "failed": errors,
            "message": f"Sent: {len(emails_sent)}, Failed: {len(errors)}"
        }


    # "-------------------------------------" EMAIL BODY COMPANY SELECTION EMAILS "-------------------------------------"
    def create_selected_company_process(self,car_form,user, form_link):
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
            <h1>Congratulations, <span class="company-name">{car_form.finance_company}</span>!</h1>
            <p>Your quotation request for <strong>{user.employee_name}</strong> has been selected for further processing.</p>
            <p>Please fill out the required form by clicking the link below. Ensure you carefully enter the <strong>PO details</strong> and upload the necessary documents.</p>

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
                        <td>PO</td>
                    </tr>
                    <tr>
                        <td>User Name</td>
                        <td>{user.employee_name}</td>
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
        return body
      
    def for_selected_compny_process(self,quotation_id):
        print("Selected Company Process Quotation ID:", quotation_id)
        car_quot_form = frappe.get_doc("Car Quotation",quotation_id)  
        user = frappe.get_doc("Employee Master",car_quot_form.employee_details)  
        form_link = f"{frappe.utils.get_url()}/car-purchase-form/new?quotation_form={quotation_id}&user={user.name}&company={car_quot_form.finance_company}"
        body = self.create_selected_company_process(car_quot_form,user,form_link)
        subject = f"Car Onboard Process for {user.employee_name}"
        vendor =frappe.get_doc("Vendor Master",car_quot_form.finance_company)
        self.send(subject=subject, body=body, recipient_email=vendor.contact_email)

    # rejection for car quotation
    def for_reject_finance_head_to_finance_team(self,quotation_id):
        car_quot_form = frappe.get_doc("Car Quotation",quotation_id)  #ismei se milega finance company
        vendor =frappe.get_doc("Vendor Master",car_quot_form.finance_company) #this is vendor details recipient humara
        user = frappe.get_doc("Employee Master",car_quot_form.employee_details)  #yaha se milega employee, jiska sirf naam chahiye
        recipient_email=vendor.contact_email
        subject=f"""{vendor.company_name} Car Quotation Rejected by Finance Head"""
        remarks_by="finance_head_remarks"
        cc_list=[emailMaster.finance_head2_email, emailMaster.finance_team_emails]

        content = f"""
        Dear {vendor.company_name},
        <br><br>
        This is to notify you that the Car Quotation Form of {user.employee_name} is rejected by the Finance Head for the following reasons:<br>
        """
        body = self.create_reject_email_body(car_quot_form,subject,content,remarks_by)  
        self.send_reject(subject,recipient_email,cc_list,body)  

    def for_reject_finance_team_to_vendor(self,quotation_id):
        car_quot_form = frappe.get_doc("Car Quotation",quotation_id)  #ismei se milega finance company
        vendor =frappe.get_doc("Vendor Master",car_quot_form.finance_company) #this is vendor details recipient humara
        user = frappe.get_doc("Employee Master",car_quot_form.employee_details)  #yaha se milega employee, jiska sirf naam chahiye
        recipient_email=vendor.contact_email
        subject=f"""{vendor.company_name} Car Quotation Rejected by Finance Team"""
        remarks_by="finance_team_remarks"
        cc_list=[emailMaster.finance_head2_email, emailMaster.finance_head_email]

        content = f"""
        Dear {vendor.company_name},
        <br><br>
        This is to notify you that the Car Quotation Form of {user.employee_name} is rejected by the Finance Team for the following reasons:<br>
        """
        body = self.create_reject_email_body(car_quot_form,subject,content,remarks_by)  
        self.send_reject(subject,recipient_email,cc_list,body) 
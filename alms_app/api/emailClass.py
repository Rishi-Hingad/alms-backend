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
from alms_app.api.role_emails import get_emails_by_role

emailMaster = EmailMaster()

class EmailServices:
    def get_approver_name(self, form_name):
        entries = frappe.get_all(
            "Approval Entry",
            filters={
                "applied_to_doctype": "Car Indent Form",
                "record": form_name,
                "status": ["in", ["Approved", "Rejected"]]
            },
            fields=["modified_by"],
            order_by="modified desc",
            limit=1
        )
        if entries:
            updated_by_email = entries[0].modified_by
        else:
            updated_by_email = frappe.session.user
            
        emp = frappe.get_all("Employee", filters={"user_id": updated_by_email}, fields=["employee_name", "full_name"], limit=1)
        if emp:
            return emp[0].get("employee_name") or emp[0].get("full_name") or updated_by_email
        return frappe.db.get_value("User", updated_by_email, "full_name") or updated_by_email

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

            # Filter out invalid email 'Administrator'
            recipient_email = [r for r in recipient_email if r and str(r).lower() != "administrator"]
            
            print(f"DEBUG RECIPIENTS AFTER FILTER: {recipient_email}")

            if not recipient_email:
                frappe.logger().info("⚠️ No valid recipient_email found after filtering Administrator. Skipping email.")
                print("DEBUG: ⚠️ No valid recipient_email found after filtering Administrator. Skipping email.")
                return False

            if cc_list:
                if isinstance(cc_list, str):
                    cc_list = [cc_list]
                cc_list = [c for c in cc_list if c and str(c).lower() != "administrator"]
            
            if bcc_list:
                if isinstance(bcc_list, str):
                    bcc_list = [bcc_list]
                bcc_list = [b for b in bcc_list if b and str(b).lower() != "administrator"]

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


    # ------------------- User Acknowledgement Email "------------------"
    def acknowledgement_email(self, user, statusFrom, statusTo):
        recipient_email = user.company_email or user.user_id
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
        recipient_email = user.company_email or user.user_id
        cc_list = get_emails_by_role("HR")
        if user.reporting_head:
            reporting_head_email = frappe.db.get_value("Employee", user.reporting_head, "company_email")
            if reporting_head_email and reporting_head_email not in cc_list:
                cc_list.append(reporting_head_email)

        form_url = f"{frappe.utils.get_url()}/car-request?employee_code={user.name}"

        emp_name = f"{user.first_name} {user.last_name}"

        # Fetch Email Template
        template = frappe.get_doc("Email Template", "Car Rental Eligibility Notification")

        context = {
            "employee_name": emp_name,
            "form_url": form_url
        }

        subject = frappe.render_template(template.subject, context)

        body = frappe.render_template(template.response_html, context)

        self.send(
            subject=subject,
            recipient_email=recipient_email,
            body=body,
            cc_list=cc_list
        )


    def for_employee_to_reporting(self, user, car_indent_form_name):
        
        employee_doc = frappe.get_doc("Employee", user)
        full_name = f"{employee_doc.first_name} {employee_doc.last_name}"
        if not employee_doc.reporting_head:
            frappe.log_error(f"Employee '{full_name}' has no reporting head assigned!")
            return

        try:
            reporting_head = frappe.get_doc("Employee", employee_doc.reporting_head)
        except Exception as e:
            frappe.log_error(f"Error fetching reporting head: {str(e)}")
            return

        recipient_email = reporting_head.company_email or reporting_head.user_id
        reporting_head_name = reporting_head.employee_name or reporting_head.full_name

        if not recipient_email:
            frappe.log_error(f"Reporting head '{reporting_head_name}' has no email!")
            return

        token = secrets.token_urlsafe(32)
        # Save token in Car Indent Form
        car_doc = frappe.get_doc("Car Indent Form", car_indent_form_name)
        car_doc.approval_token = token
        car_doc.save(ignore_permissions=True)
        frappe.db.commit()

        # Secure link with token
        link = f"{get_url()}/reporting_head_approval?id={quote(car_indent_form_name)}&token={token}"

        template = frappe.get_doc("Email Template", "Car Indent Form Reporting Head Approval")

        context = {
            "reporting_head_name": reporting_head_name,
            "employee_name": full_name,
            "link": link
        }

        subject = frappe.render_template(template.subject or "Approval Required", context)
        message = frappe.render_template(template.response_html or "", context)

        self.send(
            subject=subject,
            recipient_email=recipient_email,
            body=message
        )

    def for_employee_to_hr_team(self, user, car_indent_form_name):
        recipient_email = emailMaster.hr_team_emails
        template = frappe.get_doc("Email Template", "Car Indent Submission Notification")
        user_doc = frappe.get_doc("Employee", user)
        full_name = f"{user_doc.first_name} {user_doc.last_name}"
        car_indent_form = frappe.get_doc("Car Indent Form", car_indent_form_name)

        context = {
            "user_doc": user_doc,
            "car_indent_form": car_indent_form,
            "employee_name": full_name,
            "employee_id": user,
            "finance_amount": car_indent_form.finance_amount
        }

        subject = frappe.render_template(template.subject, context)
        body = frappe.render_template(template.response_html, context)

        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_reporting_to_hr_team(self, user):
        try:
            recipient_email = emailMaster.hr_team_emails
            full_name = f"{user.first_name} {user.last_name}"

            form = frappe.get_doc("Car Indent Form", {"employee_code": user.name})

            context = {
                "employee_name": full_name,
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
        try:
            emailMaster = EmailMaster()
            recipient_email = emailMaster.hr_head_email

            form = frappe.get_doc("Car Indent Form", user.name)

            context = {
                "employee_name": user.employee_name,
                "company": user.company,
                "designation": user.designation,
                "eligibility": user.eligibility,
                "make": form.make,
                "model": form.model,
                "finance_amount": form.finance_amount,
                "updated_by": self.get_approver_name(form.name),
                "remarks": getattr(form, "hr_remarks", ""),
                "login_link": f"{frappe.utils.get_url()}/login"
            }

            template = frappe.get_doc(
                "Email Template",
                "Car Rental Approved - HR Team to HR Head"
            )

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html or "", context)

            self.send(
                subject=subject,
                body=body,
                recipient_email=recipient_email
            )

        except Exception as e:
            frappe.log_error(str(e), "HR Team To HR Head Email Error")


    def for_hr_team_to_travel_desk(self, user):
        try:
            emailMaster = EmailMaster()
            recipient_email = emailMaster.travel_desk_email

            form = frappe.get_doc("Car Indent Form", user.name)

            context = {
                "employee_name": user.employee_name,
                "company": user.company,
                "designation": user.designation,
                "eligibility": user.eligibility,
                "make": form.make,
                "model": form.model,
                "finance_amount": form.finance_amount,
                "updated_by": self.get_approver_name(form.name),
                "remarks": getattr(form, "hr_remarks", ""),
                "login_link": f"{frappe.utils.get_url()}/login"
            }

            template = frappe.get_doc(
                "Email Template",
                "Car Rental Approved - HR Team to Travel Desk"
            )

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html or "", context)

            self.send(
                subject=subject,
                body=body,
                recipient_email=recipient_email
            )

        except Exception as e:
            frappe.log_error(str(e), "HR Team To Travel Desk Email Error")


    def for_travel_desk_to_hr_head(self, user):
        try:
            emailMaster = EmailMaster()
            recipient_email = emailMaster.hr_head_email
            
            form = frappe.get_doc("Car Indent Form", user.name)

            context = {
                "employee_name": user.employee_name,
                "company": user.company,
                "designation": user.designation,
                "eligibility": user.eligibility,
                "make": form.make,
                "model": form.model,
                "finance_amount": form.finance_amount,
                "updated_by": self.get_approver_name(form.name),
                "remarks": getattr(form, "travel_desk_remarks", ""),
                "login_link": f"{frappe.utils.get_url()}/login"
            }

            template = frappe.get_doc(
                "Email Template",
                "Car Rental Approved - Travel Desk to HR Head"
            )

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html or "", context)

            self.send(
                subject=subject,
                body=body,
                recipient_email=recipient_email
            )

        except Exception as e:
            frappe.log_error(str(e), "Travel Desk To HR Head Email Error")

    def for_hr_head_to_purchase_team(self, user):
        try:
            emailMaster = EmailMaster()
            recipient_email = emailMaster.purchase_team_email

            form = frappe.get_doc("Car Indent Form", user.name)

            context = {
                "employee_name": user.employee_name,
                "company": user.company,
                "designation": user.designation,
                "eligibility": user.eligibility,
                "make": form.make,
                "model": form.model,
                "finance_amount": form.finance_amount,
                "updated_by": self.get_approver_name(form.name),
                "remarks": getattr(form, "hr_head_remarks", ""),
                "login_link": f"{frappe.utils.get_url()}/login"
            }

            template = frappe.get_doc(
                "Email Template",
                "Car Rental Approved - HR Head to Purchase Team"
            )

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html or "", context)

            self.send(
                subject=subject,
                body=body,
                recipient_email=recipient_email
            )

        except Exception as e:
            frappe.log_error(str(e), "HR Head To Purchase Team Email Error")

    # def for_purchase_team_to_purchase_head(self, user):
    #     recipient_email = emailMaster.purchase_head_email
    #     print("FOR pt TO ph-----",recipient_email,"+++++++++++++++",recipient_email)
    #     subject = "Car Rental Form quotation Updated by Purchase Team"
    #     regards = "Purchase Team"
    #     form = frappe.get_doc("Car Indent Form",user.name)
    #     updated_by = self.get_approver_name(form.name)
    #     remarks_by="purchase_team_remarks"
    #     revised_form = frappe.get_doc("Purchase Team Form",user.name)
    #     content = f"""
    #     Dear Sir/Madam,
    #     <br><br>The Purchase Team has reviewed and approved the car rental form submitted by {user.employee_name}.
    #     <br>{updated_by} have updated the quotation for the activity mentioned below:
    #     """
    #     body = self.create_email_body_revised(form,revised_form,user,subject, content,updated_by,remarks_by,regards)
    #     print(">>> NOW CALLING SEND <<<")
    #     self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_purchase_team_to_purchase_head(self, user):
        try:
            emailMaster = EmailMaster()
            recipient_email = emailMaster.purchase_head_email

            form = frappe.get_doc("Car Indent Form", user.name)
            revised_form = frappe.get_doc("Purchase Team Form", user.name)
            
            context = {
                "employee_name": user.full_name,
                "company": user.company,
                "designation": user.meril_designation,
                "eligibility": user.eligibility,
                "make": revised_form.revised_make,
                "model": revised_form.revised_car_modal,
                "revised_finance_amount": revised_form.revised_finance_amount,
                "updated_by": self.get_approver_name(form.name),
                "remarks": getattr(form, "purchase_team_remarks", ""),
                "login_link": f"{frappe.utils.get_url()}/login",
            }

            template = frappe.get_doc(
                "Email Template",
                "Car Rental Quotation Updated - Purchase Team"
            )

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html or "", context)

            self.send(
                subject=subject,
                body=body,
                recipient_email=recipient_email
            )

        except Exception as e:
            frappe.log_error(str(e), "Purchase Team To Purchase Head Email Error")
        
    def for_purchase_head_to_finance_team(self, user):
        try:
            emailMaster = EmailMaster()
            recipient_emails = emailMaster.finance_team_emails

            form = frappe.get_doc("Car Indent Form", user.name)
            revised_form = frappe.get_doc("Purchase Team Form", user.name)

            context = {
                "employee_name": user.full_name,
                "company": user.company,
                "designation": user.meril_designation,
                "eligibility": user.eligibility,
                "make": revised_form.revised_make,
                "model": revised_form.revised_car_modal,
                "revised_finance_amount": revised_form.revised_finance_amount,
                "updated_by": self.get_approver_name(form.name),
                "remarks": getattr(form, "purchase_head_remarks", ""),
                "login_link": f"{frappe.utils.get_url()}/login",
            }

            template = frappe.get_doc(
                "Email Template",
                "Car Rental Approved - Purchase Head"
            )

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html or "", context)

            self.send(
                subject=subject,
                body=body,
                recipient_email=recipient_emails
            )

        except Exception as e:
            frappe.log_error(str(e), "Purchase Head To Finance Team Email Error")

    # def for_purchase_head_to_finance_team(self, user):
    #     recipient_emails = emailMaster.finance_team_emails
    #     print("FOR ph TO ft-----",recipient_emails,"+++++++++++++++",recipient_emails)
    #     subject = "Car Rental Form Approved by Purchase Head"
    #     regards = "Purchase Head"
    #     form = frappe.get_doc("Car Indent Form",user.name)
    #     revised_form = frappe.get_doc("Purchase Team Form",user.name)
    #     updated_by = self.get_approver_name(form.name)
    #     remarks_by="purchase_head_remarks"
    #     content = f"""
    #     Dear Sir/Madam,
    #     <br><br>The Purchase Head has approved the car rental form for {user.employee_name}.
    #     <br>{updated_by} have approved the request for the activity mentioned below:
    #     """
    #     body = self.create_email_body_revised(form,revised_form,user,subject, content,updated_by,remarks_by,regards)
    #     self.send(subject=subject, body=body, recipient_email=recipient_emails)

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
        updated_by = self.get_approver_name(form.name)
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
        try:
            emailMaster = EmailMaster()
            recipients = emailMaster.finance_team_emails

            form = frappe.get_doc("Car Indent Form", user.name)

            context = {
                "quotation_id": quotation_id,
                "employee_name": user.employee_name,
                "company": user.company,
                "designation": user.designation,
                "make": form.make,
                "model": form.model,
                "finance_amount": form.finance_amount,
                "updated_by": emailMaster.finance_head,
                "login_link": f"{frappe.utils.get_url()}/login"
            }

            template = frappe.get_doc(
                "Email Template",
                "Quotation Approved - Finance Head"
            )

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html or "", context)

            self.send(
                subject=subject,
                body=body,
                recipient_email=recipients,
                bcc_list=self.get_bcc_list()
            )

        except Exception as e:
            frappe.log_error(
                str(e),
                "Finance Head To Finance Team Email Error"
            )
    
    def for_finance_team_to_finance_head_payload(self, user, payload):

        print("Finance Team to Finance Head Payload", payload)
        print("Finance Team to Finance Head Payload", user)

        recipient_emails = emailMaster.finance_head_emails

        quot_form = frappe.get_doc("Car Quotation", payload["quotation_id"])
        form = frappe.get_doc("Car Indent Form", quot_form.employee_details)
        revised_form = frappe.get_doc("Purchase Team Form", quot_form.employee_details)

        finance_company = quot_form.finance_company
        action_by = self.get_approver_name(form.name)

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
        form = frappe.get_doc("Car Indent Form",user.name)
        updated_by = self.get_approver_name(form.name)
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
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    # def for_deduction_finance_to_finance_head(self,user,payload):
    #     recipient_email = emailMaster.finance_head_email
    #     print("Finance head email---->",recipient_email)
    #     recipient_email2 = emailMaster.finance_head2_email
    #     print("Finance head 2 email---->",recipient_email2)
    #     subject = "Deduction Approved by Finance Team"
    #     form = frappe.get_doc("Company and Employee Deduction",user.name)
    #     print("deduction done +++++++++++++++++++++++++++++++++++++++++",form)
    #     revised_form = frappe.get_doc("Car Quotation",payload["quotation_id"])
    #     print("quotation form done +++++++++++++++++++++++++++++++++++++++++",revised_form)
    #     employee_details=revised_form.employee_details
    #     print("employee details____________",employee_details)
    #     regards="Finance Team"
    #     updated_by = self.get_approver_name(form.name)
    #     remarks_by="finance_team_remarks"
    #     content = f"""
    #     Dear Sir/Madam,
    #     <br><br>The Finance Team has approved the Company and Employee Deduction Form for {employee_details}.
    #     <br>{updated_by} have approved the request for the activity mentioned below:
    #     """

    #     body = self.create_email_body_deduction(form, revised_form, user, subject, content, updated_by, remarks_by, regards)
    #     print(body)
    #     self.send(subject=subject, body=body, recipient_email=recipient_email)
    #     self.send(subject=subject, body=body, recipient_email=recipient_email2)

    def for_deduction_finance_to_finance_head(self, user, payload):
        try:
            emailMaster = EmailMaster()

            form = frappe.get_doc("Company and Employee Deduction", user.name)
            quotation = frappe.get_doc("Car Quotation", payload["quotation_id"])

            context = {
                "quotation_id": payload["quotation_id"],
                "employee_name": quotation.employee_details,
                "company_total_emi": form.total_emi,
                "company_interim_payment": form.interim_payment,
                "company_quarterly_payment": form.quarterly_payment,
                "employee_total_emi": form.employee_total_emi,
                "employee_interim_payment": form.employee_interim_payment,
                "employee_quarterly_payment": form.employee_quarterly_payment,
                "remarks": getattr(
                    quotation,
                    "finance_team_remarks",
                    ""
                ),
                "updated_by": self.get_approver_name(form.name),
                "login_link": f"{frappe.utils.get_url()}/login"
            }

            template = frappe.get_doc(
                "Email Template",
                "Deduction Approved - Finance Team"
            )

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html or "", context)

            self.send(
                subject=subject,
                body=body,
                recipient_email=emailMaster.finance_head_email
            )

            self.send(
                subject=subject,
                body=body,
                recipient_email=emailMaster.finance_head2_email
            )

        except Exception as e:
            frappe.log_error(
                str(e),
                "Finance Team To Finance Head Email Error"
            )

    # def for_deduction_finance_head_to_accounts(self,user,payload):
    #     recipient_email = emailMaster.accounts_team_email
    #     print("accounts email---->",recipient_email)
    #     subject = "Deduction Approved by Finance Head"
    #     form = frappe.get_doc("Company and Employee Deduction",user.name)
    #     print("deduction done +++++++++++++++++++++++++++++++++++++++++")
    #     revised_form = frappe.get_doc("Car Quotation",payload["quotation_id"])
    #     print("quotation form done +++++++++++++++++++++++++++++++++++++++++")
    #     employee_details=revised_form.employee_details
    #     print("employee details____________",employee_details)
    #     regards="Finance Head"
    #     updated_by = self.get_approver_name(form.name)
    #     remarks_by="finance_head_remarks" #to change here  // finance team remarks // need another form car quotation // to add new fields in email body
    #     content = f"""
    #     Dear Sir/Madam,
    #     <br><br>The Finance Team has approved the Company and Employee Deduction Form for {employee_details}.
    #     <br>{updated_by} has approved the request for the activity mentioned below:
    #     """

    #     body = self.create_email_body_deduction(form, revised_form, user, subject, content, updated_by, remarks_by, regards)
    #     self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_deduction_finance_head_to_accounts(self, user, payload):
        try:
            emailMaster = EmailMaster()

            form = frappe.get_doc("Company and Employee Deduction", user.name)
            quotation = frappe.get_doc("Car Quotation", payload["quotation_id"])

            context = {
                "quotation_id": payload["quotation_id"],
                "employee_name": quotation.employee_details,
                "company_total_emi": form.total_emi,
                "company_interim_payment": form.interim_payment,
                "company_quarterly_payment": form.quarterly_payment,
                "employee_total_emi": form.employee_total_emi,
                "employee_interim_payment": form.employee_interim_payment,
                "employee_quarterly_payment": form.employee_quarterly_payment,
                "remarks": getattr(
                    quotation,
                    "finance_head_remarks",
                    ""
                ),
                "updated_by": self.get_approver_name(form.name),
                "login_link": f"{frappe.utils.get_url()}/login"
            }

            template = frappe.get_doc(
                "Email Template",
                "Deduction Approved - Finance Head"
            )

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html or "", context)

            self.send(
                subject=subject,
                body=body,
                recipient_email=emailMaster.accounts_team_email
            )

        except Exception as e:
            frappe.log_error(
                str(e),
                "Finance Head To Accounts Email Error"
            )
    
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
        recipient_email = user.company_email or user.user_id     
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
        doc = frappe.get_doc("Employee",user.reporting_head)  #reporting head details
        # reporting_head_name = doc.employee_name
        recipient_email = user.company_email or user.user_id   
        subject = "Car Rental Form Rejected by HR Team"
        cc_list=[doc.company_email or doc.user_id]   #reporting head email
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
        recipient_email = user.company_email or user.user_id     
        subject = "Car Rental Form Rejected by Travel Desk"
        doc = frappe.get_doc("Employee",user.reporting_head)
        cc_list=[emailMaster.hr_team_email, doc.company_email or doc.user_id]
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
        recipient_email = user.company_email or user.user_id     
        subject = "Car Rental Form Rejected by HR Head"
        doc = frappe.get_doc("Employee",user.reporting_head)
        cc_list=[emailMaster.hr_team_email, emailMaster.travel_desk_email, doc.company_email or doc.user_id]
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

        print(" ACK EMAIL →", vendors, email_phase)

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
            "employee_name": user.name,
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

            # FIXED UNIQUE KEY (phase-aware & prevents duplicates across forms)
            unique_key = f"{user.name}|{quotation_id or ''}|{vendor_name}|{email_phase}"

            # Check existence first to prevent Frappe UI toast errors
            if frappe.db.exists("Vendor Email Log", {"unique_key": unique_key}):
                print(f"Skipping duplicate: {vendor_name}")
                continue

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

            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Vendor Email Log Error")
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
        user = frappe.get_doc("Employee",car_quot_form.employee_details)  
        form_link = f"{frappe.utils.get_url()}/car-purchase-form/new?quotation_form={quotation_id}&user={user.name}&company={car_quot_form.finance_company}"
        body = self.create_selected_company_process(car_quot_form,user,form_link)
        subject = f"Car Onboard Process for {user.employee_name}"
        vendor =frappe.get_doc("Vendor Master",car_quot_form.finance_company)
        self.send(subject=subject, body=body, recipient_email=vendor.contact_email)

    # rejection for car quotation
    def for_reject_finance_head_to_finance_team(self,quotation_id):
        car_quot_form = frappe.get_doc("Car Quotation",quotation_id)  #ismei se milega finance company
        vendor =frappe.get_doc("Vendor Master",car_quot_form.finance_company) #this is vendor details recipient humara
        user = frappe.get_doc("Employee",car_quot_form.employee_details)  #yaha se milega employee, jiska sirf naam chahiye
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
        user = frappe.get_doc("Employee",car_quot_form.employee_details)  #yaha se milega employee, jiska sirf naam chahiye
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

    def send_allowance_email(self, employee_code):
        try:
            employee = frappe.get_doc("Employee", employee_code)
            email_to = employee.company_email or employee.user_id

            cc_employee = frappe.get_doc("Employee", employee.reporting_head)
            email_cc = cc_employee.company_email or cc_employee.user_id

            hr_roles = frappe.get_all("Has Role", filters={"role": "HR", "parenttype": "User"}, pluck="parent")
            hr_entries = []
            if hr_roles:
                hr_entries = frappe.get_all("User", filters={"name": ("in", hr_roles), "enabled": 1}, fields=["email", "full_name"])
                
            hr_emails = [row.email for row in hr_entries if row.email]
            hr_name = ", ".join([row.full_name for row in hr_entries]) or "HR Team"

            if not hr_emails:
                frappe.throw("No HR emails found with the HR role.")
            
            template = frappe.get_doc("Email Template", "Car Allowance Request Notification")

            context = {
                "employee": employee,
                "employee_name": employee.employee_name,
                "hr_name": hr_name,
            }

            subject = frappe.render_template(template.subject, context)
            body = frappe.render_template(template.response_html, context)

            self.send(
                subject=subject,
                recipient_email=hr_emails,
                body=body,
                cc_list=[email_cc] if email_cc else []
            )
            return {"status": "success", "message": f"Email sent successfully to {', '.join(hr_emails)}."}

        except Exception as e:
            frappe.log_error(f"Error in send_allowance_email: {str(e)}")
            return {"status": "failed", "message": str(e)}
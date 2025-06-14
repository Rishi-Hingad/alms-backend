
"""
this class manage the email for each levele of approvels 
"""

import smtplib,ssl
from email.message import EmailMessage
import frappe
from alms_app.api.email_master import EmailMaster
emailMaster = EmailMaster()


class EmailServices:
    def __init__(self):
        alms_settings = frappe.get_single("ALMS Settings")
        self.smtp_server = alms_settings.smtp_server
        self.smtp_port = alms_settings.smtp_port
        self.smtp_user = alms_settings.smtp_user
        self.smtp_password = alms_settings.smtp_password
        self.from_address = "noreply@merillife.com"

    def send(self,subject,recipient_email,body):
    
        try:
            msg = EmailMessage()
            msg.set_content(body, subtype="html")
            msg["Subject"] = subject
            msg["From"] = self.from_address
            msg["To"] = recipient_email
            msg["Bcc"] = "rishi.hingad@merillife.com"
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                response = server.send_message(msg)
                print("Email Sent Successfully!")
            frappe.msgprint(f"Email sent successfully to {recipient_email}.")

        except smtplib.SMTPException as smtp_error:
            # print("-----------[EMAIL ERROR]-------------",smtp_error)
            frappe.throw(f"SMTP error occurred: {smtp_error}")

        except Exception as e:
            # print("-----------[EMAIL ERROR]-------------",str(e))
            frappe.throw(f"Failed to send email: {str(e)}")
    
    #for Rejection 
    def send_reject(self, subject,recipient_email,cc_list, body):
        print("----------------sendng-------------")
        try:
            msg = EmailMessage()
            msg.set_content(body, subtype="html")
            msg["Subject"] = subject
            msg["From"] = self.from_address
            msg["To"] = recipient_email
            msg["Cc"] = ", ".join(cc_list)
            msg["Bcc"] = "rishi.hingad@merillife.com"
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                response = server.send_message(msg)
                print("Email Sent Successfully!")
            frappe.msgprint(f"Email sent successfully to {recipient_email}.")

        except smtplib.SMTPException as smtp_error:
            # print("-----------[EMAIL ERROR]-------------",smtp_error)
            frappe.throw(f"SMTP error occurred: {smtp_error}")

        except Exception as e:
            # print("-----------[EMAIL ERROR]-------------",str(e))
            frappe.throw(f"Failed to send email: {str(e)}")

    def send_quotations(self,subject,recipient_email,body):
    
        try:
            msg = EmailMessage()
            msg.set_content(body, subtype="html")
            msg["Subject"] = subject
            msg["From"] = self.from_address
            msg["To"] = recipient_email
            msg["Bcc"] = "rishi.hingad@merillife.com"
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                response = server.send_message(msg)
                print("Email Sent Successfully!")

        except smtplib.SMTPException as smtp_error:
            # print("-----------[EMAIL ERROR]-------------",smtp_error)
            frappe.throw(f"SMTP error occurred: {smtp_error}")

        except Exception as e:
            # print("-----------[EMAIL ERROR]-------------",str(e))
            frappe.throw(f"Failed to send email: {str(e)}")


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
                <p>Best regards,</p>
                <p><strong>Meril</strong></p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        self.send(subject=subject, body=body, recipient_email=recipient_email)
        return body

    # "-------------------------------------" EMAIL BODY "-------------------------------------"
    def create_email_body(self, form, user, subject, content, updated_by, remarks_by,regards=None, link=f"{frappe.utils.get_url()}/login#login"):
        user_eligibility = user.eligibility
        remark_text = getattr(form, remarks_by, "No remarks")
        print(remark_text)
        # here edited, eligibility
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
                    <td>{form.make} - {form.model}</td>
                </tr>
                <tr>
                    <td>Eligibility</td>
                    <td>{user.eligibility}</td>  
                </tr>
                <tr>
                    <td>Finance Amount</td>
                    <td>{form.finance_amount}</td>
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
                <a href="{link}" class="button"> Login Here </a>
            </p>
                
            <p>Best regards,</p>
            <p>CRMS Team</p>
        </body>
        </html>
        """
        return body
        
    def create_email_body_revised(self,
                                form, 
                                revised_form, 
                                user,
                                subject, 
                                content,
                                updated_by,
                                remarks_by, 
                                regards=None, 
                                link=f"{frappe.utils.get_url()}/login#login"):
        user_eligibility = user.eligibility
        remark_text = getattr(revised_form, remarks_by, None)
        # changed here, eligibility
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
                    <td>{form.make} - {form.model}</td>
                </tr>
                <tr>
                    <td>Eligibility</td>
                    <td>{user.eligibility}</td>
                </tr>
                <tr>
                    <td>Net Ex-Showroom Price</td>
                    <td>{form.net_ex_showroom_price}</td>
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
                
            <p>Best regards,</p>
            <p>{regards}</p>
        </body>
        </html>
        """
        return body
    
    def create_email_body_quot(self,
                                form,
                                revised_form, 
                                quot_form, 
                                user,
                                subject, 
                                content,
                                updated_by,
                                remarks_by, 
                                regards=None, 
                                link=f"{frappe.utils.get_url()}/login#login"):
        user_eligibility = user.eligibility
        remark_text = getattr(quot_form, remarks_by, None)
        print("+++++++++++++++++++++++++remark text found")
        # changed here, eligibility
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
                    <td>{form.make} - {form.model}</td>
                </tr>
                <tr>
                    <td>Eligibility</td>
                    <td>{user.eligibility}</td>
                </tr>
                <tr>
                    <td>Net Ex-Showroom Price</td>
                    <td>{form.net_ex_showroom_price}</td>
                </tr>
                <tr>
                    <td>Revised Financed Amount</td>
                    <td>{revised_form.revised_financed_amount}</td>
                </tr>
                <tr>
                    <td>EMI (Financing)</td>
                    <td>{quot_form.emi_financing}</td>
                </tr>
                <tr>
                    <td>Total EMI</td>
                    <td>{quot_form.total_emi}</td>
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
                
            <p>Best regards,</p>
            <p>{regards}</p>
        </body>
        </html>
        """
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
                
            <p>Best regards,</p>
            <p>{regards}</p>
        </body>
        </html>
        """
        return body


    def create_email_body_for_emp(self,user):
        form_url = f"{frappe.utils.get_url()}/car-indent-form-employee/new?employee_code={user.name}"
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
        bcc_emails = "rishi.hingad@merillife.com"
        subject = "You are Eligible for the Car Rental Service"
        body = self.create_email_body_for_emp(user)
        
        self.send(subject=subject, body=body, recipient_email=recipient_email) 
 
    def for_employee_to_reporting(self, user):
        doc = frappe.get_doc("Employee Master",user.reporting_head)
        print("------------[EMPLOYEE TO REPORTING]------------------:",doc)
        reporting_head_name = doc.employee_name
        recipient_email = doc.email_id
        subject =f"Car Rental Form Submitted by {user.employee_name} for Your Review"
        regards = f"{user.employee_name} (Employee)"
        content = f"""
        Dear {reporting_head_name},
        <br><br>
        We are pleased to inform you that {user.employee_name} has submitted the car rental form for your review.
        <br><br>Kindly check and take necessary action at your earliest convenience.<br><br>
        """
        link = f"{frappe.utils.get_url()}/reportnig_head_approval?id={user.name}"
        body = self.create_reporting_email(subject, content, regards,link)
        self.send(subject=subject, body=body, recipient_email=recipient_email)
        # self.send(subject=subject, body=body, recipient_email=recipient_email,bcc_emails=bcc_emails)

    def for_reporting_to_hr_team(self, user):
        recipient_email = emailMaster.hr_team_email        
        subject = "Car Rental Form Approved by Reporting Manager"
        regards = f"{user.reporting_head} (Reporting Manager)"
        remarks_by="reporting_head_remarks"
        content = f"""
        Dear Sir/Madam,
        <br><br>
        This is to notify you that the car rental form submitted by {user.employee_name} has been approved by the Reporting Manager.<br>
        """
        updated_by = user.reporting_head
        form = frappe.get_doc("Car Indent Form",user.name)
        body = self.create_email_body(form,user,subject, content,updated_by,remarks_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_hr_team_to_travel_desk(self, user):
        emailMaster = EmailMaster()
        recipient_email = emailMaster.travel_desk_email
        print(" for hr team to hr head------",recipient_email,"+++++++++++++++",emailMaster.travel_desk_email)
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
        <br><br>The Purchase Team has reviewed and approved the car rental form form submitted by {user.employee_name}.
        <br>{updated_by} have updated the quotation for the activity mentioned below:
        """
        body = self.create_email_body_revised(form,revised_form,user,subject, content,updated_by,remarks_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_purchase_head_to_finance_team(self, user):
        recipient_email = emailMaster.finance_team_email
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
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_finance_team_to_finance_head(self, user):
        # print("FInacne Team to Finance Head",user.employee_details)

        recipient_email = emailMaster.finance_head_email
        print("Finance head email---->",recipient_email)
        recipient_email2 = emailMaster.finance_head2_email
        print("Finance head 2 email---->",recipient_email2)

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
        self.send(subject=subject, body=body, recipient_email=recipient_email)
        self.send(subject=subject, body=body, recipient_email=recipient_email2)

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
        recipient_email = emailMaster.finance_team_email
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
        """
        form = frappe.get_doc("Purchase Team Form",user.name)
        body = self.create_reject_email_body(form,subject,content,remarks_by)
        self.send(subject,recipient_email,body)
       
    def for_finance_fill_quotation_acknowledgement(self, user,regards=""):
        recipient_email = emailMaster.finance_team_email
        subject = f"""Car Quotation Form Fiiled by {regards}"""
        
        
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
                <p>Dear Finance Teams,</p>
                <p>
                    The Quotation form has been submitted by {regards} for {user.employee_name} .
                    Please log in to your dashboard to review the form and proceed with the next steps.
                </p>
                <p>Best regards,</p>
                <p><strong>{regards}</strong></p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        self.send(subject=subject, body=body, recipient_email=recipient_email)
        
    # "-------------------------------------" EMAIL BODY FOR VENDOR "-------------------------------------"
    def create_vendor_email_for_car_quotation(self,compny_name,user,form,link):
        body = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                    }}
                    h2 {{
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
                </style>
            </head>
            <body>

                <h2>{compny_name} need to provide a Car Quotation for Meril based on the basic details mentioned below and as per our previous discussions.</h2>
                <table>
                    
                    <tbody>
                        <tr>
                            <td>Car Quotation For</td>
                            <td>{user.employee_name}</td>
                        </tr>
                        <tr>
                            <td>Vehicle Make & Model</td>
                            <td>{form.make} - {form.model}</td>
                        </tr>
                        <tr>
                            <td>Vehicle Engine</td>
                            <td>{form.engine}</td>
                        </tr>
                        <tr>
                            <td>Vehicle Colour</td>
                            <td>{form.colour}</td>
                        </tr>
                            
                    </tbody>
                </table>

                <p>
                    <a href="{link}" class="button">Fill Quotation Form</a>
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
    
    def create_vendor_email_for_Revised_car_quotation(self,compny_name,user,form,link):
        body = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                    }}
                    h2 {{
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
                </style>
            </head>
            <body>

                <h2>Dear {compny_name}</h2>
                <p>The quote received is on higher side so kindly provide a revised rental.</p>
                <p>Awaiting for your positive response!! </p>
                <p>
                    <a href="{link}" class="button">Fill Quotation Form</a>
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
    
    
    def for_car_quotation_ALD_EasyAssets_Xyz(self,user,payload):
        data = frappe.get_all("Vendor Master",fields="*")
        # print("-------------------------------[DATA]----------------------",data)
        car_indent_form = frappe.get_doc("Car Indent Form",user.name)  
        car_purchase_form = frappe.get_doc("Purchase Team Form",user.name)  
        emails_sent = []
        for company_detail in data:
            
            if payload.get("email_send_to") == "ALL" or company_detail.name == payload.get("email_send_to"):
               
                link = (
                        # f"http://127.0.0.1:8001/vendor-assets-quotation/new?"
                        f"{frappe.utils.get_url()}/vendor-assets-quotation/new?"
                        f"finance_company={company_detail.name}&"
                        f"employee_details={user.name}&"
                        f"location={car_indent_form.location}&"
                        f"kms={car_purchase_form.kilometers_per_year}&"
                        f"variant={car_indent_form.model}&"
                        f"accessory={car_purchase_form.revised_accessories}&"
                        f"discount_excluding_gst={car_purchase_form.revised_discount}&"
                        f"registration_charges={car_purchase_form.revised_registration_charges}&"
                        f"financed_amount={car_purchase_form.revised_financed_amount}&"
                        f"ex_showroom_amount={car_purchase_form.revised_ex_show_room_price}&"
                        f"ex_showroom_amount_net_of_discount={car_purchase_form.revised_net_ex_showroom_price}"
                        
                    )
                if payload.get("email_phase") == "Revised":
                    body = self.create_vendor_email_for_Revised_car_quotation(company_detail.name,user,car_indent_form,link)
                # elif payload.get("email_phase") == "Modified":
                #     body = self.create_vendor_email_for_Modified_car_quotation(company_detail.name,user,car_indent_form,link)
                else:
                    body = self.create_vendor_email_for_car_quotation(company_detail.name,user,car_indent_form,link)
                subject = f"Car Quotation for {company_detail.name}"
                self.send_quotations(subject=subject, body=body, recipient_email=company_detail.contact_email)   
                # frappe.msgprint(f"Email sent successfully")
                emails_sent.append(f"<li>{company_detail.name} &lt;{company_detail.contact_email}&gt;</li>")
        if emails_sent:
            frappe.msgprint(f"<b>Emails sent successfully to:</b><ul>{''.join(emails_sent)}</ul>")
        else:
            frappe.msgprint("No matching vendors found to send emails.")
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
        car_quot_form = frappe.get_doc("Car Quotation",quotation_id)  
        user = frappe.get_doc("Employee Master",car_quot_form.employee_details)  
        form_link = f"{frappe.utils.get_url()}/car-purchase-form/new?quotation_form={quotation_id}&user={user.name}&company={car_quot_form.finance_company}"
        body = self.create_selected_company_process(car_quot_form,user,form_link)
        subject = f"Car Onboard Process for {user.employee_name}"
        vendor =frappe.get_doc("Vendor Master",car_quot_form.finance_company)
        self.send(subject=subject, body=body, recipient_email=vendor.contact_email)

    # rejection for car quotation
    def for_reject_finance_head_to_vendor(self,quotation_id):
        car_quot_form = frappe.get_doc("Car Quotation",quotation_id)  #ismei se milega finance company
        vendor =frappe.get_doc("Vendor Master",car_quot_form.finance_company) #this is vendor details recipient humara
        user = frappe.get_doc("Employee Master",car_quot_form.employee_details)  #yaha se milega employee, jiska sirf naam chahiye
        recipient_email=vendor.contact_email
        subject=f"""{vendor.company_name} Car Quotation Rejected by Finance Head"""
        remarks_by="finance_head_remarks"
        cc_list=[emailMaster.finance_head2_email, emailMaster.finance_team_email]

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

    

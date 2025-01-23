
import smtplib
from email.message import EmailMessage
import frappe

class EmailServices:
    def __init__(self):
        self.smtp_server = "smtp.transmail.co.in"
        self.smtp_port = 587
        self.smtp_user = "emailapikey"
        self.smtp_password = "PHtE6r1cF7jiim598RZVsPW9QMCkMN96/uNveQUTt4tGWPNRTk1U+tgokDO0rRx+UKZAHKPInos5tbqZtbiHdz6/Z2dED2qyqK3sx/VYSPOZsbq6x00as1wSc0TfUILscdds1CLfutnYNA=="
        self.from_address = "noreply@merillife.com"
        
    def send(self,subject,recipient_email,body):
        try:
            msg = EmailMessage()
            msg.set_content(body, subtype="html")
            msg["Subject"] = subject
            msg["From"] = self.from_address
            msg["To"] = recipient_email
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                response = server.send_message(msg)
                print(response)

            frappe.msgprint(f"Email sent successfully to {recipient_email}.")

        except smtplib.SMTPException as smtp_error:
            frappe.throw(f"SMTP error occurred: {smtp_error}")

        except Exception as e:
            frappe.throw(f"Failed to send email: {str(e)}")
    
    
    
    # "-------------------------------------" EMAIL BODY "-------------------------------------"
    def create_email_body(self,form, 
                          user,
                          subject, 
                          content,
                          updated_by, 
                          regards=None, 
                          link="http://127.0.0.1:8003/login#login"):
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
            <thead>
                <tr>
                    <th>Field</th>
                    <th></th>
                </tr>
            </thead>
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
                    <td>Activity</td>
                    <td>Employee Vehicle Delivery </td>
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
            <p>{regards}</p>
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
                                regards=None, 
                                link="http://127.0.0.1:8003/login#login"):
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
            <thead>
                <tr>
                    <th>Field</th>
                    <th></th>
                </tr>
            </thead>
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
                    <td>Revised Net Ex-Showroom Price</td>
                    <td>{revised_form.revised_net_ex_showroom_price}</td>
                </tr>
                <tr>
                    <td>Activity</td>
                    <td>Employee Vehicle Delivery </td>
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
            <p>{regards}</p>
        </body>
        </html>
        """
        return body
    
    
    def create_email_body_for_emp(self,user):
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
                <p>We are pleased to inform you that you will be eligible for Company vehicle instead of Car Allowance. </p>
                <p>Please click on below link and fill the necessary details.</p>
                <p>
                    <a href="http://127.0.0.1:8003/car-indent-form/new?employee_code={user.name}" 
                    class="button">
                    Fill Car Rental Service Form
                    </a>
                </p>
                <p>You will make the best use of the opportunity offered to you and contribute substantially to 
                        the success of both yourself and the Organization. </p>
                <p>Wishing you all the best.  </p>
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
              
            {f'<a href="{link}" class="button">Click Here For Approve</a>' if link else ''}
            <p>Best regards,</p>
            <p>{regards}</p>
        </body>
        </html>
        """
        return body
    
    
 
    # "-------------------------------------" EMAIL SEND TO "-------------------------------------"
    
    def for_hr_team_to_employee(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "You are Eligible for the Car Rental Service"
        body = self.create_email_body_for_emp(user)
        
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_employee_to_reporting(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject =f"Car Rental Form for Submitted by {user.employee_name} for Your Review"
        regards = f"{user.employee_name} (Employee)"
        content = f"""
        Dear Reporting Manager,
        <br><br>
        We are pleased to inform you that {user.employee_name} has submitted the car rental form for your review.
        <br><br>Kindly check and take necessary action at your earliest convenience.<br><br>
        """
        link = f"http://127.0.0.1:8003/api/method/alms_app.api.emailsService.approve_car_indent_by_reporting?indent_form={user.name}"
        body = self.create_reporting_email(subject, content, regards,link)
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    
    def for_reporting_to_hr_team(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by Reporting Manager"
        regards = f"{user.reporting_head} (Reporting Manager)"
        content = f"""
        Dear HR Team,
        <br><br>
        This is to notify you that the car rental form submitted by {user.employee_name} has been approved by the Reporting Manager.<br>
        """
        updated_by = user.reporting_head
        form = frappe.get_doc("Car Indent Form",user.name)
        body = self.create_email_body(form,user,subject, content,updated_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_hr_team_to_hr_head(self, user):
        pass
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by HR Team"
        regards = "HR Team"
        updated_by = "Mrs. Ami Rughani"
        form = frappe.get_doc("Car Indent Form",user.name)
        content = f"""
        Dear HR Head,
        <br><br>The HR team has reviewed and approved the car rental form submitted by {user.employee_name}.
        <br>
        {updated_by} have sent the form for the activity mentioned below:
        """
        body = self.create_email_body(form,user,subject, content,updated_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_hr_head_to_purchase_team(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by HR Head"
        regards = "HR Head"
        updated_by = "Mr. Hemchandra Panjikar"
        form = frappe.get_doc("Car Indent Form",user.name)
        content = f"""
        Dear Purchase Team,
        <br><br>
        The HR Head has approved the car rental form submitted by {user.employee_name}.
        <br>
        {updated_by} have approved the request for the activity mentioned below:
        """
        body = self.create_email_body(form,user,subject, content,updated_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)

 
    def for_purchase_team_to_purchase_head(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by Purchase Team"
        regards = "Purchase Team"
        updated_by = "Mr. Tarun Patel"
        form = frappe.get_doc("Car Indent Form",user.name)
        revised_form = frappe.get_doc("Purchase Team Form",user.name)
        content = f"""
        Dear Purchase Head,
        <br><br>The Purchase Team has reviewed and approved the car rental form form submitted by {user.employee_name}.
        <br>{updated_by} have updated the quotation for the activity mentioned below:
        """
        body = self.create_email_body_revised(form,revised_form,user,subject, content,updated_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)

# Done here
    def for_purchase_head_to_finance_team(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by Purchase Head"
        regards = "Purchase Head"
        form = frappe.get_doc("Car Indent Form",user.name)
        revised_form = frappe.get_doc("Purchase Team Form",user.name)
        updated_by = "Mr. Sumesh Nair"
        content = f"""
        Dear Finance Team,
        <br><br>The Purchase Head has approved the car rental form for {user.employee_name}.
        <br>{updated_by} have approved the request for the activity mentioned below:
        """
        body = self.create_email_body_revised(form,revised_form,user,subject, content,updated_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_finance_team_to_finance_head(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by Finance Team"
        regards ="Finance Team"
        form = frappe.get_doc("Car Indent Form",user.name)
        revised_form = frappe.get_doc("Purchase Team Form",user.name)
        updated_by = "Mr. Sumesh Nair"
        content = f"""
        Dear Finance Team,
        <br><br>The Finance Team has approved the car rental form for {user.employee_name}.
        <br>{updated_by} have approved the request for the activity mentioned below:
        """
        body = self.create_email_body_revised(form,revised_form,user,subject, content,updated_by,regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_finance_head_to_accounts_team(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Final Approval"
        regards = "Finance Head"
        content = f"Dear Accounts Team,<br><br>The car rental form submitted by {user.employee_name} has been approved at all levels and is now ready for processing. Kindly proceed with the final steps.<br><br>"
        
        body = self.create_email_body(subject, content, regards)
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

                <p class="company-name">Meril</p>

                <h2>{compny_name} - Car Quotation Form</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Field</th>
                            <th></th>
                        </tr>
                    </thead>
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
    
    
    
    def for_car_quotation_ALD_EasyAssets_Xyz(self,user):
        data = [
            {
            "name":"Easy Assets",
            "email":"jaykumar.patel@merillife.com"
            }  
            ]
        form = frappe.get_doc("Car Indent Form",user.name)
        for i in data:
            link = f"http://127.0.0.1:8003/vendor-assets-quotation/new?finance_company={i.get('name')}&employee_details={user.name}"
            body = self.create_vendor_email_for_car_quotation(i.get('name'),user,form,link)
            subject = f"Car Quotation"
            self.send(subject=subject, body=body, recipient_email=i.get('email'))
            
        
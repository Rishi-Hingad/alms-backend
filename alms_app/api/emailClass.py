
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
    
    def create_email_body(self, subject, content, regards=None, link="http://127.0.0.1:8003/login#login"):
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
              
            {f'<a href="{link}" class="button">Click Here</a>' if link else ''}
            <p>Best regards,</p>
            <p>{regards}</p>
        </body>
        </html>
        """
        return body


    def for_hr_team_to_employee(self, user):
        link = f"http://127.0.0.1:8003/car-indent-form/new?employee_code={user.name}"
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "You are Eligible for the Car Rental Service"
        regards = "HR Team"
        content = f"Dear {user.employee_name},<br><br>We are pleased to inform you that you are eligible for the Car Rental Service.<br><br>Please click on the link below to access the car rental form and complete the process:<br><br>"
        
        body = self.create_email_body(subject, content, regards, link)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_employee_to_reporting(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Submitted for Your Review"
        regards = f"{user.employee_name} (Employee)"
        content = f"Dear Reporting Manager,<br><br>We are pleased to inform you that {user.employee_name} has submitted the car rental form for your review.<br><br>Kindly check and take necessary action at your earliest convenience.<br><br>"
        
        body = self.create_email_body(subject, content, regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_reporting_to_hr_team(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by Reporting Manager"
        regards = f"{user.reporting_head} (Reporting Manager)"
        content = f"Dear HR Team,<br><br>This is to notify you that the car rental form submitted by {user.employee_name} has been approved by the Reporting Manager.<br><br>It now requires your approval.<br><br>"
        
        body = self.create_email_body(subject, content, regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_hr_team_to_hr_head(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by HR Team"
        regards = "HR Team"
        content = f"Dear HR Head,<br><br>The HR team has reviewed and approved the car rental form submitted by {user.employee_name}. We now seek your approval to proceed further.<br><br>"
        
        body = self.create_email_body(subject, content, regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_hr_head_to_purchase_team(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by HR Head"
        regards = "HR Head"
        content = f"Dear Purchase Team,<br><br>The HR Head has approved the car rental form submitted by {user.employee_name}. Kindly review and provide your approval.<br><br>"
        
        body = self.create_email_body(subject, content, regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_purchase_team_to_purchase_head(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by Purchase Team"
        regards = "Purchase Team"
        content = f"Dear Purchase Head,<br><br>The Purchase Team has reviewed and approved the car rental form form submitted by {user.employee_name}. It now requires your final approval to proceed further.<br><br>"
        
        body = self.create_email_body(subject, content, regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_purchase_head_to_finance_team(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by Purchase Head"
        regards = "Purchase Head"
        content = f"Dear Finance Team,<br><br>The Purchase Head has approved the car rental form for {user.employee_name}. Please review and process it further.<br><br>"
        
        body = self.create_email_body(subject, content, regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_finance_team_to_finance_head(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Approved by Finance Team"
        regards = "Finance Team"
        content = f"Dear Finance Head,<br><br>The Finance Team has reviewed and approved the car rental form submitted by {user.employee_name}. Your final approval is required to proceed with the process.<br><br>"
        
        body = self.create_email_body(subject, content, regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


    def for_finance_head_to_accounts_team(self, user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Final Approval"
        regards = "Finance Head"
        content = f"Dear Accounts Team,<br><br>The car rental form submitted by {user.employee_name} has been approved at all levels and is now ready for processing. Kindly proceed with the final steps.<br><br>"
        
        body = self.create_email_body(subject, content, regards)
        self.send(subject=subject, body=body, recipient_email=recipient_email)


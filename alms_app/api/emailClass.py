
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
    
    def for_hr_team_to_employee(self, user):
        link = f"http://127.0.0.1:8003/car-indent-form/new?employee_code={user.name}"
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Eligibility for Car Rental Service"
        body = f"""
        Dear {user.employee_name},

        We are pleased to inform you that you are eligible for the Car Rental Service. 
        Please click on the link below to access the car rental form and complete the process:

        {link}

        If you have any questions or require assistance, feel free to contact the HR team.

        Best regards,  
        HR Team
        """
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_employee_to_reporting(self,user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form Submission"
        body = f"""
        Dear Reporting Manager,

        We are pleased to inform you that I have submitted the car rental form for your review. Kindly check and take necessary action at your earliest convenience.

        Approval Link: []

        Best regards,
        [Your Name]
        """
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_reporting_to_hr_team(self,user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form: Reporting Manager Approval"
        body = f"""
        Dear HR Team,

        This is to notify you that the car rental form submitted by the employee has been approved by the Reporting Manager. It now requires your approval.

        Approval Link: [Insert Approval Link]

        Best regards,
        Reporting Manager
        """
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_hr_team_to_hr_head(self,user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form: HR Approval"
        body = f"""
        Dear HR Head,

        The HR team has reviewed and approved the car rental form submitted by the employee. We now seek your final approval to proceed further.

        Approval Link: [Insert Approval Link]

        Best regards,
        HR Team
        """
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_hr_head_to_purchase_team(self,user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form: HR Head Approval"
        body = f"""
        Dear Purchase Team,

        We are pleased to inform you that the HR Head has approved the car rental form submitted by the employee. Kindly review and provide your approval.

        Approval Link: [Insert Approval Link]

        Best regards,
        HR Head
        """
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_purchase_team_to_purchase_head(self,user):
        recipient_email =  "jaykumar.patel@merillife.com"
        subject = "Car Rental Form: Purchase Team Approval"
        body = f"""
        Dear Purchase Head,

        The Purchase Team has reviewed and approved the car rental form. It now requires your final approval to proceed further.

        Approval Link: [Insert Approval Link]

        Best regards,
        Purchase Team
        """
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_purchase_head_to_finance_team(self,user):
        recipient_email =  "jaykumar.patel@merillife.com"
        subject = "Car Rental Form: Purchase Head Approval"
        body = f"""
        Dear Finance Team,

        The Purchase Head has approved the car rental form for the employee. Please review and process it further.

        Approval Link: [Insert Approval Link]

        Best regards,
        Purchase Head
        """
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_finance_team_to_finance_head(self,user):
        recipient_email = "jaykumar.patel@merillife.com"
        subject = "Car Rental Form: Finance Team Approval"
        body = f"""
        Dear Finance Head,

        The Finance Team has reviewed and approved the car rental form. Your final approval is required to proceed with the process.

        Approval Link: [Insert Approval Link]

        Best regards,
        Finance Team
        """
        self.send(subject=subject, body=body, recipient_email=recipient_email)

    def for_finance_head_to_accounts_team(self,user):
        recipient_email = None
        subject = "Car Rental Form: Final Approval"
        body = f"""
        Dear Accounts Team,

        The car rental form has been approved at all levels and is now ready for processing. Kindly proceed with the final steps.

        Best regards,
        Final Approver
        """
        self.send(subject=subject, body=body, recipient_email=recipient_email)

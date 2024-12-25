# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

import smtplib
from email.message import EmailMessage
from frappe.model.document import Document
from frappe.utils import now
import frappe

class EmployeeMaster(Document):
    def send_email(self):
        smtp_server = "smtp.transmail.co.in"
        smtp_port = 587
        smtp_user = "emailapikey"
        smtp_password = "PHtE6r1cF7jiim598RZVsPW9QMCkMN96/uNveQUTt4tGWPNRTk1U+tgokDO0rRx+UKZAHKPInos5tbqZtbiHdz6/Z2dED2qyqK3sx/VYSPOZsbq6x00as1wSc0TfUILscdds1CLfutnYNA=="
        from_address = "noreply@merillife.com"

        try:
            recipient_email = self.email_id
            if not recipient_email:
                frappe.throw("Email ID is required to send an email.")
            subject = "Welcome to Our Company"
            body = f"""
                <body style="font-family: Arial, sans-serif; line-height: 1.5;">
                    <p>Dear {self.employee_name},</p>
                    <p>We are pleased to inform you that you are eligible for the Car Rental Service.</p>
                    <p>Click on the link below to fill the form:</p>
                    <p>
                        <a href="http://127.0.0.1:8003/car-indent-form/new?employee_code={self.name}" 
                        style="color: #007BFF; text-decoration: none;">
                        Car Rental Service Form
                        </a>
                    </p>
                    <br>
                    <p>Best Regards,<br>Your HR Team</p>
                </body>
                """
            msg = EmailMessage()
            msg.set_content(body, subtype="html")
            msg["Subject"] = subject
            msg["From"] = from_address
            msg["To"] = recipient_email

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(smtp_user, smtp_password)
                response = server.send_message(msg)
                print(response)

            self.status = "Sent"
            self.email_sent_date = now()
            self.save()
            frappe.db.commit()

            frappe.msgprint(f"Email sent successfully to {recipient_email}.")

        except smtplib.SMTPException as smtp_error:
            frappe.throw(f"SMTP error occurred: {smtp_error}")

        except Exception as e:
            frappe.throw(f"Failed to send email: {str(e)}")


@frappe.whitelist()
def send_email(name):
    employee = frappe.get_doc("Employee Master", name)
    employee.send_email()


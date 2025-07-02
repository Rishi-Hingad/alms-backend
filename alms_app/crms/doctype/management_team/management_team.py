# Copyright (c) 2025, Rishi Hingad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ManagementTeam(Document):
    def validate(self):
        self.full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        if self.create_user:
            if frappe.db.exists("User", self.email_id):
                frappe.throw(_(f"A user already exists with this email: {self.email_id}"))
            self.create_user_if_needed()
            self.create_user = 1

    def create_user_if_needed(self):
        if self.create_user and self.email_id:
            if not frappe.db.exists("User", self.email_id):
                safe_first_name = self.first_name.strip().capitalize() if self.first_name else "User"
                password = f"{safe_first_name}@123"

                new_user = frappe.new_doc("User")
                new_user.first_name = self.first_name
                new_user.last_name = self.last_name
                new_user.email = self.email_id
                new_user.full_name = self.full_name
                new_user.send_welcome_email = 0
                new_user.new_password = password

                if self.role:
                    new_user.append("roles", {"role": self.role})

                new_user.insert(ignore_permissions=True)

                self.send_credentials_email(self.email_id, password)

                frappe.msgprint(f"User created for: {self.email_id}")
            else:
                frappe.msgprint(f"User already exists: {self.email_id}")

    def send_credentials_email(self, email, password):
        subject = "Your Meril ERP Login Credentials"
        message = f"""
        Dear {self.full_name or 'User'},

        Your account has been created successfully. Please find your login credentials below:

        🔐 **Username:** {email}  
        🔑 **Password:** {password}

        You can log in at: [https://carleasing-dev.bilakhiagroup.com/login#login](https://carleasing-dev.bilakhiagroup.com/login#login)

        Please change your password after first login.

        Regards,  
        ALMS Admin
        """

        try:
            frappe.sendmail(
                recipients=[email],
                subject=subject,
                message=message
            )
            frappe.msgprint(f"Credentials sent to {email}")
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Failed to send user creation email")
            frappe.msgprint(f"Failed to send credentials to {email}")

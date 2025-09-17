import frappe
from frappe.model.document import Document
from frappe import _

class ManagementTeam(Document):
    def validate(self):
        self.full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        if self.create_user:
            if frappe.db.exists("User", self.email_id):
                self.update_existing_user()
            else:
                self.create_user_if_needed()
            self.create_user = 1

    def create_user_if_needed(self):
        if self.create_user and self.email_id:
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

            if self.module:
                new_user.module_profile = self.module

            new_user.insert(ignore_permissions=True)

            self.send_credentials_email(self.email_id, password)
            frappe.msgprint(f"User created for: {self.email_id}")

    def update_existing_user(self):
        """Sync role and module_profile if User already exists"""
        user = frappe.get_doc("User", self.email_id)

        if self.module:
            user.module_profile = self.module

        if self.role:
            user.roles = []
            user.append("roles", {"role": self.role})

        user.save(ignore_permissions=True)
        frappe.msgprint(f"User updated with latest role/module_profile: {self.email_id}")

    def send_credentials_email(self, email, password):
        frontend_url = frappe.get_conf().get("Frontend_URL") or "https://ri-sharedservices.bilakhiagroup.com/login#login"
        subject = "Your Meril Shared Services Login Credentials"
        message = f"""
            <p>Dear {self.full_name or 'User'},</p>

            <p>Your account has been created successfully. Please find your login credentials below:</p>

            <p>🔐 <strong>Username:</strong> {email}<br>
            🔑 <strong>Password:</strong> {password}</p>

            <p>
                <a href="{frontend_url}/login#login" 
                style="display:inline-block;padding:10px 20px;margin:10px 0;
                        background-color:#1a73e8;color:#fff;text-decoration:none;
                        border-radius:5px;font-weight:bold;">
                Login to Portal
                </a>
            </p>

            <p>Please change your password after first login.</p>

            <p>Regards,<br>
            ALMS Admin</p>
            """
        try:
            frappe.sendmail(
                recipients=[email],
                subject=subject,
                message=message,
                bcc=["rishi.hingad@merillife.com"]
            )
            frappe.msgprint(f"Credentials sent to {email}")
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Failed to send user creation email")
            frappe.msgprint(f"Failed to send credentials to {email}")

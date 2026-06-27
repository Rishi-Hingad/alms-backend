import frappe
from frappe.model.document import Document
from frappe import _

class CarIndentForm(Document):
    def before_insert(self):
        if getattr(frappe.flags, "in_web_form", False):
            self.is_submitted = 1

    def validate(self):
        self.ex_showroom_price = self.ex_showroom_price or 0
        self.discount = self.discount or 0
        self.tcs = self.tcs or 0
        self.registration_charges = self.registration_charges or 0
        self.accessories = self.accessories or 0

        self.net_ex_room_price = self.ex_showroom_price - self.discount + self.tcs

        self.financed_amount = self.net_ex_room_price + self.registration_charges + self.accessories

    def after_insert(self):
        if getattr(frappe.flags, "in_web_form", False):
            try:
                from lease_app.api.emailsService import email_sender
                email_sender(name=self.employee_code, email_send_to="To HR (New Request)", car_indent_form_name=self.name)
                email_sender(name=self.employee_code, email_send_to="To Reporting", car_indent_form_name=self.name)
            except Exception as e:
                frappe.log_error(f"Error sending HR email on web form submit: {str(e)}")



@frappe.whitelist()
def check_purchase_form_exists(employee_code):
    return frappe.db.exists("Purchase Form", employee_code)

@frappe.whitelist()
def can_view_car_indent_list():
    """Check if the current user has the ALMS User role"""
    user = frappe.session.user
    
    if user == "Administrator":
        return True
    
    has_role = frappe.db.exists("Has Role", {
        "parent": user,
        "role": "ALMS User"
    })
    
    return bool(has_role)

@frappe.whitelist()
def force_delete(docname):
    if frappe.session.user != "Administrator":
        frappe.throw("Only Administrators can force delete Car Indent Forms.")
        
    # Find and delete all linked Approval Entries first to avoid LinkExistsError
    approval_entries = frappe.get_all("Approval Entry", filters={
        "applied_to_doctype": "Car Indent Form",
        "record": docname
    })
    
    for entry in approval_entries:
        frappe.delete_doc("Approval Entry", entry.name, ignore_permissions=True, force=True)
        
    # Now safely delete the Car Indent Form
    frappe.delete_doc("Car Indent Form", docname, ignore_permissions=True, force=True)
    
    return True
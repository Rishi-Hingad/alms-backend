import frappe
from frappe.model.document import Document

class CarIndentForm(Document):    
    def validate(self):
        self.ex_showroom_price = self.ex_showroom_price or 0
        self.discount = self.discount or 0
        self.tcs = self.tcs or 0
        self.registration_charges = self.registration_charges or 0
        self.accessories = self.accessories or 0

        self.net_ex_room_price = self.ex_showroom_price - self.discount + self.tcs

        self.financed_amount = self.net_ex_room_price + self.registration_charges + self.accessories

@frappe.whitelist(allow_guest=True)
def management(current_frappe_user):
    designation_record = frappe.get_value("Management Team", {"email_id": current_frappe_user}, ["designation"], as_dict=True)
    
    if designation_record:
        return designation_record.designation
    else:
        return None
    
@frappe.whitelist()
def daily_pending_indent_email_reminder():
    pending_docs = frappe.get_all("Car Indent Form", filters=[
        ["status", "!=", "Approved"]
    ], fields=["name", "employee", "reporting_head_approval", "hr_approval", "travel_desk_approval", "hr_head_approval"])

    for doc in pending_docs:
        pending_stage = None
        email_to = None

        if doc.reporting_head_approval == "Pending":
            pending_stage = "reporting_head_approval"
            email_to = get_email_by_designation("Reporting Head")
        elif doc.hr_approval == "Pending":
            pending_stage = "hr_approval"
            email_to = get_email_by_designation("HR")
        elif doc.travel_desk_approval == "Pending":
            pending_stage = "travel_desk_approval"
            email_to = get_email_by_designation("Travel Desk")
        elif doc.hr_head_approval == "Pending":
            pending_stage = "hr_head_approval"
            email_to = get_email_by_designation("HR Head")

        if email_to and pending_stage:
            subject = f"Approval Pending - Car Indent Form: {doc.name}"
            message = f"""
                <p>Dear Approver,</p>
                <p>You have a pending car indent form awaiting your action for the <strong>{pending_stage.replace('_', ' ').title()}</strong> stage.</p>
                <p>Please <a href="{frappe.utils.get_url()}/app/car-indent-form/{doc.name}">click here</a> to approve or reject the request.</p>
                <p>Thank you,<br/>Meril Travel Desk</p>
            """
            frappe.sendmail(recipients=email_to, subject=subject, message=message)

def get_email_by_designation(designation):
    # Assuming you have Employee or User records tagged by designation
    user = frappe.db.get_value("User", {"designation": designation, "enabled": 1}, "email")
    return user



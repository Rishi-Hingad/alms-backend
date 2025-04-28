# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


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


# Copyright (c) 2026, Rishi Hingad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class PurchaseForm(Document):
    def validate(self):
        # Calculate revised fields if applicable
        ex_show_room = flt(self.revised_ex_show_room_price)
        discount = flt(self.revised_discount)
        tcs = flt(self.revised_tcs)
        reg_charges = flt(self.revised_registration_charges)
        accessories = flt(self.revised_accessories)

        if ex_show_room or discount or tcs or reg_charges or accessories:
            self.revised_net_ex_showroom_price = ex_show_room - discount + tcs
            self.revised_financed_amount = self.revised_net_ex_showroom_price + reg_charges + accessories

        if self.kilometers_per_year and self.tenure_in_years:
            self.total_kilometers = flt(self.kilometers_per_year) * flt(self.tenure_in_years)
        else:
            self.total_kilometers = 0

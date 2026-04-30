# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PurchaseTeamForm(Document):
	def validate(self):
		self.kilometers_per_year = self.kilometers_per_year or 0
		self.tenure_in_years = self.tenure_in_years or 0
		self.revised_ex_show_room_price = self.revised_ex_show_room_price or 0
		self.revised_tcs = self.revised_tcs or 0
		self.revised_registration_charges = self.revised_registration_charges or 0
		self.revised_accessories = self.revised_accessories or 0
		self.revised_discount = self.revised_discount or 0

		self.total_kilometers = self.kilometers_per_year * self.tenure_in_years

		self.revised_net_ex_showroom_price = self.revised_ex_show_room_price - self.revised_discount + self.revised_tcs

		self.revised_financed_amount = self.revised_net_ex_showroom_price + self.revised_registration_charges + self.revised_accessories
		self.set_overall_status()


	def set_overall_status(self):
		pt = self.purchase_team_status
		ph = self.purchase_head_status

		if pt == "Rejected" or ph == "Rejected":
			self.status = "Rejected"
		elif pt == "Approved" and ph == "Approved":
			self.status = "Approved"
		else:
			self.status = "Pending"
# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import math
class CompanyandEmployeeDeduction(Document):
    def validate(self):
        # Ensure that all fields are initialized
        self.interest_rate = self.interest_rate or 0
        self.tenure = self.tenure or 0
        self.ex_showroom_amount_net_of_discount = self.ex_showroom_amount_net_of_discount or 0
        self.registration_charges = self.registration_charges or 0
        self.residual_value = self.residual_value or 0
        self.gst = self.gst or 0

        # Calculate financed amount
        self.financed_amount = self.ex_showroom_amount_net_of_discount + self.registration_charges - self.residual_value

        # Calculate EMI using the PMT formula logic (Excel-style)
        self.emi_financing = self.calculate_emi(self.financed_amount, self.interest_rate, self.tenure, self.gst)

        # Additional fields
        self.finance_emi_road_tax = self.calculate_emi_road_tax(self.emi_financing, self.registration_charges, self.tenure)
        self.gst_and_cess = self.calculate_gst_and_cess(self.finance_emi_road_tax)

    def calculate_emi(self, financed_amount, interest_rate, tenure, gst):
        # Monthly interest rate (C6/12)
        monthly_rate = (interest_rate / 100) / 12

        # EMI calculation using the PMT formula logic (Excel-style)
        emi = -(
            (financed_amount * monthly_rate * math.pow(1 + monthly_rate, tenure)) /
            (math.pow(1 + monthly_rate, tenure) - 1)
        ) + (gst / tenure)  # Subtract GST per month
        
        return round(emi, 2)

    def calculate_emi_road_tax(self, emi, registration_charges, tenure):
        # Calculate the road tax (financing EMI without GST)
        return emi - (registration_charges / tenure)

    def calculate_gst_and_cess(self, finance_emi_road_tax):
        # Calculate GST and cess (using a fixed GST interest rate of 45%)
        gst_interest_rate = 0.45
        return finance_emi_road_tax * gst_interest_rate

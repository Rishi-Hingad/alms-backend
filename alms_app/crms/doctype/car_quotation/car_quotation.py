# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

import frappe
from openpyxl import load_workbook
from frappe.model.document import Document

class CarQuotation(Document):

    def upload_data(self):
        # Ensure the file is attached and accessible
        if not self.attach_file:
            frappe.throw("No file attached for upload.")
        
        try:
            # Fetch the file from the system using the file URL
            _file = frappe.get_doc("File", {"file_url": self.attach_file})  # Replace 'attach_file' with actual file URL field
            filename = _file.get_full_path()
            
            # Parse the Excel file
            data = self.parse_excel(filename)

            # Populate the Car Quotation fields with parsed data
            self.populate_car_quotation_fields(data)
        except Exception as e:
            frappe.throw(f"Error while uploading file: {str(e)}")

    def parse_excel(self, file_path):
        # Load the workbook and get the active sheet
        wb = load_workbook(file_path)
        sheet = wb.active
        
        # List to hold parsed data
        data = []

        # Assuming the first row contains headers, iterate through the rows
        for row in sheet.iter_rows(min_row=2, values_only=True):  # Start from row 2 to skip headers
            # Ensure row has the correct number of columns (29 in this case)
            if len(row) >= 29:
                row_data = {
                    'finance_company': row[0],
                    'employee_details': row[1],
                    'location': row[2],
                    'kms': row[3],
                    'variant': row[4],
                    'quote': row[5],
                    'interest_rate': row[6],
                    'tenure': row[7],
                    'base_price_excluding_gst': row[8],
                    'gst': row[9],
                    'ex_showroom_amount': row[10],
                    'accessory': row[11],
                    'discount_excluding_gst': row[12],
                    'base_price_less_discounts': row[13],
                    'total_discount': row[14],
                    'ex_showroom_amount_net_of_discount': row[15],
                    'registration_charges': row[16],
                    'residual_value': row[17],
                    'percent': row[18],
                    'financed_amount': row[19],
                    'emi_financing': row[20],
                    'finance_emi_road_tax': row[21],
                    'gst_and_cess': row[22],
                    'insurance': row[23],
                    'fleet_management_repairs_and_tyres': row[24],
                    'assist_service': row[25],
                    'pickup_and_drop': row[26],
                    'std_relief_car_non_accident': row[27],
                    'gst_on_fms': row[28],
                    'total_emi': row[29]
                }
                data.append(row_data)

        return data

    def populate_car_quotation_fields(self, data):
        # Map the parsed data to the fields of Car Quotation
        for row in data:
            self.finance_company = row['finance_company']
            self.employee_details = row['employee_details']
            self.location = row['location']
            self.kms = row['kms']
            self.variant = row['variant']
            self.quote = row['quote']
            self.interest_rate = row['interest_rate']
            self.tenure = row['tenure']
            self.base_price_excluding_gst = row['base_price_excluding_gst']
            self.gst = row['gst']
            self.ex_showroom_amount = row['ex_showroom_amount']
            self.accessory = row['accessory']
            self.discount_excluding_gst = row['discount_excluding_gst']
            self.base_price_less_discounts = row['base_price_less_discounts']
            self.total_discount = row['total_discount']
            self.ex_showroom_amount_net_of_discount = row['ex_showroom_amount_net_of_discount']
            self.registration_charges = row['registration_charges']
            self.residual_value = row['residual_value']
            self.percent = row['percent']
            self.financed_amount = row['financed_amount']
            self.emi_financing = row['emi_financing']
            self.finance_emi_road_tax = row['finance_emi_road_tax']
            self.gst_and_cess = row['gst_and_cess']
            self.insurance = row['insurance']
            self.fleet_management_repairs_and_tyres = row['fleet_management_repairs_and_tyres']
            self.assist_service = row['assist_service']
            self.pickup_and_drop = row['pickup_and_drop']
            self.std_relief_car_non_accident = row['std_relief_car_non_accident']
            self.gst_on_fms = row['gst_on_fms']
            self.total_emi = row['total_emi']

        # Save the changes
        self.save(ignore_permissions=True)

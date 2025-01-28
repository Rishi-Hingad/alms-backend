# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

import frappe
from openpyxl import load_workbook
from frappe.model.document import Document

class CarQuotation(Document):
    pass

#     def upload_data(self):
#         # Ensure the file is attached and accessible
#         if not self.attach_file:
#             frappe.throw("No file attached for upload.")
        
#         try:
#             # Fetch the file from the system using the file URL
#             _file = frappe.get_doc("File", {"file_url": self.attach_file})  # Replace 'attach_file' with actual file URL field
#             filename = _file.get_full_path()
            
#             # Parse the Excel file
#             data = self.parse_excel(filename)

#             # Populate the Car Quotation fields with parsed data
#             self.populate_car_quotation_fields(data)
#         except Exception as e:
#             frappe.throw(f"Error while uploading file: {str(e)}")

#     def parse_excel(self, file_path):
#         # Load the workbook and get the active sheet
#         wb = load_workbook(file_path)
#         sheet = wb.active
        
#         # List to hold parsed data
#         data = []

#         # Assuming the first row contains headers, iterate through the rows
#         for row in sheet.iter_rows(min_row=2, values_only=True):  # Start from row 2 to skip headers
#             # Ensure row has the correct number of columns (29 in this case)
#             if len(row) >= 29:
#                 row_data = {
#                     'finance_company': row[0],
#                     'employee_details': row[1],
#                     'location': row[2],
#                     'kms': row[3],
#                     'variant': row[4],
#                     'quote': row[5],
#                     'interest_rate': row[6],
#                     'tenure': row[7],
#                     'base_price_excluding_gst': row[8],
#                     'gst': row[9],
#                     'ex_showroom_amount': row[10],
#                     'accessory': row[11],
#                     'discount_excluding_gst': row[12],
#                     'base_price_less_discounts': row[13],
#                     'total_discount': row[14],
#                     'ex_showroom_amount_net_of_discount': row[15],
#                     'registration_charges': row[16],
#                     'residual_value': row[17],
#                     'percent': row[18],
#                     'financed_amount': row[19],
#                     'emi_financing': row[20],
#                     'finance_emi_road_tax': row[21],
#                     'gst_and_cess': row[22],
#                     'insurance': row[23],
#                     'fleet_management_repairs_and_tyres': row[24],
#                     'assist_service': row[25],
#                     'pickup_and_drop': row[26],
#                     'std_relief_car_non_accident': row[27],
#                     'gst_on_fms': row[28],
#                     'total_emi': row[29]
#                 }
#                 data.append(row_data)

#         return data

#     def populate_car_quotation_fields(self, data):
#         # Map the parsed data to the fields of Car Quotation
#         for row in data:
#             self.finance_company = row['finance_company']
#             self.employee_details = row['employee_details']
#             self.location = row['location']
#             self.kms = row['kms']
#             self.variant = row['variant']
#             self.quote = row['quote']
#             self.interest_rate = row['interest_rate']
#             self.tenure = row['tenure']
#             self.base_price_excluding_gst = row['base_price_excluding_gst']
#             self.gst = row['gst']
#             self.ex_showroom_amount = row['ex_showroom_amount']
#             self.accessory = row['accessory']
#             self.discount_excluding_gst = row['discount_excluding_gst']
#             self.base_price_less_discounts = row['base_price_less_discounts']
#             self.total_discount = row['total_discount']
#             self.ex_showroom_amount_net_of_discount = row['ex_showroom_amount_net_of_discount']
#             self.registration_charges = row['registration_charges']
#             self.residual_value = row['residual_value']
#             self.percent = row['percent']
#             self.financed_amount = row['financed_amount']
#             self.emi_financing = row['emi_financing']
#             self.finance_emi_road_tax = row['finance_emi_road_tax']
#             self.gst_and_cess = row['gst_and_cess']
#             self.insurance = row['insurance']
#             self.fleet_management_repairs_and_tyres = row['fleet_management_repairs_and_tyres']
#             self.assist_service = row['assist_service']
#             self.pickup_and_drop = row['pickup_and_drop']
#             self.std_relief_car_non_accident = row['std_relief_car_non_accident']
#             self.gst_on_fms = row['gst_on_fms']
#             self.total_emi = row['total_emi']

#         # Save the changes
#         self.save(ignore_permissions=True)


import pandas as pd 
from frappe.utils.file_manager import save_file

@frappe.whitelist(allow_guest=True)
def process_uploaded_file(file):
    file = frappe.request.files['file']  # Access the uploaded file
    file_doc = save_file(file.filename, file.read(), dt=None, dn=None, folder="Home", is_private=0)
    return {"file_path": file_doc.file_url}
    # if 'file' not in frappe.request.files:
    #     frappe.throw("No file uploaded")
        
    # uploaded_file = frappe.request.files['file']
    # file_name = uploaded_file.filename
    # if not file_name.endswith(('.xls', '.xlsx')):
    #     frappe.throw("Please upload a valid Excel file (.xls or .xlsx)")

    # file_path = frappe.utils.get_site_path('private', 'temp', uploaded_file.filename)
    # with open(file_path, 'wb') as f:
    #     f.write(uploaded_file.read())

    # print("file_path------------------------------ ")
    # try:
    #     file_doc = frappe.get_doc("File", {"file_url": file_url})
    #     file_path = file_doc.get_full_path()

    #     if file_path.endswith(".xlsx") or file_path.endswith(".xls"):
    #         data_frame = pd.read_excel(file_path)
    #     elif file_path.endswith(".csv"):
    #         data_frame = pd.read_csv(file_path)
    #     else:
    #         frappe.throw("Unsupported file format. Please upload an Excel or CSV file.")

    #     for index, row in data_frame.iterrows():
    #         car_quotation_item = frappe.get_doc({
    #             "doctype": "Car Quotation",
    #             "finance_company": row.get("finance_company"),
    #             "accessory": row.get("accessory"),
    #             "gst_and_cess": row.get("gst_and_cess"),
    #             "employee_details": row.get("employee_details"),
    #             "discount_excluding_gst": row.get("discount_excluding_gst"),
    #             "insurance": row.get("insurance"),
    #             "location": row.get("location"),
    #             "base_price_less_discounts": row.get("base_price_less_discounts"),
    #             "fleet_management_repairs_and_tyres": row.get("fleet_management_repairs_and_tyres"),
    #             "kms": row.get("kms"),
    #             "total_discount": row.get("total_discount"),
    #             "24x7_assist": row.get("24x7_assist"),
    #             "variant": row.get("variant"),
    #             "ex_showroom_amount_net_of_discount": row.get("ex_showroom_amount_net_of_discount"),
    #             "pickup_and_drop": row.get("pickup_and_drop"),
    #             "quote": row.get("quote"),
    #             "registration_charges": row.get("registration_charges"),
    #             "interest_rate": row.get("interest_rate"),
    #             "residual_value_percent": row.get("residual_value_percent"),
    #             "std_relief_car_non_accdt": row.get("std_relief_car_non_accdt"),
    #             "tenure": row.get("tenure"),
    #             "financed_amount": row.get("financed_amount"),
    #             "gst_on_fms": row.get("gst_on_fms"),
    #             "base_price_excluding_gst": row.get("base_price_excluding_gst"),
    #             "total_emi": row.get("total_emi"),
    #             "gst": row.get("gst"),
    #             "emi_financing": row.get("emi_financing"),
    #             "status": row.get("status"),
    #             "ex_showroom_amount": row.get("ex_showroom_amount"),
    #             "finance_emi_road_tax": row.get("finance_emi_road_tax"),
    #             "finance_hod_status": row.get("finance_hod_status"),
    #         })

    #         # car_quotation_item.insert()

    #     print({"car_quotation_item":car_quotation_item})
    #     # frappe.db.commit()
    #     # return f"File processed successfully: {file_path}"
    #     frappe.local.response["type"] = "redirect"
    #     frappe.local.response["location"] = "/approved"

    # except Exception as e:
    #     frappe.log_error(frappe.get_traceback(), "File Processing Error")
    #     frappe.throw(f"An error occurred while processing the file: {str(e)}")
    #     frappe.local.response["type"] = "redirect"
    #     frappe.local.response["location"] = "/somethingwrong"
    # return {"name":"Jay"}
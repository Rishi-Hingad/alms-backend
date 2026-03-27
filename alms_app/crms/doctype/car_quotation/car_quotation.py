import frappe
from openpyxl import load_workbook
from frappe.model.document import Document
import pandas as pd 
from frappe.utils.file_manager import save_file
import xlrd

class CarQuotation(Document):
    pass
    # def upload_data(self):
    #     # Ensure the file is attached and accessible
    #     if not self.attach_file:
    #         frappe.throw("No file attached for upload.")
        
    #     try:
    #         # Fetch the file from the system using the file URL
    #         _file = frappe.get_doc("File", {"file_url": self.attach_file})  # Replace 'attach_file' with actual file URL field
    #         filename = _file.get_full_path()
            
    #         # Parse the Excel file
    #         data = self.parse_excel(filename)

    #         # Populate the Car Quotation fields with parsed data
    #         self.populate_car_quotation_fields(data)
    #     except Exception as e:
    #         frappe.throw(f"Error while uploading file: {str(e)}")

    # def parse_excel(self, file_path):
    #     # Load the workbook and get the active sheet
    #     wb = load_workbook(file_path)
    #     sheet = wb.active
        
    #     # List to hold parsed data
    #     data = []

    #     # Assuming the first row contains headers, iterate through the rows
    #     for row in sheet.iter_rows(min_row=2, values_only=True):  # Start from row 2 to skip headers
    #         # Ensure row has the correct number of columns (29 in this case)
    #         if len(row) >= 29:
    #             row_data = {
    #                 'finance_company': row[0],
    #                 'employee_details': row[1],
    #                 'location': row[2],
    #                 'kms': row[3],
    #                 'variant': row[4],
    #                 'quote': row[5],
    #                 'interest_rate': row[6],
    #                 'tenure': row[7],
    #                 'base_price_excluding_gst': row[8],
    #                 'gst': row[9],
    #                 'ex_showroom_amount': row[10],
    #                 'accessory': row[11],
    #                 'discount_excluding_gst': row[12],
    #                 'base_price_less_discounts': row[13],
    #                 'total_discount': row[14],
    #                 'ex_showroom_amount_net_of_discount': row[15],
    #                 'registration_charges': row[16],
    #                 'residual_value': row[17],
    #                 'percent': row[18],
    #                 'financed_amount': row[19],
    #                 'emi_financing': row[20],
    #                 'finance_emi_road_tax': row[21],
    #                 'gst_and_cess': row[22],
    #                 'insurance': row[23],
    #                 'fleet_management_repairs_and_tyres': row[24],
    #                 'assist_service': row[25],
    #                 'pickup_and_drop': row[26],
    #                 'std_relief_car_non_accident': row[27],
    #                 'gst_on_fms': row[28],
    #                 'total_emi': row[29]
    #             }
    #             data.append(row_data)

    #     return data

    # def populate_car_quotation_fields(self, data):
    #     # Map the parsed data to the fields of Car Quotation
    #     for row in data:
    #         self.finance_company = row['finance_company']
    #         self.employee_details = row['employee_details']
    #         self.location = row['location']
    #         self.kms = row['kms']
    #         self.variant = row['variant']
    #         self.quote = row['quote']
    #         self.interest_rate = row['interest_rate']
    #         self.tenure = row['tenure']
    #         self.base_price_excluding_gst = row['base_price_excluding_gst']
    #         self.gst = row['gst']
    #         self.ex_showroom_amount = row['ex_showroom_amount']
    #         self.accessory = row['accessory']
    #         self.discount_excluding_gst = row['discount_excluding_gst']
    #         self.base_price_less_discounts = row['base_price_less_discounts']
    #         self.total_discount = row['total_discount']
    #         self.ex_showroom_amount_net_of_discount = row['ex_showroom_amount_net_of_discount']
    #         self.registration_charges = row['registration_charges']
    #         self.residual_value = row['residual_value']
    #         self.percent = row['percent']
    #         self.financed_amount = row['financed_amount']
    #         self.emi_financing = row['emi_financing']
    #         self.finance_emi_road_tax = row['finance_emi_road_tax']
    #         self.gst_and_cess = row['gst_and_cess']
    #         self.insurance = row['insurance']
    #         self.fleet_management_repairs_and_tyres = row['fleet_management_repairs_and_tyres']
    #         self.assist_service = row['assist_service']
    #         self.pickup_and_drop = row['pickup_and_drop']
    #         self.std_relief_car_non_accident = row['std_relief_car_non_accident']
    #         self.gst_on_fms = row['gst_on_fms']
    #         self.total_emi = row['total_emi']

    #     # Save the changes
    #     self.save(ignore_permissions=True)

@frappe.whitelist()
def process_uploaded_file(file_url):
    if not file_url:
            frappe.throw("No file attached for upload.")

    try:
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        file_path = file_doc.get_full_path()

        # if file_path.endswith(".xlsx") or file_path.endswith(".xls"):
        #     data_frame = pd.read_excel(file_path)
        # elif file_path.endswith(".csv"):
        #     data_frame = pd.read_csv(file_path)
        if file_path.endswith(".xlsx"):
            data_frame = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith(".xls"):
            data_frame = pd.read_excel(file_path, engine='xlrd')
        elif file_path.endswith(".csv"):
            data_frame = pd.read_csv(file_path)

        else:
            frappe.throw("Unsupported file format. Please upload an Excel or CSV file.")

        for index, row in data_frame.iterrows():
            car_quotation_item = frappe.get_doc({
                "doctype": "Car Quotation",
                "finance_company": row.get("finance_company"),
                "accessory": row.get("accessory"),
                "gst_and_cess": row.get("gst_and_cess"),
                "employee_details": row.get("employee_details"),
                "discount_excluding_gst": row.get("discount_excluding_gst"),
                "insurance": row.get("insurance"),
                "location": row.get("location"),
                "base_price_less_discounts": row.get("base_price_less_discounts"),
                "fleet_management_repairs_and_tyres": row.get("fleet_management_repairs_and_tyres"),
                "kms": row.get("kms"),
                "total_discount": row.get("total_discount"),
                "24x7_assist": row.get("24x7_assist"),
                "variant": row.get("variant"),
                "ex_showroom_amount_net_of_discount": row.get("ex_showroom_amount_net_of_discount"),
                "pickup_and_drop": row.get("pickup_and_drop"),
                "quote": row.get("quote"),
                "registration_charges": row.get("registration_charges"),
                "interest_rate": row.get("interest_rate"),
                "residual_value_percent": row.get("residual_value_percent"),
                "std_relief_car_non_accdt": row.get("std_relief_car_non_accdt"),
                "tenure": row.get("tenure"),
                "financed_amount": row.get("financed_amount"),
                "gst_on_fms": row.get("gst_on_fms"),
                "base_price_excluding_gst": row.get("base_price_excluding_gst"),
                "total_emi": row.get("total_emi"),
                "gst": row.get("gst"),
                "emi_financing": row.get("emi_financing"),
                "status": row.get("status"),
                "ex_showroom_amount": row.get("ex_showroom_amount"),
                "finance_emi_road_tax": row.get("finance_emi_road_tax"),
                "finance_hod_status": row.get("finance_hod_status"),
            })

            # car_quotation_item.insert()

        return {"car_quotation_item":car_quotation_item}
        # frappe.db.commit()
        # return f"File processed successfully: {file_path}"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "File Processing Error")
        frappe.throw(f"An error occurred while processing the file: {str(e)}")

import frappe

@frappe.whitelist()
def generate_deduction(quotation_id):

    quotation = frappe.get_doc("Car Quotation", quotation_id)

    doc = frappe.new_doc("Company and Employee Deduction")

    doc.finance_quotation_id = quotation.name
    doc.employee_details = quotation.employee_details
    doc.finance_company = quotation.finance_company

    # Company values
    doc.quarterly_payment = quotation.quarterly_payment

    # Employee values
    doc.employee_quarterly_payment = quotation.employee_quarterly_payment

    # copy other required calculation fields
    doc.interest_rate = quotation.interest_rate
    doc.tenure = quotation.tenure
    doc.ex_showroom_amount_net_of_discount = quotation.ex_showroom_amount_net_of_discount
    doc.registration_charges = quotation.registration_charges
    doc.residual_value = quotation.residual_value

    doc.insert(ignore_permissions=True)

    return doc.name


from frappe.utils import flt
import math


def pmt(rate, nper, pv, fv=0, when=1):
    if rate == 0:
        return -(pv + fv) / nper
    return -(rate * (fv + pv * (1 + rate) ** nper)) / ((1 + rate * when) * ((1 + rate) ** nper - 1))


@frappe.whitelist()
def preview_deduction(quotation_id):

    q = frappe.get_doc("Car Quotation", quotation_id)
    employee = frappe.get_doc("Employee Master", q.employee_details)
    
    # ---- Company contribution logic (same as calculate_emi) ----

    interest_rate = flt(q.interest_rate) / 100
    tenure = flt(q.tenure)

    registration = flt(q.registration_charges)
    gst = flt(q.gst)

    insurance = flt(q.insurance)
    fms = flt(q.fleet_management_repairs_and_tyres)
    assist = flt(q.get("24x7_assist"))
    print("Value of 24x7 assist:",assist)
    # assist = flt(97)
    pickup = flt(q.pickup_and_drop)
    relief = flt(q.std_relief_car_non_accdt)
    monthly_rate = interest_rate / 12

    company_ex_showroom_amount_net_of_discount = flt(employee.eligibility)
    print("Company ex-showroom amount net of discount:", company_ex_showroom_amount_net_of_discount)

    registration = flt(q.registration_charges)

    # Company financed amount
    financed_amount = company_ex_showroom_amount_net_of_discount + registration
    print("Company financed amount:", financed_amount)

    # Residual value calculation (53%)
    residual_percent = flt(q.residual_value_percent) / 100
    residual_amount = flt(q.residual_value)

    pmt_val = pmt(monthly_rate, tenure, -financed_amount, residual_amount, 1)
    print("PMT for company:", pmt_val)

    gst_per_month = gst / tenure if tenure else 0

    emi_financing = round(pmt_val - gst_per_month)
    print("EMI financing for company:", emi_financing)

    finance_emi_road_tax = round(emi_financing - (registration / tenure if tenure else 0))
    print("Finance EMI road tax for company:", finance_emi_road_tax)

    gst_and_cess = round(finance_emi_road_tax * 45 / 100)
    print("GST and cess for company:", gst_and_cess)

    gst_on_fms = round((insurance + fms + assist + pickup + relief) * 18 / 100)
    print("GST on FMS for company:", gst_on_fms)
    print("Insurance for company:", insurance)
    print("FMS for company:", fms)
    print("Assist for company:", assist)

    total_emi1 = (
        emi_financing
        + gst_and_cess
        + insurance
        + fms
        + assist
        + pickup
        + relief
        + gst_on_fms
    )

    total_emi = round(total_emi1)
    print("Total EMI for company:", total_emi)

    quarterly_payment = math.ceil(total_emi * 3)
    interim_payment = math.ceil(quarterly_payment * 39 / 90)

    # ---- Employee contribution logic (same as calculate_employee_fields) ----

    employee_ex_showroom_amount_net_of_discount = (flt(q.ex_showroom_amount_net_of_discount) - company_ex_showroom_amount_net_of_discount)

    employee_financed_amount = math.ceil(employee_ex_showroom_amount_net_of_discount)

    pmt_emp = pmt(monthly_rate, tenure, -employee_financed_amount, 0, 1)
    print("PMT for employee:", pmt_emp)

    employee_emi_financing = pmt_emp

    employee_finance_emi_road_tax = employee_emi_financing
    print("Finance EMI road tax for employee:", employee_finance_emi_road_tax)

    employee_gst_and_cess = round(employee_finance_emi_road_tax * 45 / 100)
    print("GST and cess for employee:", employee_gst_and_cess)

    employee_total_emi = round(employee_emi_financing + employee_gst_and_cess)
    print("Total EMI for employee:", employee_total_emi)

    employee_quarterly_payment = math.ceil(employee_total_emi * 3)
    employee_interim_payment = math.ceil(employee_quarterly_payment * 39 / 90)

    # return {
    #     "total_emi": total_emi,
    #     "employee_total_emi": employee_total_emi,
    #     "quarterly_payment": quarterly_payment,
    #     "employee_quarterly_payment": employee_quarterly_payment,
    #     "interim_payment": interim_payment,
    #     "employee_interim_payment": employee_interim_payment
    # }
    return {
        # company
        "company_ex_showroom": company_ex_showroom_amount_net_of_discount,
        "company_financed_amount": financed_amount,
        "company_emi_financing": emi_financing,
        "company_finance_emi_road_tax": finance_emi_road_tax,
        "company_gst_and_cess": gst_and_cess,
        "company_gst_on_fms": gst_on_fms,
        "total_emi": total_emi,
        "quarterly_payment": quarterly_payment,
        "interim_payment": interim_payment,

        # employee
        "employee_ex_showroom": employee_ex_showroom_amount_net_of_discount,
        "employee_financed_amount": employee_financed_amount,
        "employee_emi_financing": employee_emi_financing,
        "employee_finance_emi_road_tax": employee_finance_emi_road_tax,
        "employee_gst_and_cess": employee_gst_and_cess,
        "employee_total_emi": employee_total_emi,
        "employee_quarterly_payment": employee_quarterly_payment,
        "employee_interim_payment": employee_interim_payment
    }

@frappe.whitelist()
def create_deduction_doc(quotation_id):

    q = frappe.get_doc("Car Quotation", quotation_id)
    values = preview_deduction(quotation_id)

    doc = frappe.new_doc("Company and Employee Deduction")

    doc.finance_quotation_id = quotation_id
    doc.employee_name = q.employee_details

    # company
    doc.ex_showroom_amount = values["company_ex_showroom"]
    doc.financed_amount = values["company_financed_amount"]
    doc.emi_financing = values["company_emi_financing"]
    doc.finance_emi_road_tax = values["company_finance_emi_road_tax"]
    doc.gst_and_cess = values["company_gst_and_cess"]
    doc.gst_on_fms = values["company_gst_on_fms"]

    doc.total_emi = values["total_emi"]
    doc.quarterly_payment = values["quarterly_payment"]
    doc.interim_payment = values["interim_payment"]

    # employee
    doc.employee_ex_showroom_amount_net_of_discount = values["employee_ex_showroom"]
    doc.employee_financed_amount = values["employee_financed_amount"]
    doc.employee_emi_financing = values["employee_emi_financing"]
    doc.employee_finance_emi_road_tax = values["employee_finance_emi_road_tax"]
    doc.employee_gst_and_cess = values["employee_gst_and_cess"]
    doc.employee_total_emi = values["employee_total_emi"]
    doc.employee_quarterly_payment = values["employee_quarterly_payment"]
    doc.employee_interim_payment = values["employee_interim_payment"]

    doc.insert(ignore_permissions=True)

    return doc.name
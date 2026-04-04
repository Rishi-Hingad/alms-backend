# Copyright (c) 2026, Rishi Hingad and contributors
# For license information, please see license.txt

from os import link

import frappe
from frappe.model.document import Document
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
from frappe.utils import getdate
from frappe.utils import today


class InvoiceDetails(Document):

    def after_insert(self):
        self.update_contract_installment()

    def on_update(self):
        self.update_contract_installment()

    def update_contract_installment(self):

        if not self.contract_number or not self.installment_no:
            return

        contract = frappe.get_doc("Contract Master", self.contract_number)

        matched_row = None

        for row in contract.installment_date:
            if str(row.installment_no) == str(self.installment_no):
                matched_row = row
                break

        if not matched_row:
            frappe.throw(
                f"Installment {self.installment_no} not found in Contract {self.contract_number}"
            )

        start_date_child = getdate(matched_row.installment_start_date)
        end_date_child = getdate(matched_row.installment_end_date)

        start_date_invoice = getdate(self.invoice_date_from)
        end_date_invoice = getdate(self.invoice_date_to)

        if start_date_child != start_date_invoice or end_date_child != end_date_invoice:
            frappe.throw(
                f"Invoice dates do not match installment dates for installment {self.installment_no}"
            )

        # prevent duplicate linking
        if matched_row.invoice_id and matched_row.invoice_id != self.name:
            frappe.throw(
                f"Installment {self.installment_no} already linked with {matched_row.invoice_id}"
            )

        frappe.db.set_value(
            "Installment Details",
            matched_row.name,
            "invoice_id",
            self.name
        )

        frappe.msgprint(f"Linked invoice {self.name} to installment {matched_row.installment_no}")

def clean_amount(val):
    if not val:
        return 0
    return float(str(val).replace(",", "").strip())

def clean_date(val):
    if not val:
        return None
    return getdate(val)

def validate(self):

    duplicate = frappe.db.exists(
        "Invoice Details",
        {
            "contract_number": self.contract_number,
            "installment_no": self.installment_no,
            "name": ["!=", self.name]
        }
    )

    if duplicate:
        frappe.throw(
            f"Installment {self.installment_no} already invoiced for Contract {self.contract_number}"
        )

def make_link(doctype, name=None, label=None):
    route = doctype.replace(" ", "-").lower()

    if name:
        url = f"/app/{route}/{name}"
    else:
        url = f"/app/{route}"

    label = label or f"Open {doctype}"

    return f'<a href="{url}" target="_blank" style="color:#1f6feb; font-weight:500;">{label}</a>'


@frappe.whitelist()
def upload_invoice_excel(file_url, vendor, user_email):

    if vendor == "Eazy Assets":
        return process_eazy_assets(file_url, vendor, user_email)

    elif vendor == "ALD":
        return process_ald(file_url, vendor, user_email)

    else:
        frappe.throw("Invalid Vendor Selected")


@frappe.whitelist()
def process_eazy_assets(file_url, vendor=None, user_email=None):
    print("Processing Eazy Assets Excel:", vendor)

    rows = read_xlsx_file_from_attached_file(file_url)

    headers = [h.strip() for h in rows[0]]
    data = rows[1:]

    created = 0
    failed_count = 0
    total_a = 0
    total_b = 0
    total_c = 0
    total_d = 0
    total_employee_contribution = 0
    total_company_contribution = 0

    valid_invoice_count = 0

    batch = frappe.new_doc("Invoice Batch")
    batch.vendor_name = vendor
    batch.excel_file = file_url
    batch.excel_uploading_by = user_email
    batch.status = "Processing"
    batch.insert(ignore_permissions=True)

    header_map = {
        "Contract No.": "contract_number",
        "Employee Name": "employee_name",
        "Invoice date from": "invoice_date_from",
        "Invoice date to": "invoice_date_to",
        "Contract End Date": "contract_end_date",
        "Vehicle Details": "vehicle_details",
        "Installment No.": "installment_no",
        "No of Billing Days": "no_of_billing_days",
        "Billing Date": "billing_date",

        "Rental Invoice No.": "invoice_no_rental",
        "Invoice Value ( A)": "invoice_value_a",

        "Fleet Invoice No": "invoice_no_fleet",
        "Invoice Value ( B)": "invoice_value_b",

        "Road Invoice No.": "invoice_no_road",
        "Invoice Value ( C)": "invoice_value_c",

        "Insurance Invoice No.": "invoice_no_insurance",
        "Invoice Value ( D)": "invoice_value_d",
    }

    for idx, row in enumerate(data, start=1):

        row_dict = dict(zip(headers, row))

        mapped = {}
        for excel_col, fieldname in header_map.items():
            mapped[fieldname] = row_dict.get(excel_col)

        try:
            contract_number = mapped.get("contract_number")

            # ---- Extract Company from Contract ---- #
            if "-" not in contract_number:
                raise Exception(f"Invalid Contract Format: {contract_number}")

            company = contract_number.split("-")[0].strip()

            if not contract_number:
                raise Exception("Contract number missing")

            if not frappe.db.exists("Contract Master", contract_number):
                raise Exception(f"Contract {contract_number} does not exist")

            installment_no = mapped.get("installment_no")

            if not installment_no:
                raise Exception("Installment number missing")

            installment_no = str(installment_no).strip()

            duplicate = frappe.db.exists(
                "Invoice Details",
                {
                    "contract_number": contract_number,
                    "installment_no": installment_no
                }
            )

            if duplicate:
                raise Exception(
                    f"Invoice already exists for Contract {contract_number} Installment {installment_no}"
                )

            employee_name = frappe.db.get_value(
                "Contract Master",
                contract_number,
                "employee_car_process_form"
            )
            if not employee_name:
                raise Exception(f"Employee not linked to Contract {contract_number}")

            # ---- Clean values ---- #
            invoice_value_a = clean_amount(mapped.get("invoice_value_a"))
            invoice_value_b = clean_amount(mapped.get("invoice_value_b"))
            invoice_value_c = clean_amount(mapped.get("invoice_value_c"))
            invoice_value_d = clean_amount(mapped.get("invoice_value_d"))

            total = (
                invoice_value_a +
                invoice_value_b +
                invoice_value_c +
                invoice_value_d
            )

            # ---- Fetch Cost Center ---- #
            cost_center = frappe.db.get_value(
                "Employee Master",
                {"name": employee_name},
                "cost_center"
            )
            print("Cost Center ee:", cost_center)
            print("Employee Name ee:", employee_name)
            if not cost_center:
                # raise Exception(f"Cost Center not found for Employee {employee_name}")
                link = make_link("Employee Master", employee_name, "Open Employee")
                raise Exception(f"Cost Center not found for Employee {employee_name}. {link}")

            # ---- Default values ---- #
            employee_contribution = 0
            company_contribution = 0
            remarks = ""

            # ---- Fetch Deduction ---- #
            deduction = frappe.db.get_value(
                "Company and Employee Deduction",
                {"employee_name": employee_name},
                [
                    "finance_team_status",
                    "finance_head_status",
                    "quarterly_payment",
                    "employee_quarterly_payment"
                ],
                as_dict=True,
                order_by="creation desc"
            )

            if not deduction:
                # raise Exception("Deduction record not found")
                link = make_link("Car Quotation", contract_number, "Open Car Quotation")
                raise Exception(f"Deduction record not found. {link}")
            
            if deduction.finance_team_status != "Approved":
                raise Exception("Deduction not approved by Finance Team")

            if deduction.finance_head_status != "Approved":
                raise Exception("Deduction not approved by Finance Head")

            # Only if approved
            company_contribution = deduction.quarterly_payment or 0
            employee_contribution = deduction.employee_quarterly_payment or 0

            total_a += invoice_value_a
            total_b += invoice_value_b
            total_c += invoice_value_c
            total_d += invoice_value_d

            valid_invoice_count += 1

            # ---- Add to totals ---- #
            total_company_contribution += company_contribution
            total_employee_contribution += employee_contribution

            created += 1

            # ---- STORE IN BATCH (SUCCESS) ---- #
            batch.append("rows", {
                "row_number": idx,

                "contract_number": contract_number,
                "employee_name": employee_name,
                "vehicle_details": mapped.get("vehicle_details"),
                "company": company,

                "invoice_date_from": clean_date(mapped.get("invoice_date_from")),
                "invoice_date_to": clean_date(mapped.get("invoice_date_to")),
                "contract_end_date": clean_date(mapped.get("contract_end_date")),

                "installment_no": installment_no,
                "no_of_billing_days": mapped.get("no_of_billing_days"),
                "billing_date": clean_date(mapped.get("billing_date")),

                "invoice_no_rental": mapped.get("invoice_no_rental"),
                "invoice_value_a": invoice_value_a,

                "invoice_no_fleet": mapped.get("invoice_no_fleet"),
                "invoice_value_b": invoice_value_b,

                "invoice_no_road": mapped.get("invoice_no_road"),
                "invoice_value_c": invoice_value_c,

                "invoice_no_insurance": mapped.get("invoice_no_insurance"),
                "invoice_value_d": invoice_value_d,

                "total_invoice_value": total,
                "cost_center": cost_center,
                "employee_contribution": employee_contribution,
                "company_contribution": company_contribution,
                # "error_message": remarks,

                "status": "Success"
            })

        except Exception as e:

            failed_count += 1

            # ---- STORE IN BATCH (ALL ROWS) ---- #
            # batch.append("rows", {
            #     "row_number": idx,
            #     "contract_number": mapped.get("contract_number"),
            #     "installment_no": mapped.get("installment_no"),
            #     "status": "Failed",
            #     "error_message": str(e)
            # })

            # ---- STORE IN FAILED TABLE ---- #
            failed_row = {
                "row_number": idx,
                "status": "Failed",
                "error_message": str(e)
            }

            # dump all mapped fields
            for key, value in mapped.items():
                failed_row[key] = value

            batch.append("failed_rows_table", failed_row)

    # ---- FINALIZE BATCH ---- #
    batch.success_rows = created
    batch.failed_rows = failed_count
    batch.total_rows = created + failed_count

    batch.status = "Failed" if failed_count else "Completed"
    batch.batch_date = today()
    batch.company = company


    batch.no_of_invoice = valid_invoice_count

    batch.total_value_of_rental_charges = total_a
    batch.total_value_of_fleet_charges = total_b
    batch.total_value_of_rto = total_c
    batch.total_value_of_insurance = total_d

    batch.total_value_of_all = (
        total_a + total_b + total_c + total_d
    )

    # Optional (if you have logic later)
    batch.total_value_of_company_contribution = total_company_contribution
    batch.total_value_of_employee_contribution = total_employee_contribution

    batch.save()
    frappe.db.commit()

    msg = f"{created} invoices created successfully"

    if failed_count:
        msg += f"<br>{failed_count} failed rows logged in Batch: <b>{batch.name}</b>"

    return msg


# ---------------- ALD PLACEHOLDER ---------------- #

@frappe.whitelist()
def process_ald(file_url, vendor=None, user_email=None):
    print("Processing ALD Excel:", vendor)

    rows = read_xlsx_file_from_attached_file(file_url)
    print("Rows read from Excel:", len(rows))
    print("Sample Row:", rows[0] if rows else "No data found")

    headers = [h.strip() for h in rows[0]]
    data = rows[1:]

    created = 0
    failed_count = 0

    total_a = 0
    total_b = 0
    total_c = 0

    total_employee_contribution = 0
    total_company_contribution = 0

    valid_invoice_count = 0

    batch = frappe.new_doc("Invoice Batch")
    batch.vendor_name = vendor
    batch.excel_file = file_url
    batch.excel_uploading_by = user_email
    batch.status = "Processing"
    batch.insert(ignore_permissions=True)

    # ---- ALD HEADER MAP ---- #
    header_map = {
        "Contract No.": "contract_number",
        "Emp. Name": "employee_name",
        "Vehicle Details": "vehicle_details",
        "Inst. No.": "installment_no",
        "Company": "company",
        "Month": "month",

        # A - Rental
        "Inv.No.": "invoice_no_rental",
        "Inv.Date": "invoice_date_rental",
        "Inv.Value (A)": "invoice_value_a",

        # B - Fleet
        "Inv.No._1": "invoice_no_fleet",
        "Inv.Date_1": "invoice_date_fleet",
        "Inv.Value (B)": "invoice_value_b",

        # C - RTO
        "Inv.No._2": "invoice_no_road",
        "Inv.Date_2": "invoice_date_road",
        "RTO ( C )": "invoice_value_c",
    }
    company = None

    for idx, row in enumerate(data, start=1):

        row_dict = dict(zip(headers, row))

        mapped = {}
        for excel_col, fieldname in header_map.items():
            mapped[fieldname] = row_dict.get(excel_col)

        try:
            contract_number = mapped.get("contract_number")
            row_company = mapped.get("company")

            if not company and row_company:
                company = row_company

            if not contract_number:
                raise Exception("Contract number missing")

            if not frappe.db.exists("Contract Master", contract_number):
                # raise Exception(f"Contract {contract_number} does not exist")
                link = make_link("Contract Master", None, "Create Contract")
                raise Exception(f"Contract {contract_number} does not exist. {link}")

            installment_no = mapped.get("Inst. No.")

            if not installment_no:
                raise Exception("Installment number missing")

            installment_no = str(installment_no).strip()

            duplicate = frappe.db.exists(
                "Invoice Details",
                {
                    "contract_number": contract_number,
                    "installment_no": installment_no
                }
            )

            if duplicate:
                # raise Exception(
                #     f"Invoice already exists for Contract {contract_number} Installment {installment_no}"
                # )
                link = make_link("Invoice Details", None, "View Invoices")
                raise Exception(
                    f"Invoice already exists for Contract {contract_number} Installment {installment_no}. {link}"
                )

            # ---- Employee from Contract ---- #
            employee_name = frappe.db.get_value(
                "Contract Master",
                contract_number,
                "employee_car_process_form"
            )

            if not employee_name:
                raise Exception(f"Employee not linked to Contract {contract_number}")

            # ---- Clean Values ---- #
            invoice_value_a = clean_amount(mapped.get("invoice_value_a"))
            invoice_value_b = clean_amount(mapped.get("invoice_value_b"))
            invoice_value_c = clean_amount(mapped.get("invoice_value_c"))

            total = invoice_value_a + invoice_value_b + invoice_value_c

            # ---- Cost Center ---- #
            cost_center = frappe.db.get_value(
                "Employee Master",
                employee_name,
                "cost_center"
            )
            print("Cost Center:", cost_center)
            print("Employee Name:", employee_name)

            if not cost_center:
                # raise Exception(f"Cost Center not found for Employee {employee_name}")
                link = make_link("Employee Master", employee_name, "Open Employee")
                raise Exception(f"Cost Center not found for Employee {employee_name}. {link}")

            # ---- Contributions ---- #
            employee_contribution = 0
            company_contribution = 0

            deduction = frappe.db.get_value(
                "Company and Employee Deduction",
                {"employee_name": employee_name},
                [
                    "finance_team_status",
                    "finance_head_status",
                    "quarterly_payment",
                    "employee_quarterly_payment"
                ],
                as_dict=True,
                order_by="creation desc"
            )

            if not deduction:
                # raise Exception("Deduction record not found")
                link = make_link("car-quotation")
                raise Exception(f"Deduction record not found. {link}")

            if deduction.finance_team_status != "Approved":
                raise Exception("Deduction not approved by Finance Team")

            if deduction.finance_head_status != "Approved":
                raise Exception("Deduction not approved by Finance Head")

            company_contribution = deduction.quarterly_payment or 0
            employee_contribution = deduction.employee_quarterly_payment or 0

            # ---- Totals ---- #
            total_a += invoice_value_a
            total_b += invoice_value_b
            total_c += invoice_value_c

            total_company_contribution += company_contribution
            total_employee_contribution += employee_contribution

            valid_invoice_count += 1
            created += 1

            # ---- STORE SUCCESS ---- #
            batch.append("rows", {
                "row_number": idx,

                "contract_number": contract_number,
                "employee_name": employee_name,
                "vehicle_details": mapped.get("vehicle_details"),

                "installment_no": installment_no,
                "month": clean_date(mapped.get("month")),

                "invoice_no_rental": mapped.get("invoice_no_rental"),
                "invoice_value_a": invoice_value_a,

                "invoice_no_fleet": mapped.get("invoice_no_fleet"),
                "invoice_value_b": invoice_value_b,

                "invoice_no_road": mapped.get("invoice_no_road"),
                "invoice_value_c": invoice_value_c,

                "total_invoice_value": total,
                "cost_center": cost_center,
                "employee_contribution": employee_contribution,
                "company_contribution": company_contribution,

                "status": "Success"
            })

        except Exception as e:

            failed_count += 1

            # batch.append("rows", {
            #     "row_number": idx,
            #     "contract_number": mapped.get("contract_number"),
            #     "installment_no": mapped.get("installment_no"),
            #     "status": "Failed",
            #     "error_message": str(e)
            # })

            failed_row = {
                "row_number": idx,
                "status": "Failed",
                "error_message": str(e)
            }

            # dump all mapped fields
            for key, value in mapped.items():
                failed_row[key] = value

            batch.append("failed_rows_table", failed_row)

    # ---- FINALIZE ---- #
    batch.success_rows = created
    batch.failed_rows = failed_count
    batch.total_rows = created + failed_count

    batch.status = "Failed" if failed_count else "Completed"
    batch.batch_date = today()
    batch.company = company

    batch.no_of_invoice = valid_invoice_count

    batch.total_value_of_rental_charges = total_a
    batch.total_value_of_fleet_charges = total_b
    batch.total_value_of_rto = total_c

    batch.total_value_of_all = total_a + total_b + total_c

    batch.total_value_of_company_contribution = total_company_contribution
    batch.total_value_of_employee_contribution = total_employee_contribution

    batch.save()
    frappe.db.commit()

    msg = f"{created} invoices created successfully"

    if failed_count:
        msg += f"<br>{failed_count} failed rows logged in Batch: <b>{batch.name}</b>"

    return msg
# Copyright (c) 2026, Rishi Hingad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
from frappe.utils import getdate


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
     

@frappe.whitelist()
def upload_invoice_excel(file_url):

    rows = read_xlsx_file_from_attached_file(file_url)

    headers = [h.strip() for h in rows[0]]
    data = rows[1:]

    created = 0
    failed_rows = []
    
    # Create batch import
    batch = frappe.new_doc("Invoice Import")
    batch.excel_file = file_url
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

        try:

            row_dict = dict(zip(headers, row))

            mapped = {}
            for excel_col, fieldname in header_map.items():
                mapped[fieldname] = row_dict.get(excel_col)

            contract_number = mapped.get("contract_number")

            if not contract_number:
                raise Exception("Contract number missing")

            if not frappe.db.exists("Contract Master", contract_number):
                raise Exception(f"Contract {contract_number} does not exist")

            installment_no = str(mapped.get("installment_no")).strip()

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

            doc = frappe.new_doc("Invoice Details")

            doc.contract_number = contract_number
            doc.employee_name = employee_name

            doc.invoice_date_from = clean_date(mapped.get("invoice_date_from"))
            doc.invoice_date_to = clean_date(mapped.get("invoice_date_to"))
            doc.contract_end_date = clean_date(mapped.get("contract_end_date"))

            doc.vehicle_details = mapped.get("vehicle_details")
            doc.installment_no = installment_no
            doc.no_of_billing_days = mapped.get("no_of_billing_days")

            doc.billing_date = clean_date(mapped.get("billing_date"))

            doc.invoice_no_rental = mapped.get("invoice_no_rental")
            doc.invoice_value_a = clean_amount(mapped.get("invoice_value_a"))

            doc.invoice_no_fleet = mapped.get("invoice_no_fleet")
            doc.invoice_value_b = clean_amount(mapped.get("invoice_value_b"))

            doc.invoice_no_road = mapped.get("invoice_no_road")
            doc.invoice_value_c = clean_amount(mapped.get("invoice_value_c"))

            doc.invoice_no_insurance = mapped.get("invoice_no_insurance")
            doc.invoice_value_d = clean_amount(mapped.get("invoice_value_d"))

            doc.total_invoice_value = (
                doc.invoice_value_a
                + doc.invoice_value_b
                + doc.invoice_value_c
                + doc.invoice_value_d
            )
            doc.excel_uploaded_by = frappe.session.user
            doc.excel_uploaded_on = frappe.utils.now_datetime()
            doc.excel_batch_id = batch.name

            doc.insert(ignore_permissions=True)
            doc.update_contract_installment()

            created += 1

        except Exception as e:

            mapped["row_number"] = idx
            mapped["status"] = "Error"
            mapped["error_message"] = str(e)

            failed_rows.append(mapped)

    # Create Invoice Import only if errors exist
    if failed_rows:

        for r in failed_rows:
            batch.append("rows", r)
        batch.failed_rows = len(failed_rows)

    batch.success_rows = created
    batch.total_rows = created + len(failed_rows)
    if failed_rows:
        batch.status = "Failed"
    else:
        batch.status = "Completed"
    
    batch.save()
    frappe.db.commit()

    msg = f"{created} invoices created successfully"

    if failed_rows:
        msg += f"<br>{len(failed_rows)} rows moved to Invoice Import Batch: <b>{batch.name}</b>"

    return msg
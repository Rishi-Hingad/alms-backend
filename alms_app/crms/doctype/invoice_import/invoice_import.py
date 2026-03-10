# Copyright (c) 2026, Rishi Hingad
from frappe.model.document import Document
import frappe
import pandas as pd
from frappe.utils.file_manager import get_file
from frappe.utils import getdate
from frappe import _
import io

class InvoiceImport(Document):
    pass


# -----------------------------
# Helpers
# -----------------------------

def clean_amount(val):
    if not val:
        return 0
    return float(str(val).replace(",", "").strip())


def clean_date(val):
    if not val:
        return None
    return getdate(val)


def get_total(row):
    return (
        (row.invoice_value_a or 0)
        + (row.invoice_value_b or 0)
        + (row.invoice_value_c or 0)
        + (row.invoice_value_d or 0)
    )


# Parse Excel
@frappe.whitelist()
def parse_excel(docname):

    doc = frappe.get_doc("Invoice Import", docname)

    file_path = get_file(doc.excel_file)[1]
    df = pd.read_excel(file_path)

    doc.rows = []

    required_columns = [
        "Contract No.",
        "Installment No.",
        "Billing Date"
    ]

    for col in required_columns:
        if col not in df.columns:
            frappe.throw(f"Missing required column: {col}")

    for i, row in df.iterrows():

        doc.append("rows", {
            "row_number": i + 1,

            "contract_number": row.get("Contract No."),
            "employee_name": row.get("Employee Name"),

            "invoice_date_from": row.get("Invoice date from"),
            "invoice_date_to": row.get("Invoice date to"),
            "contract_end_date": row.get("Contract End Date"),

            "vehicle_details": row.get("Vehicle Details"),

            "installment_no": row.get("Installment No."),
            "no_of_billing_days": row.get("No of Billing Days"),
            "billing_date": row.get("Billing Date"),

            "invoice_no_rental": row.get("Rental Invoice No."),
            "invoice_value_a": clean_amount(row.get("Invoice Value ( A)")),

            "invoice_no_fleet": row.get("Fleet Invoice No"),
            "invoice_value_b": clean_amount(row.get("Invoice Value ( B)")),

            "invoice_no_road": row.get("Road Invoice No."),
            "invoice_value_c": clean_amount(row.get("Invoice Value ( C)")),

            "invoice_no_insurance": row.get("Insurance Invoice No."),
            "invoice_value_d": clean_amount(row.get("Invoice Value ( D)")),

            "total_invoice_value": 0,

            "status": "Pending"
        })

    doc.total_rows = len(doc.rows)
    doc.save()

    return _("Excel parsed successfully")


@frappe.whitelist()
def process_rows(docname):

    doc = frappe.get_doc("Invoice Import", docname)

    total = len(doc.rows)
    success = 0
    failed = 0

    for idx, row in enumerate(doc.rows, start=1):

        if row.status == "Success":
            continue

        try:

            if not row.contract_number:
                raise Exception("Contract Number missing")

            if not frappe.db.exists("Contract Master", row.contract_number):
                raise Exception(f"Contract {row.contract_number} not found")

            duplicate = frappe.db.exists(
                "Invoice Details",
                {
                    "contract_number": row.contract_number,
                    "installment_no": row.installment_no,
                    "billing_date": clean_date(row.billing_date)
                }
            )

            if duplicate:
                raise Exception("Duplicate invoice exists")

            employee = frappe.db.get_value(
                "Contract Master",
                row.contract_number,
                "employee_car_process_form"
            )

            invoice = frappe.get_doc({
                "doctype": "Invoice Details",

                "contract_number": row.contract_number,
                "employee_name": employee,

                "invoice_date_from": clean_date(row.invoice_date_from),
                "invoice_date_to": clean_date(row.invoice_date_to),

                "billing_date": clean_date(row.billing_date),
                "installment_no": row.installment_no,

                "vehicle_details": row.vehicle_details,

                "invoice_no_rental": row.invoice_no_rental,
                "invoice_value_a": clean_amount(row.invoice_value_a),

                "invoice_no_fleet": row.invoice_no_fleet,
                "invoice_value_b": clean_amount(row.invoice_value_b),

                "invoice_no_road": row.invoice_no_road,
                "invoice_value_c": clean_amount(row.invoice_value_c),

                "invoice_no_insurance": row.invoice_no_insurance,
                "invoice_value_d": clean_amount(row.invoice_value_d),
            })

            invoice.total_invoice_value = get_total(invoice)

            invoice.insert(ignore_permissions=True)

            row.invoice_document = invoice.name
            row.status = "Success"
            row.error_message = ""

            success += 1

        except Exception as e:

            row.status = "Error"
            row.error_message = str(e)

            failed += 1

        frappe.publish_progress(
            percent=(idx / total) * 100,
            title="Processing Invoices"
        )

    doc.success_rows = success
    doc.failed_rows = failed

    doc.save()

    return _("Processing completed")


@frappe.whitelist()
def retry_failed(docname):

    doc = frappe.get_doc("Invoice Import", docname)

    for row in doc.rows:
        if row.status == "Error":
            row.status = "Pending"
            row.error_message = ""

    doc.save()

    return process_rows(docname)


@frappe.whitelist()
def download_error_report(docname):

    doc = frappe.get_doc("Invoice Import", docname)

    rows = []

    for r in doc.rows:
        if r.status == "Error":

            rows.append({
                "Row": r.row_number,
                "Contract No": r.contract_number,
                "Installment": r.installment_no,
                "Billing Date": r.billing_date,
                "Error": r.error_message
            })

    df = pd.DataFrame(rows)

    file_name = "invoice_import_errors.xlsx"

    output = io.BytesIO()
    df.to_excel(output, index=False)

    frappe.response["filename"] = file_name
    frappe.response["filecontent"] = output.getvalue()
    frappe.response["type"] = "binary"
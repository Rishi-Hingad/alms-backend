# Copyright (c) 2026, Rishi Hingad
from frappe.model.document import Document
import frappe
import pandas as pd
from frappe.recorder import status
from frappe.utils.file_manager import get_file
from frappe.utils import getdate, user
from frappe import _
import io

class InvoiceBatch(Document):
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

    file_name = "invoice_batch_errors.xlsx"

    output = io.BytesIO()
    df.to_excel(output, index=False)

    frappe.response["filename"] = file_name
    frappe.response["filecontent"] = output.getvalue()
    frappe.response["type"] = "binary"


@frappe.whitelist()
def update_approval_status(docname, role, action, remarks):

    user = frappe.session.user
    user_roles = frappe.get_roles(user)

    def is_admin():
        return user == "Administrator"
    
    def is_already_processed(status):
        return status in ["Approved", "Rejected"]

    doc = frappe.get_doc("Invoice Batch", docname)

    # ---------------- FINANCE TEAM ---------------- #
    if role == "finance_team":

        if "Finance Team" not in user_roles and not is_admin():
            frappe.throw("Not authorized for Finance Team action")

        if is_already_processed(doc.finance_team_status):
            frappe.throw("Finance Team already processed this")

        doc.finance_team_status = action
        doc.finance_team_remarks = remarks

    # ---------------- FINANCE HEAD ---------------- #
    elif role == "finance_head":

        if "Finance Head" not in user_roles and not is_admin():
            frappe.throw("Not authorized for Finance Head action")
        
        if is_already_processed(doc.finance_head_status):
            frappe.throw("Finance Head already processed this")

        if doc.finance_team_status != "Approved":
            frappe.throw("Finance Team must approve first")

        doc.finance_head_status = action
        doc.finance_head_remarks = remarks

    # ---------------- HR HEAD ---------------- #
    elif role == "hr_head":

        if "HR Head" not in user_roles and not is_admin():
            frappe.throw("Not authorized for HR Head action")
        
        if is_already_processed(doc.hr_head_status):
            frappe.throw("HR Head already processed this")

        if doc.finance_head_status != "Approved":
            frappe.throw("Finance Head must approve first")

        doc.hr_head_status = action
        doc.hr_head_remarks = remarks

    else:
        frappe.throw("Invalid role")

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return "Updated"


def create_invoice_details_on_approval(doc, method):

    if doc.hr_head_status != "Approved":
        return

    # prevent duplicate execution
    if doc.get("invoice_created"):
        return

    for row in doc.rows:

        if row.status != "Success":
            continue

        # duplicate check again (safety net)
        exists = frappe.db.exists(
            "Invoice Details",
            {
                "contract_number": row.contract_number,
                "installment_no": row.installment_no
            }
        )

        if exists:
            continue

        inv = frappe.new_doc("Invoice Details")

        inv.contract_number = row.contract_number
        employee = frappe.db.get_value(
            "Contract Master",
            row.contract_number,
            "employee_car_process_form"
        )

        if not employee:
            frappe.log_error(
                f"Employee not found for Contract {row.contract_number}",
                "Invoice Creation Error"
            )
            continue

        inv.employee_name = employee

        inv.invoice_date_from = row.invoice_date_from
        inv.invoice_date_to = row.invoice_date_to
        inv.contract_end_date = row.contract_end_date

        inv.vehicle_details = row.vehicle_details
        inv.installment_no = row.installment_no
        inv.no_of_billing_days = row.no_of_billing_days

        inv.billing_date = row.billing_date

        inv.invoice_no_rental = row.invoice_no_rental
        inv.invoice_value_a = row.invoice_value_a

        inv.invoice_no_fleet = row.invoice_no_fleet
        inv.invoice_value_b = row.invoice_value_b

        inv.invoice_no_road = row.invoice_no_road
        inv.invoice_value_c = row.invoice_value_c

        inv.invoice_no_insurance = row.invoice_no_insurance
        inv.invoice_value_d = row.invoice_value_d

        inv.total_invoice_value = row.total_invoice_value

        inv.excel_batch_id = doc.name

        inv.insert(ignore_permissions=True)

    # mark so it doesn't run again
    doc.invoice_created = 1
    doc.save(ignore_permissions=True)
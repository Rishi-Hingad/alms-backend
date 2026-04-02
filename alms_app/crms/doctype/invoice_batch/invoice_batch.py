# Copyright (c) 2026, Rishi Hingad
from pydoc import doc

from frappe import config
from frappe.model.document import Document
import frappe
import pandas as pd
from frappe.recorder import status
from frappe.utils.file_manager import get_file
from frappe.utils import getdate, user
from frappe import _
import io
from alms_app.api.send_to_leaseapp import send_to_leaseapp

class InvoiceBatch(Document):

    def autoname(self):
        from frappe.utils import now_datetime
        from frappe.model.naming import make_autoname

        now = now_datetime()

        year = now.strftime("%Y")
        month = now.strftime("%m")

        vendor = (self.vendor_name or "NA").replace(" ", "")

        prefix = f"IB-{vendor}-{year}-{month}-"

        self.name = make_autoname(prefix + ".#####")

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

VENDOR_CONFIG = {

    "Eazy Assets": {
        "required_columns": [
            "Contract No.", "Installment No.", "Billing Date"
        ],

        "field_map": {
            "contract_number": "Contract No.",
            "employee_name": "Employee Name",
            "vehicle_details": "Vehicle Details",

            "installment_no": "Installment No.",
            "billing_date": "Billing Date",

            "invoice_date_from": "Invoice date from",
            "invoice_date_to": "Invoice date to",

            "invoice_no_rental": "Rental Invoice No.",
            "invoice_value_a": "Invoice Value ( A)",

            "invoice_no_fleet": "Fleet Invoice No",
            "invoice_value_b": "Invoice Value ( B)",

            "invoice_no_road": "Road Invoice No.",
            "invoice_value_c": "Invoice Value ( C)",

            "invoice_no_insurance": "Insurance Invoice No.",
            "invoice_value_d": "Invoice Value ( D)",
        },

        "has_insurance": True,
        "use_billing_date": True,
        "use_month_for_period": False
    },

    "ALD": {
        "required_columns": [
            "Contract No.", "Inst. No.", "Month"
        ],

        "field_map": {
            "contract_number": "Contract No.",
            "employee_name": "Emp. Name",
            "vehicle_details": "Vehicle Details",
            "month": "Month",

            "installment_no": "Inst. No.",

            "invoice_no_rental": "Inv.No.",
            "invoice_date_rental": "Inv.Date",
            "invoice_value_a": "Inv.Value (A)",

            "invoice_no_fleet": "Inv.No.",
            "invoice_date_fleet": "Inv.Date",
            "invoice_value_b": "Inv.Value (B)",

            "invoice_no_road": "Inv.No.",
            "invoice_date_road": "Inv.Date",
            "invoice_value_c": "RTO ( C )",
        },

        "has_insurance": False,
        "use_billing_date": False,
        "use_month_for_period": True
    }
}

def map_row(row, config):
    mapped = {}

    for field, col in config["field_map"].items():
        val = row.get(col)

        if "value" in field:
            val = clean_amount(val)

        mapped[field] = val

    return mapped

from frappe.utils import getdate

def get_installment_dates(contract_number, installment_no, month=None):

    children = frappe.get_all(
        "Installment Details",
        filters={"parent": contract_number},
        fields=[
            "installment_no",
            "installment_start_date",
            "installment_end_date",
            "month"
        ]
    )

    for row in children:

        # match by installment_no
        if str(row.installment_no) == str(installment_no):
            return row.installment_start_date, row.installment_end_date

        # match by month (properly)
        if month and row.month:
            try:
                if getdate(row.month).month == getdate(month).month:
                    return row.installment_start_date, row.installment_end_date
            except:
                pass

    return None, None


def create_invoice_details_on_approval(doc, method):
    print("Checking conditions for creating Invoice Details from Invoice Batch:", doc.name)
    frappe.logger().info(f"Creating invoices for batch {doc.name}")

    if (doc.hr_head_status != "Approved" or doc.status != "Completed"):
        return
    
    config = VENDOR_CONFIG.get(doc.vendor_name)
    created_count = 0

    for row in doc.rows:

        if row.status != "Success":
            continue

        if frappe.db.exists("Invoice Details", {
            "contract_number": row.contract_number,
            "installment_no": row.installment_no
        }):
            continue

        inv = frappe.new_doc("Invoice Details")

        for field in config["field_map"].keys():
            if hasattr(row, field):
                setattr(inv, field, getattr(row, field))

        # ---- PERIOD FIX ---- #
        if config.get("use_month_for_period"):

            start_date, end_date = get_installment_dates(
                row.contract_number,
                row.installment_no,
                getattr(row, "month", None)
            )

            if not start_date or not end_date:
                frappe.log_error(
                    f"Installment dates missing for {row.contract_number}",
                    "ALD Date Mapping Error"
                )
                continue

            inv.invoice_date_from = start_date
            inv.invoice_date_to = end_date

            row.invoice_date_from = start_date
            row.invoice_date_to = end_date

        else:
            inv.invoice_date_from = row.invoice_date_from
            inv.invoice_date_to = row.invoice_date_to

        inv.employee_name = frappe.db.get_value(
            "Contract Master",
            row.contract_number,
            "employee_car_process_form"
        )

        inv.total_invoice_value = row.total_invoice_value
        inv.excel_batch_id = doc.name

        inv.insert(ignore_permissions=True)
        created_count += 1

    if any(r.status == "Success" for r in doc.rows):
        doc.db_set("invoice_created", 1)

    valid_rows = [ r for r in doc.rows if r.status == "Success" and r.contract_number and r.installment_no ]

    if not valid_rows:
        msg = f"No valid rows to send for {doc.name}"

        frappe.logger().warning(msg)
        doc.db_set("api_message", msg)

        return

    if not doc.lease_api_call:
        try:
            res = send_to_leaseapp(doc)
            if res.get("status") == "Success":
                doc.db_set("lease_api_call", 1)
                doc.db_set("api_message", res.get("message") or "Success")
                doc.db_set("api_log", res.get("log_name"))
            else:
                doc.db_set("api_message", "Retry failed. Check API Log.")

        except Exception:
            frappe.log_error(frappe.get_traceback(), "Lease API Failed")


@frappe.whitelist()
def retry_failed(docname):

    doc = frappe.get_doc("Invoice Batch", docname)
    config = VENDOR_CONFIG.get(doc.vendor_name)

    success = 0
    failed = 0

    rows_to_remove = []

    for frow in doc.failed_rows_table:

        try:
            if not frow.contract_number:
                raise Exception("Contract Number missing")

            if not frappe.db.exists("Contract Master", frow.contract_number):
                raise Exception("Contract not found")

            filters = {
                "contract_number": frow.contract_number,
                "installment_no": frow.installment_no
            }

            if config["use_billing_date"]:
                filters["billing_date"] = clean_date(frow.billing_date)

            # validate installment dates (if needed)
            if config.get("use_month_for_period"):
                start_date, end_date = get_installment_dates(
                    frow.contract_number,
                    frow.installment_no,
                    getattr(frow, "month", None)
                )

                if not start_date or not end_date:
                    raise Exception("Installment dates not found")

            if frappe.db.exists("Invoice Details", filters):
                raise Exception("Duplicate invoice exists")

            employee = frappe.db.get_value(
                "Contract Master",
                frow.contract_number,
                "employee_car_process_form"
            )

            doc.append("rows", {
                **frow.as_dict(),
                "status": "Success",
            })

            rows_to_remove.append(frow)
            success += 1

        except Exception as e:
            frow.status = "Error"
            frow.error_message = str(e)
            failed += 1

    for r in rows_to_remove:
        doc.remove(r)

    doc.success_rows += success
    doc.failed_rows = len(doc.failed_rows_table)
    doc.total_rows = doc.success_rows + doc.failed_rows

    if doc.failed_rows == 0 and doc.total_rows > 0:
        doc.status = "Completed"
    elif doc.success_rows > 0:
        doc.status = "Partially Completed"
    else:
        doc.status = "Failed"

    doc.save()
    # trigger invoice creation if conditions met
    create_invoice_details_on_approval(doc, None)

    return {
        "success": success,
        "failed": failed,
        "message": f"{success} Success, {failed} Failed"
    }


@frappe.whitelist()
def download_error_report(docname):

    doc = frappe.get_doc("Invoice Batch", docname)

    rows = []

    for r in doc.rows:
        if r.status == "Error":

            rows.append({
                "Row": r.row_number,
                "Contract No": r.contract_number,
                "Installment": r.installment_no,
                "Billing Date": r.billing_date if doc.vendor_name == "Eazy Assets" else "",
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
def retry_lease_api(docname):

    doc = frappe.get_doc("Invoice Batch", docname)

    if doc.hr_head_status != "Approved":
        frappe.throw("HR Head must approve first")

    if doc.status != "Completed":
        frappe.throw("Batch must be Completed")

    if doc.lease_api_call and doc.api_log:
        return {"message": "API already called successfully"}

    valid_rows = [
        r for r in doc.rows
        if r.status == "Success" and r.contract_number and r.installment_no
    ]

    if not valid_rows:
        msg = f"No valid rows to send for {doc.name}"
        doc.db_set("api_message", msg)
        return {"message": msg}

    try:
        res = send_to_leaseapp(doc)

        doc.db_set("lease_api_call", 1)

        if res.get("log_name"):
            doc.db_set("api_log", res.get("log_name"))

        if res.get("message"):
            doc.db_set("api_message", res.get("message"))

        return {
            "message": res.get("message") or "API retried successfully",
            "status": res.get("status")
        }

    except Exception:
        error = frappe.get_traceback()

        frappe.log_error(error, "Retry Lease API Failed")

        doc.db_set("api_message", "Retry failed. Check API Log.")

        return {"message": "Retry failed"}

# *********************************************

@frappe.whitelist()
def update_approval_status(docname, role, action, remarks):

    user = frappe.session.user
    user_roles = frappe.get_roles(user)

    signature = frappe.db.get_value("Employee Master", {"email_id": user}, "employee_signature") or user

    def is_admin():
        return user == "Administrator"
    
    # def is_already_processed(status):
    #     return status in ["Approved", "Rejected"]

    doc = frappe.get_doc("Invoice Batch", docname)

    # ---------------- FINANCE TEAM ---------------- #
    if role == "finance_team":

        if "Finance Team" not in user_roles and not is_admin():
            frappe.throw("Not authorized for Finance Team action")

        # if is_already_processed(doc.finance_team_status):
        #     frappe.throw("Finance Team already processed this")
        if doc.finance_head_status == "Approved":
            frappe.throw("Cannot change Finance Team after Finance Head approval")

        doc.finance_team_status = action
        doc.finance_team_user = user
        doc.finance_team_remarks = remarks
        doc.finance_team_signature = signature

    # ---------------- FINANCE HEAD ---------------- #
    elif role == "finance_head":

        if "Finance Head" not in user_roles and not is_admin():
            frappe.throw("Not authorized for Finance Head action")
            
        if doc.hr_head_status == "Approved":
            frappe.throw("Cannot change Finance Head after HR Head approval")
        
        # if is_already_processed(doc.finance_head_status):
        #     frappe.throw("Finance Head already processed this")

        if doc.finance_team_status != "Approved":
            frappe.throw("Finance Team must approve first")

        doc.finance_head_status = action
        doc.finance_head_user = user
        doc.finance_head_remarks = remarks
        doc.finance_head_signature = signature

    # ---------------- HR HEAD ---------------- #
    elif role == "hr_head":

        if "HR Head" not in user_roles and not is_admin():
            frappe.throw("Not authorized for HR Head action")
        
        # if is_already_processed(doc.hr_head_status):
        #     frappe.throw("HR Head already processed this")

        if doc.finance_head_status != "Approved":
            frappe.throw("Finance Head must approve first")

        doc.hr_head_status = action
        doc.hr_head_user = user
        doc.hr_head_remarks = remarks
        doc.hr_head_signature = signature

    else:
        frappe.throw("Invalid role")

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return "Updated"


import frappe
from frappe.utils.file_manager import get_file_path
from frappe.utils import get_url

@frappe.whitelist()
def get_file_preview_url(file_url):
    file_doc = frappe.get_doc("File", {"file_url": file_url})

    if not file_doc:
        frappe.throw("File not found")

    # Permission check (important)
    if file_doc.is_private:
        return get_url("/api/method/frappe.utils.file_manager.download_file?file_url=" + file_doc.file_url)
        # if not frappe.has_permission(file_doc.attached_to_doctype, "read", file_doc.attached_to_name):
        #     frappe.throw("No permission")

    # Convert to accessible URL
    return get_url(file_doc.file_url)
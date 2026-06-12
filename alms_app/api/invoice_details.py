import frappe
import json
import traceback
from frappe.utils import getdate
import base64


def get_file_content(file_url):
    if not file_url:
        return None

    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_path = file_doc.get_full_path()

    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return {
        "file_name": file_doc.file_name,
        "content": encoded
    }

@frappe.whitelist(allow_guest=True)
def get_invoice_batch_details(batch_date=None, vendor_name=None, name=None):

    log = frappe.new_doc("API Log")
    log.api_url = "/api/method/crms.api.get_invoice_batch_details"
    log.api_method = "GET"

    try:
        # ---- CAPTURE REQUEST ---- #
        request_data = {
            "batch_date": batch_date,
            "vendor_name": vendor_name,
            "name": name
        }

        log.api_json_body = json.dumps(request_data)

        filters = {
            "hr_head_status": "Approved",
            "status": "Completed"
        }

        if batch_date:
            filters["batch_date"] = getdate(batch_date)

        if vendor_name:
            filters["vendor_name"] = vendor_name

        if name:
            filters["name"] = name

        batch_names = frappe.get_all(
            "Invoice Batch",
            filters=filters,
            pluck="name"
        )

        if not batch_names:
            message = f"No Invoice Batch available for this particular {batch_date}."

            response = {
                "message": message,
                "data": []
            }

            log.response_data = json.dumps(response)
            log.status_code = 200
            log.status = "Success"

            log.insert(ignore_permissions=True)
            frappe.db.commit()

            return response

        result = []

        for batch_name in batch_names:
            doc = frappe.get_doc("Invoice Batch", batch_name)

            # ---- FETCH COMPANY CODE ---- #
            company_code = ""
            if doc.company:
                company_code = frappe.db.get_value(
                    "Company Master",
                    {"company_short_form": doc.company},
                    "company_code"
                )

            # ---- MAIN RESPONSE (ONLY REQUIRED FIELDS) ---- #
            batch_data = {
                "batch_name": doc.name,
                "vendor_name": doc.vendor_name,
                "company": doc.company,
                "batch_date": doc.batch_date,
                "total_value_of_rental_charges": doc.total_value_of_rental_charges,
                "total_value_of_fleet_charges": doc.total_value_of_fleet_charges,
                "total_value_of_rto": doc.total_value_of_rto,
                "total_value_of_insurance": doc.total_value_of_insurance,
                "total_value_of_company_contribution": doc.total_value_of_company_contribution,
                "total_value_of_employee_contribution": doc.total_value_of_employee_contribution,
                "total_value_of_all": doc.total_value_of_all,

                # ---- ATTACHMENTS ---- #
                "excel_file": get_file_content(doc.excel_file),
                "invoice_attachment": get_file_content(doc.invoice_attachment),

                "rows": []
            }

            # ---- CHILD TABLE PROCESSING ---- #
            for row in doc.rows:
                contract_number = row.contract_number

                employee_code = ""

                if contract_number and frappe.db.exists("Contract Master", contract_number):
                    contract_doc = frappe.get_doc("Contract Master", contract_number)

                    employee = contract_doc.get("employee_car_process_form")

                    if employee and frappe.db.exists("Employee", employee):
                        employee_code = frappe.db.get_value(
                            "Employee",
                            employee,
                            "employee_code"
                        )

                row_data = {
                    "contract_number": row.contract_number,
                    "company": row.company,
                    # "company_code": frappe.db.get_value(
                    #     "Company",
                    #     row.company,
                    #     "company_short_name"
                    # ) if row.company else "",
                    "company_code": company_code,
                    "employee_name": row.employee_name,
                    "employee_code": employee_code,
                    "cost_center": row.cost_center,
                    "vehicle_details": row.vehicle_details,
                    "billing_date": row.billing_date,
                    "invoice_date_from": row.invoice_date_from,
                    "invoice_date_to": row.invoice_date_to,
                    "total_invoice_value": row.total_invoice_value,
                    "invoice_value_a": row.invoice_value_a,
                    "invoice_value_b": row.invoice_value_b,
                    "invoice_value_c": row.invoice_value_c,
                    "invoice_value_d": row.invoice_value_d,
                    "company_contribution": row.company_contribution,
                    "employee_contribution": row.employee_contribution,
                    "installment_no": row.installment_no,
                    "month": row.month
                }

                batch_data["rows"].append(row_data)

            result.append(batch_data)

        # ---- SUCCESS LOG ---- #
        log.response_data = json.dumps(result, default=str)
        log.status_code = 200
        log.status = "Success"

        log.insert(ignore_permissions=True)
        frappe.db.commit()

        return result

    except Exception as e:

        # ---- ERROR LOG ---- #
        log.status = "Failed"
        log.error_message = str(e)
        log.traceback = traceback.format_exc()

        log.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.throw(str(e))
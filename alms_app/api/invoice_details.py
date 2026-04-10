import frappe
import json
import traceback
from frappe.utils import getdate

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

            batch_data = doc.as_dict()

            # ---- Remove unwanted fields ---- #
            fields_to_remove = [
                "failed_rows_table",
                "total_rows",
                "success_rows",
                "failed_rows",
                "progress"
            ]

            for field in fields_to_remove:
                batch_data.pop(field, None)

            # ---- Process Child Rows ---- #
            clean_rows = []

            for row in doc.rows:
                row_data = row.as_dict()

                contract_number = row.contract_number

                # ---- Fetch Contract Master Details ---- #
                contract_details = {}
                if contract_number and frappe.db.exists("Contract Master", contract_number):

                    contract_doc = frappe.get_doc("Contract Master", contract_number)

                    contract_details = {
                        "contract_start_date": contract_doc.get("contract_start_date"),
                        "contract_end_date": contract_doc.get("contract_end_date"),
                        "employee": contract_doc.get("employee_car_process_form"),
                        "company": contract_doc.get("company"),
                    }

                row_data["contract_details"] = contract_details
                clean_rows.append(row_data)

            batch_data["rows"] = clean_rows
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
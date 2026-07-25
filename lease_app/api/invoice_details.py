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

                    if employee and frappe.db.exists("ALMS Employee", employee):
                        employee_code = frappe.db.get_value("ALMS Employee",
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


def map_invoice_row(row):
    from frappe.utils import getdate

    billing_date = getdate(row.get("billing_date")) if row.get("billing_date") else None

    return {
        "contract_number": row.get("contract_number"),
        "company": row.get("company"),
        "employee_code": "",
        "cost_center": row.get("cost_center"),
        "vehicle_details": row.get("vehicle_details"),
        "billing_date": billing_date,
        "invoice_from_date": row.get("invoice_date_from"),
        "invoice_to_date": row.get("invoice_date_to"),
        "invoice_amount": row.get("total_invoice_value"),
        "invoice_value_a": row.get("invoice_value_a"),
        "invoice_value_b": row.get("invoice_value_b"),
        "invoice_value_c": row.get("invoice_value_c"),
        "invoice_value_d": row.get("invoice_value_d"),
        "company_contribution": row.get("company_contribution"),
        "employee_contribution": row.get("employee_contribution"),
        "installment_no": row.get("installment_no"),
        "month": row.get("month"),
    }


def _link_invoice_to_lease(doc):
    from frappe.utils import getdate
    from dateutil.relativedelta import relativedelta
    from datetime import date

    for child in doc.rows:
        contract_no = child.contract_number
        invoice_date = getdate(child.billing_date) if child.billing_date else None
        invoice_from_date = getdate(child.invoice_from_date) if child.invoice_from_date else None
        invoice_to_date = getdate(child.invoice_to_date) if child.invoice_to_date else None

        # 1. Contract Number Check
        car = frappe.db.get_value(
            "Vehicle Details",
            {"contract_number": contract_no},
            ["name", "vendor_company", "company_name", "employee_code_and_name"],
            as_dict=1,
        )

        if not car:
            child.lease_status = "Contract Not Found"
            continue

        car_company_code = frappe.db.get_value("Company Master", {"name": car.company_name}, "company_code")

        # 2. Company Match
        if str(car_company_code) != str(child.company_code):
            child.lease_status = "Company Mismatch"
            continue

        # 3. Employee Code Match
        if str(car.employee_code_and_name) != str(child.employee_code):
            child.lease_status = "Employee Mismatch"
            continue

        # 4. Find Lease Management
        leases = frappe.get_all(
            "Lease Management",
            filters={"car_description": car.name, "vendor": car.vendor_company, "company": car.company_name},
            fields=["name", "agreement_start_date", "agreement_end_date", "status"],
        )

        if not leases:
            child.lease_status = "Lease Not Found"
            continue

        matched = False
        if len(leases) > 0:
            for lease in leases:
                lease_doc = frappe.get_doc("Lease Management", lease.name)
                if lease.status == "Discarded":
                    if lease_doc.modifications:
                        temp = frappe.db.get_value(
                            "Lease Management",
                            lease_doc.modifications[0].modified_lease,
                            "agreement_start_date",
                        )
                        modified_date = date(temp.year, temp.month, temp.day) - relativedelta(days=1)
                        if invoice_date:
                            if not (
                                lease.agreement_start_date <= invoice_from_date
                                and invoice_to_date <= modified_date
                            ):
                                child.lease_status = "Date Out of Range for lease " + str(lease_doc.name)
                                continue
                        lease_doc.append(
                            "invoice_details",
                            {
                                "amount": child.invoice_amount,
                                "from_date": child.invoice_from_date,
                                "to_date": child.invoice_to_date,
                            },
                        )

                        lease_doc.save(ignore_permissions=True)

                        child.lease_reference = lease.name
                        child.lease_status = "Linked"

                        matched = True
                        break
                if lease.status == "Modified":
                    if invoice_date:
                        if not (
                            lease_doc.agreement_start_date <= invoice_from_date
                            and invoice_to_date <= lease_doc.agreement_end_date
                        ):
                            child.lease_status = "Date Out of Range for lease " + str(lease_doc.name)
                            continue
                    lease_doc.append(
                        "invoice_details",
                        {
                            "amount": child.invoice_amount,
                            "from_date": child.invoice_from_date,
                            "to_date": child.invoice_to_date,
                        },
                    )

                    lease_doc.save(ignore_permissions=True)

                    child.lease_reference = lease.name
                    child.lease_status = "Linked"

                    matched = True
                    break

                if lease.status == "Terminated":
                    child.lease_status = "Terminated Lease"
                    if invoice_date:
                        if not (
                            lease_doc.agreement_start_date <= invoice_from_date
                            and invoice_to_date <= lease_doc.termination_date
                        ):
                            child.lease_status = "Date Out of Range for lease " + str(lease_doc.name)
                            continue
                    lease_doc.append(
                        "invoice_details",
                        {
                            "amount": child.invoice_amount,
                            "from_date": child.invoice_from_date,
                            "to_date": child.invoice_to_date,
                        },
                    )

                    lease_doc.save(ignore_permissions=True)

                    child.lease_reference = lease.name
                    child.lease_status = "Linked"

                    matched = True
                    break

        if not matched and not child.lease_status:
            child.lease_status = "Lease Not Found"
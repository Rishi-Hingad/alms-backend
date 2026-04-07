# Copyright (c) 2026, Rishi Hingad

import frappe
from frappe.model.document import Document
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
from frappe.utils import getdate, today


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


# ---------------- COMMON HELPERS ---------------- #

def clean_amount(val):
    if not val:
        return 0
    return float(str(val).replace(",", "").strip())


def clean_date(val):
    if not val:
        return None
    return getdate(val)


def normalize(text):
    if not text:
        return ""
    return (
        str(text)
        .strip()
        .lower()
        .replace(" ", "")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
        .replace("_", "")
    )


def make_link(doctype, name=None, label=None):
    route = doctype.replace(" ", "-").lower()
    url = f"/app/{route}/{name}" if name else f"/app/{route}"
    label = label or f"Open {doctype}"
    return f'<a href="{url}" target="_blank">{label}</a>'


# ---------------- EXCEL MAPPING ---------------- #

def get_excel_mapping(vendor):
    doc = frappe.get_doc("Excel Mapper", vendor)

    mapping = []

    for row in doc.excel_row_mapper:
        if not row.field_column:
            continue

        mapping.append({
            "fieldname": row.field_column,
            "index": row.column_index,
            "normalized_key": normalize(row.excel_column)
        })

    return mapping


# ---------------- MAIN ENTRY ---------------- #

@frappe.whitelist()
def upload_invoice_excel(file_url, vendor, user_email):
    return process_invoice(file_url, vendor, user_email)


# ---------------- CORE ENGINE ---------------- #
def process_invoice(file_url, vendor, user_email):
    print(f"Processing invoice upload for vendor: {vendor} by user: {user_email}")
    rows = read_xlsx_file_from_attached_file(file_url)
    if not rows or not rows[0]:
        frappe.throw("Excel file is empty or invalid")

    # ---------------- HEADERS ---------------- #
    headers_raw = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
    headers_norm = []
    header_count = {}
    for h in headers_raw:
        key = normalize(h)
        if key in header_count:
            header_count[key] += 1
            key = f"{key}_{header_count[key]}"
        else:
            header_count[key] = 0
        headers_norm.append(key)

    data = rows[1:]
    header_map = get_excel_mapping(vendor)

    # ---------------- INIT ---------------- #
    created = failed = 0
    valid_count = 0
    company = None

    total_value_all = 0
    total_company_contrib = 0
    total_employee_contrib = 0
    total_rental = 0
    total_fleet = 0
    total_rto = 0
    total_insurance = 0

    batch = frappe.new_doc("Invoice Batch")
    batch.vendor_name = vendor
    batch.excel_file = file_url
    batch.excel_uploading_by = user_email
    batch.status = "Processing"
    batch.insert(ignore_permissions=True)

    # ---------------- PROCESS ROWS ---------------- #
    for idx, row in enumerate(data, start=1):
        row_dict = dict(zip(headers_norm, row))
        mapped = {}

        # Map Excel columns to child fields
        for m in header_map:
            fieldname = m.get("fieldname")
            col_idx = m.get("index")
            key = m.get("normalized_key")

            value = None
            
            if col_idx is not None:
                try:
                    value = row[col_idx]
                except IndexError:
                    value = None

            mapped[fieldname] = value

        # Initialize calculation variables
        total_invoice_value = 0
        company_contribution = 0
        employee_contribution = 0

        try:
            # ---------------- VALIDATIONS ---------------- #
            contract_number = str(mapped.get("contract_number") or "").strip()
            print(f"Row {idx} raw contract: {contract_number}")

            if not contract_number:
                raise Exception(f"Invalid contract: {contract_number}")

            # Vendor-aware contract resolution
            if vendor == "ALD":
                contract_doc = frappe.db.get_value(
                    "Contract Master",
                    {
                        "vendor": vendor,
                        "name": contract_number
                    },
                    ["name", "company"],
                    as_dict=True
                )

                if not contract_doc:
                    raise Exception(f"Contract not found: {contract_number}")

                # replace with actual doc name (like ABC-60857)
                contract_number = contract_doc.name

                if not company:
                    company = contract_doc.company

            else:
                # For vendors like Eazy Assets
                if "-" not in contract_number:
                    raise Exception(f"Invalid contract: {contract_number}")

                if not company:
                    company = contract_number.split("-")[0].strip()

                if not frappe.db.exists("Contract Master", contract_number):
                    raise Exception(f"Contract not found: {contract_number}")

            installment_no = str(mapped.get("installment_no") or "").strip()
            if not installment_no:
                raise Exception("Installment number missing")

            if frappe.db.exists("Invoice Details", {"contract_number": contract_number, "installment_no": installment_no}):
                raise Exception(f"Duplicate invoice for {contract_number} - {installment_no}")

            employee_name = frappe.db.get_value("Contract Master", contract_number, "employee_car_process_form")
            if not employee_name:
                raise Exception(f"Employee not linked to {contract_number}")

            # ---------------- AMOUNTS ---------------- #
            a = float(clean_amount(mapped.get("invoice_value_a")))
            b = float(clean_amount(mapped.get("invoice_value_b")))
            c = float(clean_amount(mapped.get("invoice_value_c")))
            d = float(clean_amount(mapped.get("invoice_value_d")))
            total_rental += a
            total_fleet += b
            total_rto += c
            total_insurance += d
            total_invoice_value = a + b + c + d
            print(f"Row {idx} amounts: A={a}, B={b}, C={c}, D={d}, Total={total_invoice_value}")

            # ---------------- COST CENTER ---------------- #
            cost_center = frappe.db.get_value("Employee Master", employee_name, "cost_center")
            if not cost_center:
                raise Exception("Missing cost center")

            # ---------------- CONTRIBUTIONS ---------------- #
            deduction = frappe.db.get_value(
                "Company and Employee Deduction",
                {"employee_name": employee_name},
                ["finance_team_status", "finance_head_status", "quarterly_payment", "employee_quarterly_payment"],
                as_dict=True,
                order_by="creation desc"
            )

            if not deduction:
                raise Exception("Deduction missing")
            if deduction.finance_team_status != "Approved" or deduction.finance_head_status != "Approved":
                raise Exception("Deduction not approved")

            company_contribution = float(deduction.quarterly_payment or 0)
            employee_contribution = float(deduction.employee_quarterly_payment or 0)
            print(f"Row {idx} contributions: Company={company_contribution}, Employee={employee_contribution}")

            # ---------------- APPEND CHILD ROW ---------------- #
            child_meta = frappe.get_meta("Invoice Import Row")
            valid_fields = {df.fieldname for df in child_meta.fields}

            success_row = {
                "row_number": idx,
                "status": "Success"
            }

            # include all mapped fields
            for k, v in mapped.items():
                if k in valid_fields:
                    success_row[k] = v

            # override / add system fields
            success_row.update({
                "contract_number": contract_number,
                "employee_name": employee_name,
                "installment_no": installment_no,
                "total_invoice_value": total_invoice_value,
                "cost_center": cost_center,
                "company_contribution": company_contribution,
                "employee_contribution": employee_contribution
            })

            batch.append("rows", success_row)

            # accumulate totals for parent
            total_value_all += total_invoice_value
            total_company_contrib += company_contribution
            total_employee_contrib += employee_contribution

            valid_count += 1
            created += 1

        # ---------------- HANDLE FAILED ROW ---------------- #
        except Exception as e:
            failed += 1
            print(f"Row {idx} failed: {e}")

            # Get all valid fields from child doctype
            child_meta = frappe.get_meta("Invoice Import Row")
            valid_fields = {df.fieldname for df in child_meta.fields}

            # Base failed row with mapped fields that exist in child
            failed_row = {"row_number": idx, "status": "Failed", "error_message": str(e)}
            for k, v in mapped.items():
                if k in valid_fields:
                    failed_row[k] = v

            # Add calculated fields even if not in mapped
            failed_row.update({
                "total_invoice_value": total_invoice_value,
                "company_contribution": company_contribution,
                "employee_contribution": employee_contribution,
                "cost_center": mapped.get("cost_center") or ""
            })

            # Append to failed_rows_table
            batch.append("failed_rows_table", failed_row)

    # ---------------- FINALIZE PARENT ---------------- #
    print(f"Final totals: Total Invoice={total_value_all}, Company Contribution={total_company_contrib}, Employee Contribution={total_employee_contrib}")

    batch.success_rows = created
    batch.failed_rows = failed
    batch.total_rows = created + failed
    batch.status = "Failed" if failed else "Completed"
    batch.batch_date = today()
    batch.company = company
    batch.no_of_invoice = valid_count

    batch.total_value_of_all = total_value_all
    batch.total_value_of_rental_charges = total_rental
    batch.total_value_of_fleet_charges = total_fleet
    batch.total_value_of_rto = total_rto
    batch.total_value_of_insurance = total_insurance
    batch.total_value_of_company_contribution = total_company_contrib
    batch.total_value_of_employee_contribution = total_employee_contrib
    batch.save()
    frappe.db.commit()

    return f"{created} success, {failed} failed"
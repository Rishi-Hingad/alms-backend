# Copyright (c) 2025, Rishi Hingad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class VehicleDetails(Document):

    def autoname(self):
        self.name = self.employee_code_and_name

    def on_update(self):
        self.sync_lease_management()

    def sync_lease_management(self):
        installment_amount = 0
        if self.get("installment_payment") and len(self.installment_payment) > 0:
            installment_amount = self.installment_payment[0].installment_amount or 0
            
        is_easy_asset = (self.vendor_company == "Easy Asset")
        report_type = "Quarterly" if is_easy_asset else "Monthly"
        monthly_rent = (installment_amount / 3) if is_easy_asset else installment_amount
        
        existing_lease = frappe.db.get_value("Lease Management", {"car_description": self.name}, "name")
        
        if existing_lease:
            lease = frappe.get_doc("Lease Management", existing_lease)
        else:
            lease = frappe.new_doc("Lease Management")
            lease.car_description = self.name
            lease.type_of_asset = "Car"
            lease.calculation_rate_type = "Monthly Rate"
            
        lease.contract_number = self.get("contract_number")
        lease.company = self.get("company_name")
        lease.vendor = self.get("vendor_company")
        lease.agreement_start_date = self.get("date_begin")
        lease.agreement_end_date = self.get("date_end")
        lease.agreement = self.get("contract_document")
        lease.monthly_rent = monthly_rent
        lease.type_of_report = report_type
        
        try:
            lease.flags.ignore_mandatory = True
            lease.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error syncing Lease Management for {self.name}: {str(e)}", "Lease Sync Error")

@frappe.whitelist()
def send_car_allotment_email(docname, employee_code, file_url):
    print(f"[DEBUG] send_car_allotment_email → docname={docname}, employee_code={employee_code}, file_url={file_url}")
    _send_vehicle_email(employee_code, file_url, "Car Allotment Letter")

@frappe.whitelist()
def send_rc_book_email(docname, employee_code, file_url):
    print("\n[DEBUG] send_rc_book_email called")
    print(f" - docname: {docname}")
    print(f" - employee_code: {employee_code}")
    print(f" - file_url: {file_url}")
    _send_vehicle_email(employee_code, file_url, "RC Book")


def _send_vehicle_email(employee_code, file_url, doc_type):
    print(f"\n[DEBUG] _send_vehicle_email START for {doc_type}")
    print(f" - employee_code: {employee_code}")
    print(f" - file_url: {file_url}")

    # Fetch employee email
    employee = frappe.get_doc("Employee", employee_code)
    recipient = employee.email_id

    if not recipient:
        frappe.throw("Employee has no email address set.")

    # Fetch file
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    site_config = frappe.get_site_config()
    bcc_emails = site_config.get("bcc_email", [])

    # Email body
    subject = f"{doc_type} Uploaded"
    message = f"Dear {employee.employee_name},<br><br>Your {doc_type} has been uploaded.<br>Attached below."

    # Send email
    frappe.sendmail(
        recipients=[recipient],
        subject=subject,
        message=message,
        attachments=[{
            "fname": file_doc.file_name,
            "fcontent": file_doc.get_content()
        }],
        bcc=bcc_emails
    )

    print(f"[DEBUG] Email sent successfully for {doc_type}")
    frappe.msgprint(f"{doc_type} email sent successfully to {recipient}")
    return f"{doc_type} email sent successfully."
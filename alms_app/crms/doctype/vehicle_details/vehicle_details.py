# Copyright (c) 2025, Rishi Hingad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class VehicleDetails(Document):

    def autoname(self):
        self.name = self.employee_code_and_name

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
    employee = frappe.get_doc("ALMS Employee", employee_code)
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
# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

import smtplib
from email.message import EmailMessage
from frappe.model.document import Document
from frappe.utils import now
import frappe

class EmployeeMaster(Document):
    pass
@frappe.whitelist(allow_guest=True)
def get_eligibility_from_designation(designation):
    if not designation:
        return {"error": "No designation provided"}

    doc = frappe.get_doc("Employee Designation", designation)
    return {"eligibility": doc.custom_eligibility}

# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

# import frappe
from datetime import datetime
from frappe.model.document import Document
class VendorRentalInvoice(Document):
    def validate(self):
        # Define date format
        date_format = "%d-%m-%Y"
        
        # Get dates from the form fields
        invoice_date_from = self.invoice_date_from
        invoice_date_to = self.invoice_date_to
        
        # Parse dates and calculate days
        try:
            date_from = datetime.strptime(invoice_date_from, date_format)
            date_to = datetime.strptime(invoice_date_to, date_format)
            
            # Calculate difference in days and include start date
            days_between = (date_to - date_from).days + 1
            
            # Ensure non-negative result
            self.number_of_billing_days = days_between if days_between > 0 else 0

        except ValueError:
            # If parsing fails, set billing days to 0
            self.number_of_billing_days = 0


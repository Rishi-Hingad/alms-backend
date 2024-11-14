# Copyright (c) 2024, Harsh and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import pandas as pd

@frappe.whitelist()
def process_file(file_url):
    try:
        # Fetch the file's path on the server (split URL to get file name)
        _file = frappe.get_doc("File", {"file_url": file_url.split("/")[-1]})
        file_path = _file.get_full_path()

        # Use pandas to read the Excel file
        df = pd.read_excel(file_path, engine='openpyxl')

        # Assuming the data is in the first row of the Excel file
        data = df.iloc[0].to_dict()

        # Map the Excel columns to Doctype fields
        location = data.get('location')
        kms = data.get('kms')
        variant = data.get('variant')
        # Map additional fields as necessary

        # Return the data to the client-side script
        return {
            'location': location,
            'kms': kms,
            'variant': variant,
            # Add additional fields as necessary
        }
    except Exception as e:
        frappe.log_error(message=str(e), title="Error in processing file")
        return {
            'error': "There was an issue processing the file. Please check the logs."
        }

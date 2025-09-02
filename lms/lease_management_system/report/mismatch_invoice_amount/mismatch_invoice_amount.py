# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

def execute(filters=None):
	data=[]
	columns = [
        {"label": "Lease", "fieldname": "lease", "fieldtype": "Data", "width": 150},
        {"label": "Month Start Date", "fieldname": "month_start_date", "fieldtype": "Date", "width": 150},
        {"label": "Month End Date", "fieldname": "month_end_date", "fieldtype": "Date", "width": 150},
        {"label": "Calculated Rent", "fieldname": "calculated_rent", "fieldtype": "Currency", "width": 200,"precision":4},
		{"label": "Invoice From Date", "fieldname": "invoice_from_date", "fieldtype": "Date", "width": 150},
        {"label": "Invoice To Date", "fieldname": "invoice_to_date", "fieldtype": "Date", "width": 150},
        {"label": "Invoice Amount", "fieldname": "invoice_amount", "fieldtype": "Currency", "width": 200,"precision":4}
    ]

	leases = frappe.get_all(
        "Lease Management",
        order_by="name asc",
        fields=["name"]
    )

	for lease in leases:
		lease_doc=frappe.get_doc("Lease Management",lease.name)
		rent_timeline=lease_doc.get_lease_rent_timeline()
		if lease_doc.invoice_details and len(lease_doc.invoice_details)>0:
			for child in lease_doc.invoice_details:
				mismatch=child.is_mismatch
				if int(mismatch) == 1:
					from_date = child.from_date
					inv_month=from_date.strftime("%Y-%m")
					expected_rent=rent_timeline.get(inv_month)
					monthly_data=lease_doc.get_lease_monthly_data()
					month=monthly_data.get(from_date.strftime("%Y-%m"))
					if not month:
						continue
					if expected_rent is None:
						continue
					data.append({
						"lease":lease.name,
						"month_start_date": month[0],
						"month_end_date": month[1],
						"calculated_rent":expected_rent,
						"invoice_from_date":child.from_date,
						"invoice_to_date":child.to_date,
						"invoice_amount":child.amount
					})

	return columns, data
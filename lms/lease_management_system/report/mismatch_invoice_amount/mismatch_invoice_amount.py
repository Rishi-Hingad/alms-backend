# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange

def execute(filters=None):
	data=[]
	columns = [
        {"label": "Lease", "fieldname": "lease", "fieldtype": "Data", "width": 200},
        # {"label": "Month Start Date", "fieldname": "month_start_date", "fieldtype": "Date", "width": 150},
        # {"label": "Month End Date", "fieldname": "month_end_date", "fieldtype": "Date", "width": 150},
		{"label": "Invoice From Date", "fieldname": "invoice_from_date", "fieldtype": "Date", "width": 150},
        {"label": "Invoice To Date", "fieldname": "invoice_to_date", "fieldtype": "Date", "width": 150},
        {"label": "Calculated Rent", "fieldname": "calculated_rent", "fieldtype": "Currency", "width": 200,"precision":4},
        {"label": "Tax (%)", "fieldname": "tax", "fieldtype": "Percentage", "width": 100},
        {"label": "Taxable Amount", "fieldname": "taxable_amount", "fieldtype": "Currency", "width": 200,"precision":4},
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
		monthly_data=lease_doc.get_lease_monthly_data()
		if lease_doc.invoice_details and len(lease_doc.invoice_details)>0:
			for child in lease_doc.invoice_details:
				if child.is_mismatch is None:
					continue
				mismatch=child.is_mismatch
				if int(mismatch) == 1:
					from_date = child.from_date
					to_date = child.to_date
					date_ranges=[]
					exp_rent=[]
					current=from_date
					while current<=to_date:
						start_date=current
						_,last_day=monthrange(current.year, current.month)
						end_date=datetime(current.year, current.month, last_day)

						if end_date.date()>to_date:
							end_date=to_date

						date_ranges.append([start_date,end_date])

						if current.month==12:
							current=current.replace(year=current.year+1,month=1,day=1)
						else:
							current=current.replace(month=current.month+1,day=1)
					
					for i in range(len(date_ranges)):
						dates=date_ranges[i]
						start_date=dates[0]
						end_date=dates[1]
						inv_month=start_date.strftime("%Y-%m")
						# lease_data=monthly_data.get(inv_month,0)
						# ms_date=lease_data[0]
						# me_date=lease_data[1]
						# frappe.msgprint(str(ms_date)+"-"+str(me_date)+" "+str(start_date.strftime("%Y-%m-%d"))+"\\"+str(end_date.strftime("%Y-%m-%d")))
						# if start_date.strftime("%Y-%m-%d")==ms_date and end_date.strftime("%Y-%m-%d")==me_date:
						exp_rent.append(rent_timeline.get(inv_month))
						
					expected_rent=0.0
					for i in range(len(exp_rent)):
						expected_rent+=exp_rent[i]

					# inv_month=from_date.strftime("%Y-%m")
					# expected_rent=rent_timeline.get(inv_month)
					# actual_amount=float(child.amount)
					tax=float(child.tax)

					if int(child.with_tax)==1:
						calc_amount=expected_rent+((tax*expected_rent)/100)
					else:
						calc_amount=expected_rent
					monthly_data=lease_doc.get_lease_monthly_data()
					month=monthly_data.get(from_date.strftime("%Y-%m"))
					if not month:
						continue
					if expected_rent is None:
						continue
					data.append({
						"lease":lease.name,
						# "month_start_date": month[0],
						# "month_end_date": month[1],
						"invoice_from_date":child.from_date,
						"invoice_to_date":child.to_date,
						"calculated_rent":expected_rent,
						"tax":child.tax,
						"taxable_amount":calc_amount,
						"invoice_amount":child.amount
					})

	return columns, data

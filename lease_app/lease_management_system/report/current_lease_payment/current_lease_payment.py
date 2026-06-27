# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

from calendar import monthrange
from datetime import date, datetime, timedelta

import frappe
from dateutil.relativedelta import relativedelta
from frappe import _ as translate
from frappe.desk.query_report import run
from frappe.utils import getdate


def execute(filters=None):
	data = []
	columns = [
		{"label": translate("Lease"), "fieldname": "lease", "fieldtype": "Data", "width": 200},
		{"label": "Month Start Date", "fieldname": "month_start_date", "fieldtype": "Date", "width": 150},
		{"label": "Month End Date", "fieldname": "month_end_date", "fieldtype": "Date", "width": 150},
		{
			"label": translate("Total Rent"),
			"fieldname": "total_rent",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 4,
		},
		{
			"label": translate("Payment Status"),
			"fieldname": "payment_status",
			"fieldtype": "Data",
			"width": 200,
		},
	]

	today = frappe.utils.nowdate()
	if isinstance(today, str):
		today = datetime.strptime(today, "%Y-%m-%d")

	current_month = today.strftime("%Y-%m")
	lease_status = "Pending"
	ms_date = None
	me_date = None

	leases = frappe.get_all(
		"Lease Management",
		filters={
			"agreement_start_date": ("<=", today),
			"agreement_end_date": (">=", today),
			"type_of_asset": "Immovable",
		},
		order_by="name asc",
		fields=["name"],
	)
	for lease in leases:
		lease_doc = frappe.get_doc("Lease Management", lease.name)
		terminated_on = None
		discarded_on = None
		# timeline = lease_doc.get_lease_rent_timeline()
		# mdata = lease_doc.get_lease_monthly_data()
		# lease_data = mdata.get(current_month, 0)
		# # inv_attachment=lease_doc.get_invoice_attachments_with_dates()
		# if not lease_data and not isinstance(lease_data, list):
		# 	continue
		# else:
		# 	ms_date = lease_data[0]
		# 	me_date = lease_data[1]
		# rent = timeline.get(current_month, 0)

		if lease_doc.termination_date:
			if (lease_doc.termination_date).strftime("%Y-%m") == current_month:
				terminated_on = lease_doc.termination_date
			if (lease_doc.termination_date).strftime("%Y-%m") < current_month:
				continue
		if lease_doc.status == "Discarded":
			if lease_doc.modifications:
				modified_start = frappe.db.get_value(
					"Lease Management", lease_doc.modifications[0].modified_lease, "agreement_start_date"
				)
				temp = date(modified_start.year, modified_start.month, modified_start.day) - relativedelta(
					days=1
				)
				if (temp).strftime("%Y-%m") == current_month:
					discarded_on = temp
				if (temp).strftime("%Y-%m") < current_month:
					continue

		report_data = run("Lease Report", filters={"docname": lease.name})

		rows = report_data.get("result", [])

		month_map = {
			getdate(row.get("month_start_date")).strftime("%Y-%m"): {
				"mlp": row.get("mlp"),
				"month_start_date": getdate(row.get("month_start_date")),
				"month_end_date": getdate(row.get("month_end_date")),
			}
			for row in rows
			if row.get("month_start_date") and row.get("month_end_date") and row.get("mlp") is not None
		}

		lease_data = month_map.get(current_month)

		if not lease_data:
			continue

		ms_date = lease_data["month_start_date"]
		me_date = lease_data["month_end_date"]
		rent = lease_data["mlp"]

		if terminated_on:
			total_days = (lease_data["month_end_date"] - lease_data["month_start_date"]).days + 1
			used_days = (terminated_on - ms_date).days + 1
			me_date = terminated_on
			rent = rent * (used_days / total_days)
		if discarded_on:
			total_days = (lease_data["month_end_date"] - lease_data["month_start_date"]).days + 1
			used_days = (discarded_on - ms_date).days + 1
			me_date = discarded_on
			rent = rent * (used_days / total_days)

		# inv_dates=[]
		# for i in range(len(inv_attachment)):
		#     record=inv_attachment[i]
		#     inv_dates.append(record["uploaded_on"])

		if len(lease_doc.invoice_details) > 0:
			# for r in lease_doc.invoice_details:
			#     if r.payment_status=="Paid":
			#         lease_status="Paid"
			#         break
			# else:
			#     if today.date()>me_date:
			#         lease_status="Was Due on "+str(me_date)

			for child in lease_doc.invoice_details:
				from_date = child.from_date
				to_date = child.to_date
				date_ranges = []
				current = from_date
				while current <= to_date:
					start_date = current
					_, last_day = monthrange(current.year, current.month)
					end_date = datetime(current.year, current.month, last_day)

					if end_date.date() > to_date:
						end_date = to_date

					# date_ranges.append(start_date.strftime("%Y-%m-%d"))
					# date_ranges.append(end_date.strftime("%Y-%m-%d"))
					if ms_date.strftime("%Y-%m-%d") == start_date.strftime("%Y-%m-%d") or me_date.strftime(
						"%Y-%m-%d"
					) == end_date.strftime("%Y-%m-%d"):
						date_ranges.append([start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")])

					if current.month == 12:
						current = current.replace(year=current.year + 1, month=1, day=1)
					else:
						current = current.replace(month=current.month + 1, day=1)

				# frappe.msgprint(lease.name+"==="+str(date_ranges)+" len="+str(len(date_ranges)))
				if len(date_ranges) > 0:
					for i in range(len(date_ranges)):
						rsdate, redate = date_ranges[i]
						if ms_date.strftime("%Y-%m-%d") == rsdate or me_date.strftime("%Y-%m-%d") == redate:
							# frappe.msgprint("Yes"+" "+child.payment_status+" || "+str())+" || "+str(me_date.strftime("%Y-%m-%d"))+" ** "+str(date_ranges[i]))
							lease_status = child.payment_status
							break
		else:
			# if today.date()>me_date:
			#         lease_status="Was Due on "+str(me_date)
			if today.date() >= me_date:
				lease_status = "Due"
			else:
				lease_status = "Pending"

		# for r in lease_doc.invoice_details:
		#     # inv_date=r.invoice_date
		#     for i in range(len(inv_dates)):
		#         if r.payment_status=="Paid":
		#             # lease_status="Paid on "+str(inv_dates[i])
		#             lease_status="Paid"
		#             break
		#         # if inv_dates[i].strftime("%Y-%m") and (r.to_date.strftime("%Y-%m")==current_month or r.from_date.strftime("%Y-%m")==current_month):
		#         #     lease_status="Paid on "+str(inv_dates[i])
		#         #     break
		#     # if inv_date.strftime("%Y-%m")==current_month:
		#     #     lease_status="Paid on "+str(inv_date)
		#     else:
		#         if today.date()>me_date:
		#             lease_status="Was Due on "+str(me_date)
		if rent is not None and lease_status == "":
			if today.date() >= me_date:
				lease_status = "Due"
			else:
				lease_status = "Pending"

		data.append(
			{
				"lease": lease.name,
				"month_start_date": ms_date,
				"month_end_date": me_date,
				"total_rent": rent,
				"payment_status": lease_status,
			}
		)
		lease_status = "Pending"

	return columns, data

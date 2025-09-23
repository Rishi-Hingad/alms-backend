# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange

def execute(filters=None):
	if not filters:
		return [], []

	docname = filters.get("docname")

	if not docname:
		frappe.throw("Please select a Lease Agreement.")

	doc = frappe.get_doc("Lease Management", docname)

	start_date = doc.agreement_start_date
	end_date = doc.agreement_end_date

	if not start_date or not end_date:
		frappe.throw("Start Date or End Date not found in Lease Agreement.")

	# 🔁 Convert to datetime if they are date objects
	if isinstance(start_date, date) and not isinstance(start_date, datetime):
		start_date = datetime.combine(start_date, datetime.min.time())
	if isinstance(end_date, date) and not isinstance(end_date, datetime):
		end_date = datetime.combine(end_date, datetime.min.time())

	mlp = float(doc.monthly_rent)
	mlp2 = float(doc.monthly_rent)

	disc_doc = float(doc.discounting_rate) / 100
	if doc.calculation_rate_type == "Daily Rate":
		daily_rate = (1 + disc_doc) ** (1 / 365) - 1

	arg_sd=start_date
	arg_ed=end_date+ timedelta(days=1)
	diff_years = relativedelta(arg_ed,arg_sd)
	diff_years=int(str(diff_years.years))


	columns = [
		{"label": "Month Start Date", "fieldname": "month_start_date", "fieldtype": "Date", "width": 120},
		{"label": "Month End Date", "fieldname": "month_end_date", "fieldtype": "Date", "width": 120},
		{"label": "Days in Month", "fieldname": "days_in_month", "fieldtype": "Int", "width": 120},
		{"label": "Minimum Lease Payment (MLP)", "fieldname": "mlp", "fieldtype": "Currency", "width": 180,"precision":4},
		{"label": "Present Value of MLP", "fieldname": "pv", "fieldtype": "Currency", "width": 180},
		{"label": "Depreciation on Right to Use", "fieldname": "depreciation", "fieldtype": "Currency", "width": 200},
		{"label": "Written Down Value (WDV)", "fieldname": "wdv", "fieldtype": "Currency", "width": 180},
		{"label": "Interest Cost", "fieldname": "interest_cost", "fieldtype": "Currency", "width": 150},
		{"label": "Closing Liability", "fieldname": "closing_liability", "fieldtype": "Currency", "width": 180}
	]

	current_date = start_date
	ndays = 0
	# nmonths = 0
	total_mlp = 0
	total_pv = 0
	total_depre = 0
	pv_arr = ['']
	cnt = 0
	data = []
	
	# First loop PV calculations
	while current_date <= end_date:
		cnt += 1
		month_start = current_date
		_, last_day = monthrange(current_date.year, current_date.month)
		month_end = datetime(current_date.year, current_date.month, last_day)
		month_start2=current_date.replace(day=1)
		_,last_day2=monthrange(current_date.year, current_date.month)
		month_end2=datetime(current_date.year, current_date.month, last_day2)
		date_difference2 = month_end2 - month_start2
		total_days_of_month = date_difference2.days +1

		if end_date < month_end:
			month_end = end_date

		date_difference = month_end - month_start
		n=date_difference.days+1

		if n<total_days_of_month:
			prev_mlp=mlp
			mlp=mlp*n/total_days_of_month
			
			total_mlp+=mlp
			if cnt==1:
				pv=mlp
				pv_arr.append(pv)
			else:
				pv=mlp/((1+daily_rate)**ndays)
				pv_arr.append(pv)
			mlp=prev_mlp

		else:
			total_mlp+=mlp
			if cnt==1:
				pv=mlp
				pv_arr.append(pv)
			else:
				pv=mlp/((1+daily_rate)**ndays)
				pv_arr.append(pv)

		total_pv += pv
		ndays += n

		# Move to next month
		if current_date.month == 12:
			current_date = datetime(current_date.year + 1, 1, 1)
		else:
			current_date = datetime(current_date.year, current_date.month + 1, 1)

	prev_closing_liability = total_pv
	total_days = ndays

	# Second loop depreciation calculation
	current_date2 = start_date
	cnt1 = 0
	while current_date2 <= end_date:
		cnt1 += 1
		month_start = current_date2
		_, last_day = monthrange(current_date2.year, current_date2.month)
		month_end = datetime(current_date2.year, current_date2.month, last_day)
		if end_date < month_end:
			month_end = end_date

		date_difference = month_end - month_start
		n = date_difference.days +1

		if (doc.previous_wdv)!=0:
			prev_closing_liability_wdv=float(doc.previous_wdv)
			depreciation=(n/total_days)*prev_closing_liability_wdv
			total_depre+=depreciation
		else:
			depreciation=(n/total_days)*prev_closing_liability
			total_depre+=depreciation

		# Move to next month
		if current_date2.month == 12:
			current_date2 = datetime(current_date2.year + 1, 1, 1)
		else:
			current_date2 = datetime(current_date2.year, current_date2.month + 1, 1)

	prev_wdv = float(doc.previous_wdv) if doc.previous_wdv != 0 else total_depre
	wdv = prev_wdv
	closing_liability = prev_closing_liability
	total_interest_cost = 0

	# Append opening balance row
	data.append({
		"month_start_date": "",
		"month_end_date": "",
		"days_in_month": "",
		"mlp": "",
		"pv": "",
		"depreciation": "",
		"wdv": round(wdv, 3),
		"interest_cost": "",
		"closing_liability": round(closing_liability, 3)
	})

	# Third loop final report generation
	current_date3 = start_date
	cnt2 = 0
	while current_date3 <= end_date:
		cnt2 += 1
		month_start = current_date3
		_, last_day = monthrange(current_date3.year, current_date3.month)
		month_end = datetime(current_date3.year, current_date3.month, last_day)
		if end_date < month_end:
			month_end = end_date
		
		month_start2=current_date3.replace(day=1)
		_,last_day2=monthrange(current_date3.year, current_date3.month)
		month_end2=datetime(current_date3.year, current_date3.month, last_day2)
		date_difference2 = month_end2 - month_start2
		total_days_of_month = date_difference2.days +1

		date_difference = month_end - month_start
		n = date_difference.days +1

		if n<total_days_of_month:
			prev_mlp2=mlp2
			mlp2=mlp2*n/total_days_of_month
						
			interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
			total_interest_cost+=interest_cost
			closing_liability=closing_liability+interest_cost-mlp2

			if (doc.previous_wdv)!=0:
				prev_closing_liability_wdv=float(doc.previous_wdv)
				depreciation=(n/total_days)*prev_closing_liability_wdv
				total_depre+=depreciation
			else:
				depreciation=(n/total_days)*prev_closing_liability
				total_depre+=depreciation

			row = {
				"month_start_date": month_start.date(),
				"month_end_date": month_end.date(),
				"days_in_month": n,
				"mlp": mlp2,
				"pv": pv_arr[cnt2] if cnt2 < len(pv_arr) else '',
				"depreciation": round(depreciation, 3),
				"wdv": round(wdv, 3),
				"interest_cost": round(interest_cost, 3),
				"closing_liability": round(closing_liability, 3)
			}
			data.append(row)
			mlp2=prev_mlp2

		else:
			interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
			total_interest_cost+=interest_cost
			closing_liability=closing_liability+interest_cost-mlp2

			if (doc.previous_wdv)!=0:
				prev_closing_liability_wdv=float(doc.previous_wdv)
				depreciation=(n/total_days)*prev_closing_liability_wdv
				wdv-=depreciation
			else:
				depreciation=(n/total_days)*prev_closing_liability
				wdv-=depreciation
			row = {
				"month_start_date": month_start.date(),
				"month_end_date": month_end.date(),
				"days_in_month": n,
				"mlp": mlp2,
				"pv": pv_arr[cnt2] if cnt2 < len(pv_arr) else '',
				"depreciation": round(depreciation, 3),
				"wdv": round(wdv, 3),
				"interest_cost": round(interest_cost, 3),
				"closing_liability": round(closing_liability, 3)
			}
			data.append(row)


		# Move to next month
		if current_date3.month == 12:
			current_date3 = datetime(current_date3.year + 1, 1, 1)
		else:
			current_date3 = datetime(current_date3.year, current_date3.month + 1, 1)

	# Add summary row
	data.append({
		"month_start_date": "",
		"month_end_date": "",
		"days_in_month": total_days,
		"mlp": round(total_mlp, 3),
		"pv": round(total_pv, 3),
		"depreciation": round(total_depre, 3),
		"wdv": "",
		"interest_cost": round(total_interest_cost, 3),
		"closing_liability": ""
	})

	return columns, data

# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from calendar import monthrange
from dateutil.relativedelta import relativedelta

#function to generate monthwise data
def generate_month_range(start_date,end_date,docname):
	doc = frappe.get_doc("Lease Management",docname)
	start_year=start_date.year
	end_year=end_date.year
	n_year=end_year-start_year

	for child in doc.escalation:
		escl_type=child.escalation_type
		if escl_type=="Per Annum":
			rate=child.rate
			escl_dates=[]
			# new_date = start_date + relativedelta(years=1)
			# escl_dates.append(new_date)
			# if new_date<end_date:
			# 	new_date=new_date + relativedelta(years=1)
			# 	escl_dates.append(new_date)
			for i in range(5):
				if i==0:
					new_date = start_date + relativedelta(years=1)
					escl_dates.append(new_date)
				else:
					new_date=new_date + relativedelta(years=1)
					if new_date<end_date:
						escl_dates.append(new_date)

		elif escl_type=="Based On Dates":
			monthly_rent=child.monthly_rent
			escl_start_date=child.start_date
			escl_end_date=child.end_date
		elif escl_type=="Per Annum and Fixed Amount":
			rate=child.rate
			fixed_amt=child.fixed_amount

	month_ranges=[]
	current_date=start_date
	cnt=0
	ndays=0

	while current_date<=end_date:
		# month_start=current_date.replace(day=1)
		month_start=current_date

		_,last_day=monthrange(current_date.year, current_date.month)
		month_end=datetime(current_date.year, current_date.month, last_day)

		date_difference = month_end - month_start
		n = date_difference.days +1
		ndays+=n

		if month_end>end_date:
			month_end=end_date

		cnt+=1
		# month_ranges.append(f"Start: {month_start.date()}, End: {month_end.date()}, Count: {cnt}")
		month_ranges.append(f"End: {month_end.date()}, No of Days: {ndays}, escl_dates**={escl_dates}")


		if current_date.month==12:
			current_date=datetime(current_date.year + 1, 1, 1)
		else:
			current_date=datetime(current_date.year, current_date.month + 1, 1)
			
	return "\n".join(month_ranges)

@frappe.whitelist()
def generate_report(docname):
	# Your report generation logic here
	doc = frappe.get_doc("Lease Management",docname)
	disc_doc=frappe.get_doc("Discounting Rate",'disc-09')
	escal=doc.escalation
	# Discounting Rate
	disc_rate=float(disc_doc.discounting_rate/100)

	daily_rate=(1+disc_rate)**(1/365)-1

	date_format = "%Y-%m-%d"
	# date_str1 = datetime.strptime(doc.agreement_start_date, date_format).date()
	# date_str2 = datetime.strptime(doc.agreement_end_date, date_format).date()

	# date_str1 = "2020-04-24"
	# date_str2 = "2025-04-23"

	date_str1 = str(doc.agreement_start_date)
	date_str2 = str(doc.agreement_end_date)
	date1 = datetime.strptime(date_str1, date_format)
	date2 = datetime.strptime(date_str2, date_format)
	date_difference = date2 - date1
	total_days = date_difference.days

	n=31

	mlp=int(doc.monthly_rent)

	pv=mlp/((1+daily_rate)**n)

	depre=(n/total_days)*1877278.34360599

	month_range_output = generate_month_range(date1, date2,docname)
	

	return "Report Generated Successfully pv="+str(pv)+" total days="+str(total_days)+" Depre= "+str(depre)+" "+month_range_output+" "+str(escal[0])



class LeaseManagement(Document):
	# @frappe.whitelist()
	# def get_pincodes_by_city(city):
	# 	pincodes = frappe.get_all("Pincode Master", 
	# 		filters={"city": city},
	# 		fields=["pincode"])

	# 	if not pincodes:
	# 		return "No pincodes found for this city."

	# 	pincode_list = ", ".join(p["pincode"] for p in pincodes)
	# 	return pincode_list
	pass
	
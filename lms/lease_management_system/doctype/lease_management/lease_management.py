# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from calendar import monthrange
from dateutil.relativedelta import relativedelta
import pandas as pd


#function to generate monthwise data
def generate_month_range(start_date,end_date,docname):
	doc = frappe.get_doc("Lease Management",docname)
	mlp=float(doc.monthly_rent)
	mlp2=float(doc.monthly_rent)
	
	disc_doc=frappe.get_doc("Discounting Rate",'disc-09')
	# Discounting Rate
	disc_rate=float(disc_doc.discounting_rate/100)

	daily_rate=(1+disc_rate)**(1/365)-1

	start_year=start_date.year
	end_year=end_date.year
	n_year=end_year-start_year

	month_ranges=[]
	deprec=[]
	current_date=start_date
	current_date2=start_date
	current_date3=start_date
	cnt=0
	cnt2=0
	ndays=0
	total_mlp=0
	total_pv=0
	total_depre=0

	columns=["Month", "Days","MLP","PV", "Depreciation", "WDV", "Interest Cost", "Closing Liability"]
	data=[]
	pv_arr=[]

	for child in doc.escalation:
		escl_type=child.escalation_type
		if escl_type=="Per Annum":
			escl_rate=float(child.rate)
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

			while current_date<=end_date:
				# month_start=current_date.replace(day=1)
				cnt+=1

				if current_date in escl_dates:
					mlp=mlp+(escl_rate*mlp/100)
				total_mlp+=mlp

				month_start=current_date

				_,last_day=monthrange(current_date.year, current_date.month)
				month_end=datetime(current_date.year, current_date.month, last_day)
				if end_date<month_end:
					month_end=end_date

				date_difference = month_end - month_start
				n = date_difference.days +1

				if cnt==1:
					pv=mlp
					pv_arr.append(pv)
				else:
					pv=mlp/((1+daily_rate)**ndays)
					pv_arr.append(pv)
				total_pv=total_pv+pv

				ndays+=n

				if month_end>end_date:
					month_end=end_date

				

				
				# month_ranges.append(f"Start: {month_start.date()}, End: {month_end.date()}, Count: {cnt}")
				# month_ranges.append(f"End: {month_end.date()}, No of Days: {ndays}, escl_dates**={escl_dates} mlp={mlp}")
				# month_ranges.append(f"End: {month_end.date()}, mlp={mlp}, total mlp={total_mlp}, PV= {pv}, Total PV: {total_pv}")


				if current_date.month==12:
					current_date=datetime(current_date.year + 1, 1, 1)
				else:
					current_date=datetime(current_date.year, current_date.month + 1, 1)

			prev_closing_liability=total_pv
			total_days=ndays
			#depreciation
			while current_date2<=end_date:
				month_start=current_date2

				_,last_day=monthrange(current_date2.year, current_date2.month)
				month_end=datetime(current_date2.year, current_date2.month, last_day)

				if end_date<month_end:
					month_end=end_date

				date_difference = month_end - month_start
				n = date_difference.days +1

				depreciation=(n/total_days)*prev_closing_liability
				total_depre+=depreciation
				# month_ranges.append(f"End Date: {month_end.date()},Days={n}, Dprec= {depreciation}")

				if month_end>end_date:
					month_end=end_date

				if current_date2.month==12:
					current_date2=datetime(current_date2.year + 1, 1, 1)
				else:
					current_date2=datetime(current_date2.year, current_date2.month + 1, 1)
			
			prev_wdv=total_depre
			wdv=prev_wdv
			closing_liability=prev_closing_liability
			total_interest_cost=0
			#WDV
			while current_date3<=end_date:
				month_start=current_date3
				cnt2+=1

				_,last_day=monthrange(current_date3.year, current_date3.month)
				month_end=datetime(current_date3.year, current_date3.month, last_day)

				if end_date<month_end:
					month_end=end_date

				date_difference = month_end - month_start
				n = date_difference.days +1

				if current_date3 in escl_dates:
					mlp2=mlp2+(escl_rate*mlp2/100)
				interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
				total_interest_cost+=interest_cost
				closing_liability=closing_liability+interest_cost-mlp2

				depreciation=(n/total_days)*prev_closing_liability
				wdv-=depreciation

				data.append([month_end.date(), n,mlp2, round(depreciation, 10), round(wdv, 10), round(interest_cost, 10),
                              round(closing_liability, 10)])
				

				month_ranges.append(f"End Date: {month_end.date()},Days={n}, Dprec= {depreciation}, WDV={wdv}, IC={interest_cost}, Closing Liability={closing_liability}, TIC={total_interest_cost}")

				if month_end>end_date:
					month_end=end_date

				if current_date3.month==12:
					current_date3=datetime(current_date3.year + 1, 1, 1)
				else:
					current_date3=datetime(current_date3.year, current_date3.month + 1, 1)

		elif escl_type=="Based On Dates":
			monthly_rent=child.monthly_rent
			escl_start_date=child.start_date
			escl_end_date=child.end_date
		elif escl_type=="Per Annum and Fixed Amount":
			rate=child.rate
			fixed_amt=child.fixed_amount
		
	if not data:
		frappe.msgprint("No Data ")

	for i in range(len(data)):
		data[i].insert(3,pv_arr[i])

	data.append(['',total_days,total_mlp,total_pv,total_depre,'',total_interest_cost,''])
	df = pd.DataFrame(data, columns=columns)

	excel_filename = f"/home/shradha/frappe-bench/sites/lms_localhost/public/files/lease_management_report_{docname}.xlsx"
	df.to_excel(excel_filename, index=False, engine='openpyxl')

	return excel_filename

	# while current_date<=end_date:
	# 	# month_start=current_date.replace(day=1)
	# 	month_start=current_date

	# 	_,last_day=monthrange(current_date.year, current_date.month)
	# 	month_end=datetime(current_date.year, current_date.month, last_day)

	# 	date_difference = month_end - month_start
	# 	n = date_difference.days +1
	# 	ndays+=n

	# 	if month_end>end_date:
	# 		month_end=end_date

	# 	cnt+=1
	# 	# month_ranges.append(f"Start: {month_start.date()}, End: {month_end.date()}, Count: {cnt}")
	# 	month_ranges.append(f"End: {month_end.date()}, No of Days: {ndays}, escl_dates**={escl_dates}")


	# 	if current_date.month==12:
	# 		current_date=datetime(current_date.year + 1, 1, 1)
	# 	else:
	# 		current_date=datetime(current_date.year, current_date.month + 1, 1)
	# res=month_ranges+deprec
	# return "\n".join(month_ranges)

@frappe.whitelist()
def generate_report(docname):
	doc = frappe.get_doc("Lease Management",docname)
	

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

	# n=31

	# mlp=int(doc.monthly_rent)

	# pv=mlp/((1+daily_rate)**n)

	# depre=(n/total_days)*1877278.34360599

	month_range_output = generate_month_range(date1, date2,docname)
	

	# return "Report Generated Successfully pv="+str(pv)+" total days="+str(total_days)+" Depre= "+str(depre)+" "+month_range_output+" "
	return "\n"+month_range_output+" "




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
	
	def validate(self):
		for row in self.escalation:
			if row.escalation_type=='Per Annum' and not row.rate:
				frappe.throw("Rate Field Required in Escalation")
			if row.escalation_type=='Based On Dates' and not row.start_date:
				frappe.throw("Start Date Field Required in Escalation")
			if row.escalation_type=='Based On Dates' and not row.end_date:
				frappe.throw("End Date Field Required in Escalation")
			if row.escalation_type=='Based On Dates' and not row.monthly_rent:
				frappe.throw("Monthly Rent Field Required in Escalation")
			if row.escalation_type=='Per Annum and Fixed Amount' and not row.rate:
				frappe.throw("Rate Field Required in Escalation")
			if row.escalation_type=='Per Annum and Fixed Amount' and not row.fixed_amount:
				frappe.throw("Fixed Amount Field Required in Escalation")
	
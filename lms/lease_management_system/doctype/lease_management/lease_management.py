# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime,timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
import pandas as pd
import io
from frappe.utils.file_manager import save_file
from openpyxl.utils import get_column_letter

#function to generate monthwise data
def generate_lease_report(start_date,end_date,docname,cnt_time):
	doc = frappe.get_doc("Lease Management",docname)
	mlp=float(doc.monthly_rent)
	mlp2=float(doc.monthly_rent)
	
	# disc_doc=frappe.get_doc("Discounting Rate",'disc-01')
	# # Discounting Rate
	disc_doc=(float(doc.discounting_rate)/100)

	# daily_rate=(1+disc_rate)**(1/365)-1
	if doc.calculation_rate_type=="Daily Rate":
		# daily_rate=float(disc_doc.daily_rate)
		daily_rate=(1+(disc_doc))**(1/365)-1
	elif doc.calculation_rate_type=="Monthly Rate":
		# daily_rate=float(disc_doc.monthly_rate)
		daily_rate=(1+(disc_doc))**(1/12)-1


	# start_year=start_date.year
	# end_year=end_date.year
	# n_year=end_year-start_year
	arg_sd=start_date
	arg_ed=end_date+ timedelta(days=1)
	diff_years = relativedelta(arg_ed,arg_sd)
	diff_years=int(str(diff_years.years))

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

	columns=["Month Start Date","Month End Date", "Days in Month","Minimum Lease Payment (MLP)","Present Value of MLP", "Depreciation on Right to Use", "Written Down Value (WDV)", "Interest Cost", "Closing Liability"]
	# columns=["Month End Date", "MLP","PV"]
	data=[]
	pv_arr=[]
	etype=[]
	escl_dates_pafr=[]
	escl_dates_bdates=[]
	total_escl_dates_bdates=[]
	escl_dates_pannum=[]
	date_list=[]
	calc_dict={}
	calc_keys=[]
	bd_start_date=""
	bd_end_date=""
	cnt_etype=0
	new_start_date=[]

	for child in doc.escalation:
		escl_type=child.escalation_type
		# if escl_type=="Per Annum":
		# 	etype.append(escl_type+str(child.rate))
		# elif escl_type=="Per Annum and Fixed Amount":
		# 	etype.append(escl_type+str(child.rate))
		if escl_type:
			etype.append(escl_type)
			if "Based On Dates"==escl_type:
				monthly_rent_bdates=float(child.monthly_rent)
				bd_start_date=child.start_date
				bd_end_date=child.end_date
				# escl_dates_bdates=[]
				new_date=current_date
				new_date=new_date.date()
				while new_date<=bd_end_date:
					if new_date>=bd_start_date and new_date<=bd_end_date:
						escl_dates_bdates.append(new_date)
						new_date = new_date + timedelta(days=1)
					else:
						new_date = new_date + timedelta(days=1)

				if new_date>bd_end_date:
					new_start_date.append(new_date)
				dkey="Based On Dates"+'-'+str(monthly_rent_bdates)
				calc_dict[dkey]={monthly_rent_bdates:escl_dates_bdates}
				# calc_dict.setdefault(dkey, {}).setdefault(monthly_rent_bdates, []).extend(escl_dates_bdates)
				total_escl_dates_bdates+=escl_dates_bdates
				escl_dates_bdates=[]

	if len(total_escl_dates_bdates)>0:
		# date_list = [datetime.strptime(d, '%Y-%m-%d').date() for d in escl_dates_bdates]
		# date_list = [
		# 	datetime.strptime(d.strip(), '%Y-%m-%d').date()
		# 	for d in total_escl_dates_bdates
		# 	if d and d.strip()
		# ]
		date_list=total_escl_dates_bdates

	for child in doc.escalation:
		if child.escalation_type=="Per Annum":
			cnt_etype+=1
			escl_rate_pannum=float(child.rate)
			for i in range(diff_years):
				if i==0 and cnt_etype==1:
					for j in range(len(new_start_date)):
						if new_date>=new_start_date[j]:
							new_date=new_start_date[j]
						elif new_date<new_start_date[j]:
							new_date = start_date + relativedelta(years=1)
					if new_date not in date_list:
						escl_dates_pannum.append(new_date)
						new_date=new_date + relativedelta(years=1)
				else:
					# new_date=new_date + relativedelta(years=1)
					if new_date in date_list:
						new_date=new_date + relativedelta(years=1)
						break
					if new_date<end_date.date() and new_date not in date_list:
						escl_dates_pannum.append(new_date)	
						new_date=new_date + relativedelta(years=1)
			dkey="Per Annum"+'-'+str(escl_rate_pannum)
			calc_dict[dkey]={escl_rate_pannum:escl_dates_pannum}
			escl_dates_pannum=[]
		
		elif child.escalation_type=="Per Annum and Fixed Amount":
			cnt_etype+=1
			escl_rate_pafr=float(child.rate)
			fixed_amt_pafr=float(child.fixed_amount)
			# escl_dates_pafr=[]
			for i in range(diff_years):
				if i==0 and cnt_etype==1:
					for j in range(len(new_start_date)):
						if new_date>=new_start_date[j]:
							new_date=new_start_date[j]
						elif new_date<new_start_date[j]:
							new_date = start_date + relativedelta(years=1)
						
					if new_date not in date_list:
						escl_dates_pafr.append(new_date)
						new_date=new_date + relativedelta(years=1)
				else:
					# new_date=new_date + relativedelta(years=1)
					if new_date in date_list:
						new_date=new_date + relativedelta(years=1)
						break
					if new_date<end_date.date() and new_date not in date_list:
						escl_dates_pafr.append(new_date)
						new_date=new_date + relativedelta(years=1)	
			dkey="Per Annum and Fixed Amount"+'-'+str(escl_rate_pafr)+'-'+str(fixed_amt_pafr)
			dsubkey=str(escl_rate_pafr)+'-'+str(fixed_amt_pafr)
			calc_dict[dkey]={dsubkey:escl_dates_pafr}
			# calc_dict.setdefault(dkey, {}).setdefault(dsubkey, []).extend(escl_dates_pafr)	
			escl_dates_pafr=[]
	# res=[]
	for key in calc_dict:
		calc_keys.append(key)

	edates_pannum=[]
	edates_bd=[]
	edates_pafa=[]
	pa_rate=0
	pafa_rate=0
	famt=0
	mrent=0
	dict_ed_pannum={}
	dict_ed_pafa={}
	dict_ed_bdates={}

	for i in range(len(calc_keys)):
		temp_str=calc_keys[i]
		temp=calc_keys[i].split('-')
		calc_escl_type=temp[0]

		if calc_escl_type=="Per Annum":
			sub_dict=calc_dict[temp_str]
			rate_val=next(iter(sub_dict))
			pa_rate=float(rate_val)
			edates_pannum+=sub_dict[rate_val]
			dict_ed_pannum[rate_val]=sub_dict[rate_val]

		elif calc_escl_type=="Based On Dates":
			sub_dict=calc_dict[temp_str]
			mrent_val=next(iter(sub_dict))
			mrent=float(mrent_val)
			edates_bd+=sub_dict[mrent_val]
			dict_ed_bdates[mrent_val]=sub_dict[mrent_val]


		elif calc_escl_type=="Per Annum and Fixed Amount":
			sub_dict=calc_dict[temp_str]
			# temp_val=next(iter(sub_dict))
			# pafa_rate,famt=temp_val
			temp_val=next(iter(sub_dict))
			temp=temp_val.split('-')
			pafa_rate=temp[0]
			famt=temp[1]
			edates_pafa+=sub_dict[temp_val]
			dict_ed_pafa[temp_val]=sub_dict[temp_val]
			

	# for i in range(len(calc_keys)):
	# 	# temp_str=calc_keys[i]
	# 	temp=calc_keys[i].split('-')
	# 	calc_escl_type=temp[0]

	# 	if calc_escl_type=="Per Annum":
	# 		sub_dict=calc_dict[calc_escl_type]
	# 		rate_val=next(iter(sub_dict))
	# 		rate=float(rate_val)
	# 		escl=sub_dict[rate_val]
	# Calculate Previous Closing Liability from Present Value and Total Days
	while current_date<=end_date:
		cnt+=1
		month_start=current_date

		_,last_day=monthrange(current_date.year, current_date.month)
		month_end=datetime(current_date.year, current_date.month, last_day)

		month_start2=current_date.replace(day=1)
		_,last_day2=monthrange(current_date.year, current_date.month)
		month_end2=datetime(current_date.year, current_date.month, last_day2)
		date_difference2 = month_end2 - month_start2
		total_days_of_month = date_difference2.days +1

		if end_date<month_end:
			month_end=end_date

		date_difference = month_end - month_start
		n = date_difference.days +1

		if n<total_days_of_month:
			prev_mlp=mlp
			mlp=mlp*n/total_days_of_month
			if current_date.date() in edates_pannum:
				for k in dict_ed_pannum.keys():
					rate_pa=float(k)
					escl=dict_ed_pannum[k]
					if current_date.date() in escl:
						pa_rate=rate_pa
						break
				mlp=mlp+(pa_rate*mlp/100)
			elif current_date.date() in edates_bd:
				for k in dict_ed_bdates.keys():
					rpm=float(k)
					escl=dict_ed_bdates[k]
					if current_date.date() in escl:
						mrent=rpm
						break
				mlp=mrent
			elif current_date.date() in edates_pafa:
				for k in dict_ed_pafa.keys():
					temp_val=k
					temp=temp_val.split('-')
					rate_pa=temp[0]
					f=temp[1]
					escl=dict_ed_pafa[k]
					if current_date.date() in escl:
						pafa_rate=float(rate_pa)
						famt=float(f)
						break
				mlp=mlp+(pafa_rate*mlp/100)+famt

			total_mlp+=mlp
			if cnt==1:
				pv=mlp
				pv_arr.append(pv)
			else:
				pv=mlp/((1+daily_rate)**ndays)
				pv_arr.append(pv)
			mlp=prev_mlp

		else:
			if current_date.date() in edates_pannum and len(edates_pannum)>0:
				for k in dict_ed_pannum.keys():
					rate_pa=float(k)
					escl=dict_ed_pannum[k]
					if current_date.date() in escl:
						pa_rate=rate_pa
						break
				mlp=mlp+(pa_rate*mlp/100)
				
			elif current_date.date() in edates_bd and len(edates_bd)>0:
				for k in dict_ed_bdates.keys():
					rpm=float(k)
					escl=dict_ed_bdates[k]
					if current_date.date() in escl:
						mrent=rpm
						break
				mlp=mrent

			elif current_date.date() in edates_pafa and len(edates_pafa)>0:
				for k in dict_ed_pafa.keys():
					# rate_pa,f=k
					temp_val=k
					temp=temp_val.split('-')
					rate_pa=temp[0]
					f=temp[1]
					escl=dict_ed_pafa[k]
					if current_date.date() in escl:
						pafa_rate=float(rate_pa)
						famt=float(f)
						break
				mlp=mlp+(pafa_rate*mlp/100)+famt

			total_mlp+=mlp
			if cnt==1:
				pv=mlp
				pv_arr.append(pv)
			else:
				pv=mlp/((1+daily_rate)**ndays)
				pv_arr.append(pv)

		# total_mlp+=mlp
		total_pv=total_pv+pv
		ndays+=n

		if month_end>end_date:
			month_end=end_date

		if current_date.month==12:
			current_date=datetime(current_date.year + 1, 1, 1)
		else:
			current_date=datetime(current_date.year, current_date.month + 1, 1)

	prev_closing_liability=total_pv
	total_days=ndays

	# Calculate Depreciation
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

	# calc depre,wdv
	while current_date3<=end_date:
		cnt2+=1
		month_start=current_date3

		_,last_day=monthrange(current_date3.year, current_date3.month)
		month_end=datetime(current_date3.year, current_date3.month, last_day)

		month_start2=current_date.replace(day=1)
		_,last_day2=monthrange(current_date3.year, current_date3.month)
		month_end2=datetime(current_date3.year, current_date3.month, last_day2)
		date_difference2 = month_end2 - month_start2
		total_days_of_month = date_difference2.days +1

		if end_date<month_end:
			month_end=end_date

		date_difference = month_end - month_start
		n = date_difference.days +1

		if n<total_days_of_month:
			prev_mlp2=mlp2
			mlp2=mlp2*n/total_days_of_month
			if current_date3.date() in edates_pannum:
				for k in dict_ed_pannum.keys():
					rate_pa=float(k)
					escl=dict_ed_pannum[k]
					if current_date3.date() in escl:
						pa_rate=rate_pa
						break
				mlp2=mlp2+(pa_rate*mlp2/100)
			elif current_date3.date() in edates_bd:
				for k in dict_ed_bdates.keys():
					rpm=float(k)
					escl=dict_ed_bdates[k]
					if current_date3.date() in escl:
						mrent=rpm
						break
				mlp2=mrent
			elif current_date3.date() in edates_pafa:
				for k in dict_ed_pafa.keys():
					# rate_pa,f=k
					temp_val=k
					temp=temp_val.split('-')
					rate_pa=temp[0]
					f=temp[1]
					escl=dict_ed_pafa[k]
					if current_date3.date() in escl:
						pafa_rate=float(rate_pa)
						famt=float(f)
						break
				mlp2=mlp2+(pafa_rate*mlp2/100)+famt

			interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
			total_interest_cost+=interest_cost
			closing_liability=closing_liability+interest_cost-mlp2

			depreciation=(n/total_days)*prev_closing_liability
			wdv-=depreciation

			data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
						round(closing_liability, 3)])
			mlp2=prev_mlp2

		else:
			if current_date3.date() in edates_pannum and len(edates_pannum)>0:
				for k in dict_ed_pannum.keys():
					rate_pa=float(k)
					escl=dict_ed_pannum[k]
					if current_date3.date() in escl:
						pa_rate=rate_pa
						break
				mlp2=mlp2+(pa_rate*mlp2/100)
				
			elif current_date3.date() in edates_bd and len(edates_bd)>0:
				for k in dict_ed_bdates.keys():
					rpm=float(k)
					escl=dict_ed_bdates[k]
					if current_date3.date() in escl:
						mrent=rpm
						break
				mlp2=mrent

			elif current_date3.date() in edates_pafa and len(edates_pafa)>0:
				for k in dict_ed_pafa.keys():
					# rate_pa,f=k
					temp_val=k
					temp=temp_val.split('-')
					rate_pa=temp[0]
					f=temp[1]
					escl=dict_ed_pafa[k]
					if current_date3.date() in escl:
						pafa_rate=float(rate_pa)
						famt=float(f)
						break
				mlp2=mlp2+(pafa_rate*mlp2/100)+famt

			interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
			total_interest_cost+=interest_cost
			closing_liability=closing_liability+interest_cost-mlp2

			depreciation=(n/total_days)*prev_closing_liability
			wdv-=depreciation

			data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
						round(closing_liability, 3)])

		if month_end>end_date:
			month_end=end_date

		if current_date3.month==12:
			current_date3=datetime(current_date3.year + 1, 1, 1)
		else:
			current_date3=datetime(current_date3.year, current_date3.month + 1, 1)
			

		# Create Lease Report when Escalation Type is "Per Annum"
	# 	if escl_type=="Per Annum":
	# 		escl_rate=float(child.rate)
	# 		escl_dates=[]
			
	# 		for i in range(diff_years):
	# 			if i==0:
	# 				new_date = start_date + relativedelta(years=1)
	# 				escl_dates.append(new_date)
	# 			else:
	# 				new_date=new_date + relativedelta(years=1)
	# 				if new_date<end_date:
	# 					escl_dates.append(new_date)

	# 		# Calculate Previous Closing Liability from Present Value and Total Days
	# 		while current_date<=end_date:
	# 			cnt+=1
	# 			month_start=current_date

	# 			_,last_day=monthrange(current_date.year, current_date.month)
	# 			month_end=datetime(current_date.year, current_date.month, last_day)

	# 			month_start2=current_date.replace(day=1)
	# 			_,last_day2=monthrange(current_date.year, current_date.month)
	# 			month_end2=datetime(current_date.year, current_date.month, last_day2)
	# 			date_difference2 = month_end2 - month_start2
	# 			total_days_of_month = date_difference2.days +1

	# 			if end_date<month_end:
	# 				month_end=end_date

	# 			date_difference = month_end - month_start
	# 			n = date_difference.days +1

	# 			# if n==15:
	# 			# 	prev_mlp=mlp
	# 			# 	mlp=mlp/2
	# 			# 	if current_date in escl_dates:
	# 			# 		mlp=mlp+(escl_rate*mlp/100)
	# 			# 	total_mlp+=mlp
	# 			# 	if cnt==1:
	# 			# 		pv=mlp
	# 			# 		pv_arr.append(pv)
	# 			# 	else:
	# 			# 		pv=mlp/((1+daily_rate)**ndays)
	# 			# 		pv_arr.append(pv)
	# 			# 	mlp=prev_mlp
	# 			if n<total_days_of_month:
	# 				prev_mlp=mlp
	# 				mlp=mlp*n/total_days_of_month
	# 				if current_date in escl_dates:
	# 					mlp=mlp+(escl_rate*mlp/100)
	# 				total_mlp+=mlp
	# 				if cnt==1:
	# 					pv=mlp
	# 					pv_arr.append(pv)
	# 				else:
	# 					pv=mlp/((1+daily_rate)**ndays)
	# 					pv_arr.append(pv)
	# 				mlp=prev_mlp
	# 			else:
	# 				if current_date in escl_dates:
	# 					mlp=mlp+(escl_rate*mlp/100)
	# 				total_mlp+=mlp
	# 				if cnt==1:
	# 					pv=mlp
	# 					pv_arr.append(pv)
	# 				else:
	# 					pv=mlp/((1+daily_rate)**ndays)
	# 					pv_arr.append(pv)

	# 			# total_mlp+=mlp

				
	# 			total_pv=total_pv+pv

	# 			ndays+=n

	# 			if month_end>end_date:
	# 				month_end=end_date

	# 			# month_ranges.append(f"Start: {month_start.date()}, End: {month_end.date()}, Count: {cnt}")
	# 			# month_ranges.append(f"End: {month_end.date()}, No of Days: {ndays}, escl_dates**={escl_dates} mlp={mlp}")
	# 			# month_ranges.append(f"End: {month_end.date()}, mlp={mlp}, total mlp={total_mlp}, PV= {pv}, Total PV: {total_pv}")

	# 			if current_date.month==12:
	# 				current_date=datetime(current_date.year + 1, 1, 1)
	# 			else:
	# 				current_date=datetime(current_date.year, current_date.month + 1, 1)

	# 		prev_closing_liability=total_pv
	# 		total_days=ndays

	# 		# Calculate Depreciation
	# 		while current_date2<=end_date:
	# 			month_start=current_date2

	# 			_,last_day=monthrange(current_date2.year, current_date2.month)
	# 			month_end=datetime(current_date2.year, current_date2.month, last_day)

	# 			if end_date<month_end:
	# 				month_end=end_date

	# 			date_difference = month_end - month_start
	# 			n = date_difference.days +1

	# 			depreciation=(n/total_days)*prev_closing_liability
	# 			total_depre+=depreciation
	# 			# month_ranges.append(f"End Date: {month_end.date()},Days={n}, Dprec= {depreciation}")

	# 			if month_end>end_date:
	# 				month_end=end_date

	# 			if current_date2.month==12:
	# 				current_date2=datetime(current_date2.year + 1, 1, 1)
	# 			else:
	# 				current_date2=datetime(current_date2.year, current_date2.month + 1, 1)
			
	# 		prev_wdv=total_depre
	# 		wdv=prev_wdv
	# 		closing_liability=prev_closing_liability
	# 		total_interest_cost=0

	# 		# Calculate Depreciation, WDV, Interest Cost, Closing Liability Per Month
	# 		while current_date3<=end_date:
	# 			month_start=current_date3
	# 			cnt2+=1

	# 			_,last_day=monthrange(current_date3.year, current_date3.month)
	# 			month_end=datetime(current_date3.year, current_date3.month, last_day)

	# 			month_start2=current_date3.replace(day=1)
	# 			_,last_day2=monthrange(current_date3.year, current_date3.month)
	# 			month_end2=datetime(current_date3.year, current_date3.month, last_day2)
	# 			date_difference2 = month_end2 - month_start2
	# 			total_days_of_month = date_difference2.days +1

	# 			if end_date<month_end:
	# 				month_end=end_date

	# 			date_difference = month_end - month_start
	# 			n = date_difference.days +1

	# 			if n<total_days_of_month:
	# 				prev_mlp2=mlp2
	# 				mlp2=mlp2*n/total_days_of_month
	# 				# prev_mlp2=mlp2
	# 				# mlp2=mlp2/2 
	# 				if current_date3 in escl_dates:
	# 					mlp2=mlp2+(escl_rate*mlp2/100)
	# 				interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
	# 				total_interest_cost+=interest_cost
	# 				closing_liability=closing_liability+interest_cost-mlp2
	# 				depreciation=(n/total_days)*prev_closing_liability
	# 				wdv-=depreciation

	# 				data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),round(closing_liability, 3)])
	# 				mlp2=prev_mlp2
					
	# 			else:
	# 				if current_date3 in escl_dates:
	# 					mlp2=mlp2+(escl_rate*mlp2/100)
	# 				interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
	# 				total_interest_cost+=interest_cost
	# 				closing_liability=closing_liability+interest_cost-mlp2

	# 				depreciation=(n/total_days)*prev_closing_liability
	# 				wdv-=depreciation

	# 				data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
	# 							round(closing_liability, 3)])
				

	# 			month_ranges.append(f"End Date: {month_end.date()},Days={n}, Dprec= {depreciation}, WDV={wdv}, IC={interest_cost}, Closing Liability={closing_liability}, TIC={total_interest_cost}")

	# 			if month_end>end_date:
	# 				month_end=end_date

	# 			if current_date3.month==12:
	# 				current_date3=datetime(current_date3.year + 1, 1, 1)
	# 			else:
	# 				current_date3=datetime(current_date3.year, current_date3.month + 1, 1)

	# 	elif escl_type=="Based On Dates":
	# 		monthly_rent=float(child.monthly_rent)
	# 		escl_start_date=child.start_date
	# 		escl_end_date=child.end_date
	# 		# escl_start_date=datetime.strptime(str(escl_start_date), "%Y-%m-%d").date()
	# 		# escl_end_date=datetime.strptime(str(escl_end_date), "%Y-%m-%d").date()
	# 		# current_date=datetime.strptime(start_date, "%Y-%m-%d").date()
			
	# 		escl_dates=[]
	# 		new_date=current_date
	# 		new_date=new_date.date()
			
	# 		while new_date<=escl_end_date:
	# 			if new_date>=escl_start_date and new_date<=escl_end_date:
	# 				escl_dates.append(new_date)
	# 				new_date = new_date + timedelta(days=1)
	# 			else:
	# 				new_date = new_date + timedelta(days=1)

	# 		# Calculate Previous Closing Liability from Present Value and Total Days
	# 		while current_date<=end_date:
	# 			cnt+=1
	# 			month_start=current_date

	# 			_,last_day=monthrange(current_date.year, current_date.month)
	# 			month_end=datetime(current_date.year, current_date.month, last_day)

	# 			month_start2=current_date.replace(day=1)
	# 			_,last_day2=monthrange(current_date.year, current_date.month)
	# 			month_end2=datetime(current_date.year, current_date.month, last_day2)
	# 			date_difference2 = month_end2 - month_start2
	# 			total_days_of_month = date_difference2.days +1

	# 			if end_date<month_end:
	# 				month_end=end_date

	# 			date_difference = month_end - month_start
	# 			n = date_difference.days +1

	# 			if n<total_days_of_month:
	# 				prev_mlp=mlp
	# 				mlp=mlp*n/total_days_of_month
	# 				if current_date.date() in escl_dates:
	# 				# if (escl_start_date <= current_date) and (current_date <= escl_end_date):
	# 					mlp=monthly_rent
	# 				total_mlp+=mlp
	# 				if cnt==1:
	# 					pv=mlp
	# 					pv_arr.append(pv)
	# 				else:
	# 					pv=mlp/((1+daily_rate)**ndays)
	# 					pv_arr.append(pv)
	# 				mlp=prev_mlp
	# 			else:
	# 				if current_date.date() in escl_dates:
	# 				# if (escl_start_date <= current_date) and (current_date <= escl_end_date):
	# 					mlp=monthly_rent
	# 				total_mlp+=mlp
	# 				if cnt==1:
	# 					pv=mlp
	# 					pv_arr.append(pv)
	# 				else:
	# 					pv=mlp/((1+daily_rate)**ndays)
	# 					pv_arr.append(pv)

	# 			# total_mlp+=mlp

				
	# 			total_pv=total_pv+pv

	# 			ndays+=n

	# 			if month_end>end_date:
	# 				month_end=end_date

	# 			# month_ranges.append(f"Start: {month_start.date()}, End: {month_end.date()}, Count: {cnt}")
	# 			# month_ranges.append(f"End: {month_end.date()}, No of Days: {ndays}, escl_dates**={escl_dates} mlp={mlp}")
	# 			# month_ranges.append(f"End: {month_end.date()}, mlp={mlp}, total mlp={total_mlp}, PV= {pv}, Total PV: {total_pv}")

	# 			if current_date.month==12:
	# 				current_date=datetime(current_date.year + 1, 1, 1)
	# 			else:
	# 				current_date=datetime(current_date.year, current_date.month + 1, 1)

	# 		prev_closing_liability=total_pv
	# 		total_days=ndays

	# 		# Calculate Depreciation
	# 		while current_date2<=end_date:
	# 			month_start=current_date2

	# 			_,last_day=monthrange(current_date2.year, current_date2.month)
	# 			month_end=datetime(current_date2.year, current_date2.month, last_day)

	# 			if end_date<month_end:
	# 				month_end=end_date

	# 			date_difference = month_end - month_start
	# 			n = date_difference.days +1

	# 			depreciation=(n/total_days)*prev_closing_liability
	# 			total_depre+=depreciation
	# 			# month_ranges.append(f"End Date: {month_end.date()},Days={n}, Dprec= {depreciation}")

	# 			if month_end>end_date:
	# 				month_end=end_date

	# 			if current_date2.month==12:
	# 				current_date2=datetime(current_date2.year + 1, 1, 1)
	# 			else:
	# 				current_date2=datetime(current_date2.year, current_date2.month + 1, 1)
			
	# 		prev_wdv=total_depre
	# 		wdv=prev_wdv
	# 		closing_liability=prev_closing_liability
	# 		total_interest_cost=0

	# 		# Calculate Depreciation, WDV, Interest Cost, Closing Liability Per Month
	# 		while current_date3<=end_date:
	# 			month_start=current_date3
	# 			cnt2+=1

	# 			_,last_day=monthrange(current_date3.year, current_date3.month)
	# 			month_end=datetime(current_date3.year, current_date3.month, last_day)

	# 			month_start2=current_date3.replace(day=1)
	# 			_,last_day2=monthrange(current_date3.year, current_date3.month)
	# 			month_end2=datetime(current_date3.year, current_date3.month, last_day2)
	# 			date_difference2 = month_end2 - month_start2
	# 			total_days_of_month = date_difference2.days +1

	# 			if end_date<month_end:
	# 				month_end=end_date

	# 			date_difference = month_end - month_start
	# 			n = date_difference.days +1

	# 			if n<total_days_of_month:
	# 				prev_mlp2=mlp2
	# 				mlp2=mlp2*n/total_days_of_month
	# 				# prev_mlp2=mlp2
	# 				# mlp2=mlp2/2 
	# 				if current_date3.date() in escl_dates:
	# 				# if (escl_start_date <= current_date3) and (current_date3 <= escl_end_date):
	# 					mlp2=monthly_rent
						
	# 				interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
	# 				total_interest_cost+=interest_cost
	# 				closing_liability=closing_liability+interest_cost-mlp2
	# 				depreciation=(n/total_days)*prev_closing_liability
	# 				wdv-=depreciation

	# 				data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),round(closing_liability, 3)])
	# 				mlp2=prev_mlp2
					
	# 			else:
	# 				if current_date3.date() in escl_dates:
	# 				# if (escl_start_date <= current_date3) and (current_date3 <= escl_end_date):
	# 					mlp2=monthly_rent
	# 				interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
	# 				total_interest_cost+=interest_cost
	# 				closing_liability=closing_liability+interest_cost-mlp2

	# 				depreciation=(n/total_days)*prev_closing_liability
	# 				wdv-=depreciation

	# 				data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
	# 							round(closing_liability, 3)])
				

	# 			# month_ranges.append(f"End Date: {month_end.date()},Days={n}, Dprec= {depreciation}, WDV={wdv}, IC={interest_cost}, Closing Liability={closing_liability}, TIC={total_interest_cost}")

	# 			if month_end>end_date:
	# 				month_end=end_date

	# 			if current_date3.month==12:
	# 				current_date3=datetime(current_date3.year + 1, 1, 1)
	# 			else:
	# 				current_date3=datetime(current_date3.year, current_date3.month + 1, 1)

	# 	elif escl_type=="Per Annum and Fixed Amount":
	# 		escl_rate=float(child.rate)
	# 		fixed_amt=float(child.fixed_amount)
	# 		escl_dates=[]
	# 		for i in range(diff_years):
	# 			if i==0:
	# 				new_date = start_date + relativedelta(years=1)
	# 				escl_dates.append(new_date)
	# 			else:
	# 				new_date=new_date + relativedelta(years=1)
	# 				if new_date<end_date:
	# 					escl_dates.append(new_date)

	# 		# Calculate Previous Closing Liability from Present Value and Total Days
	# 		while current_date<=end_date:
	# 			cnt+=1
	# 			month_start=current_date

	# 			_,last_day=monthrange(current_date.year, current_date.month)
	# 			month_end=datetime(current_date.year, current_date.month, last_day)

	# 			month_start2=current_date.replace(day=1)
	# 			_,last_day2=monthrange(current_date.year, current_date.month)
	# 			month_end2=datetime(current_date.year, current_date.month, last_day2)
	# 			date_difference2 = month_end2 - month_start2
	# 			total_days_of_month = date_difference2.days +1

	# 			if end_date<month_end:
	# 				month_end=end_date

	# 			date_difference = month_end - month_start
	# 			n = date_difference.days +1

	# 			if n<total_days_of_month:
	# 				prev_mlp=mlp
	# 				mlp=mlp*n/total_days_of_month
	# 				if current_date in escl_dates:
	# 					mlp=mlp+(escl_rate*mlp/100)+fixed_amt
	# 				total_mlp+=mlp
	# 				if cnt==1:
	# 					pv=mlp
	# 					pv_arr.append(pv)
	# 				else:
	# 					pv=mlp/((1+daily_rate)**ndays)
	# 					pv_arr.append(pv)
	# 				mlp=prev_mlp
	# 			else:
	# 				if current_date in escl_dates:
	# 					mlp=mlp+(escl_rate*mlp/100)+fixed_amt
	# 				total_mlp+=mlp
	# 				if cnt==1:
	# 					pv=mlp
	# 					pv_arr.append(pv)
	# 				else:
	# 					pv=mlp/((1+daily_rate)**ndays)
	# 					pv_arr.append(pv)

	# 			total_pv=total_pv+pv

	# 			ndays+=n

	# 			if month_end>end_date:
	# 				month_end=end_date

	# 			if current_date.month==12:
	# 				current_date=datetime(current_date.year + 1, 1, 1)
	# 			else:
	# 				current_date=datetime(current_date.year, current_date.month + 1, 1)

	# 		prev_closing_liability=total_pv
	# 		total_days=ndays

	# 		# Calculate Depreciation
	# 		while current_date2<=end_date:
	# 			month_start=current_date2

	# 			_,last_day=monthrange(current_date2.year, current_date2.month)
	# 			month_end=datetime(current_date2.year, current_date2.month, last_day)

	# 			if end_date<month_end:
	# 				month_end=end_date

	# 			date_difference = month_end - month_start
	# 			n = date_difference.days +1

	# 			depreciation=(n/total_days)*prev_closing_liability
	# 			total_depre+=depreciation

	# 			if month_end>end_date:
	# 				month_end=end_date

	# 			if current_date2.month==12:
	# 				current_date2=datetime(current_date2.year + 1, 1, 1)
	# 			else:
	# 				current_date2=datetime(current_date2.year, current_date2.month + 1, 1)
			
	# 		prev_wdv=total_depre
	# 		wdv=prev_wdv
	# 		closing_liability=prev_closing_liability
	# 		total_interest_cost=0

	# 		# Calculate Depreciation, WDV, Interest Cost, Closing Liability Per Month
	# 		while current_date3<=end_date:
	# 			month_start=current_date3
	# 			cnt2+=1

	# 			_,last_day=monthrange(current_date3.year, current_date3.month)
	# 			month_end=datetime(current_date3.year, current_date3.month, last_day)

	# 			month_start2=current_date3.replace(day=1)
	# 			_,last_day2=monthrange(current_date3.year, current_date3.month)
	# 			month_end2=datetime(current_date3.year, current_date3.month, last_day2)
	# 			date_difference2 = month_end2 - month_start2
	# 			total_days_of_month = date_difference2.days +1

	# 			if end_date<month_end:
	# 				month_end=end_date

	# 			date_difference = month_end - month_start
	# 			n = date_difference.days +1

	# 			if n<total_days_of_month:
	# 				prev_mlp2=mlp2
	# 				mlp2=mlp2*n/total_days_of_month
	# 				# prev_mlp2=mlp2
	# 				# mlp2=mlp2/2 
	# 				if current_date3 in escl_dates:
	# 					mlp2=mlp2+(escl_rate*mlp2/100)+fixed_amt
	# 				interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
	# 				total_interest_cost+=interest_cost
	# 				closing_liability=closing_liability+interest_cost-mlp2
	# 				depreciation=(n/total_days)*prev_closing_liability
	# 				wdv-=depreciation

	# 				data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),round(closing_liability, 3)])
	# 				mlp2=prev_mlp2
					
	# 			else:
	# 				if current_date3 in escl_dates:
	# 					mlp2=mlp2+(escl_rate*mlp2/100)+fixed_amt
	# 				interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
	# 				total_interest_cost+=interest_cost
	# 				closing_liability=closing_liability+interest_cost-mlp2

	# 				depreciation=(n/total_days)*prev_closing_liability
	# 				wdv-=depreciation

	# 				data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
	# 							round(closing_liability, 3)])
				

	# 			month_ranges.append(f"End Date: {month_end.date()},Days={n}, Dprec= {depreciation}, WDV={wdv}, IC={interest_cost}, Closing Liability={closing_liability}, TIC={total_interest_cost}")

	# 			if month_end>end_date:
	# 				month_end=end_date

	# 			if current_date3.month==12:
	# 				current_date3=datetime(current_date3.year + 1, 1, 1)
	# 			else:
	# 				current_date3=datetime(current_date3.year, current_date3.month + 1, 1)

	# Store Calculated Data in Dataframe and Save it in Excel File 	
	if not data:
		frappe.msgprint("No Data Calculated")

	for i in range(len(data)):
		data[i].insert(4,pv_arr[i])

	data.append(['','',total_days,round(total_mlp,3),round(total_pv,3),round(total_depre,3),'',round(total_interest_cost,3),''])
	# data.append(['',total_mlp,total_pv])

	# df=pd.DataFrame({'Per Annum':edates_pannum})
	df = pd.DataFrame(data, columns=columns)

	# excel_filename = f"/home/shradha/frappe-bench/sites/lms_localhost/public/files/lease_management_report_{docname}.xlsx"
	# excel_filename = f"/home/iddhiatel/frappe-bench/sites/lease/public/files/lease_management_report_{docname}_{cnt_time}.xlsx"
	# df.to_excel(excel_filename, index=False, engine='openpyxl')

	# output = io.BytesIO()
	# with pd.ExcelWriter(output, engine='openpyxl') as writer:
	# 	df.to_excel(writer, index=False)
		
	# output.seek(0)
	# # cnt_time = datetime.now().strftime("%Y%m%d%H%M%S")
	# file_name=f"lease_management_report_{docname}_{cnt_time}.xlsx"
	# folder="Home"
	# file_doc = save_file(file_name, output.read(),dt="Lease Management",dn=docname, folder=folder, decode=False)
	# return {
    #     "file_url": file_doc.file_url
    # }

	output = io.BytesIO()

	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		df.to_excel(writer, index=False, sheet_name='Sheet1')
		# Get the openpyxl worksheet object
		worksheet = writer.sheets['Sheet1']

    	# Autofit column widths
		for i, col in enumerate(df.columns):
        	# Get the maximum length of the column (including header)
			max_length = max(
            	df[col].astype(str).map(len).max(),
            	len(col)
        	)
			col_letter = get_column_letter(i + 1)
        	# Set column width (add a little extra space)
			worksheet.column_dimensions[col_letter].width = max_length + 2

	output.seek(0)
	file_name = f"lease_management_report_{docname}_{cnt_time}.xlsx"
	folder = "Home"
	
	file_doc = save_file(file_name, output.read(), dt="Lease Management", dn=docname, folder=folder, decode=False)

	return {
    	"file_url": file_doc.file_url
	}

	# res="Based On dates "
	# for i in range(len(escl_dates_bdates)):
	# 	res+=escl_dates_bdates[i]
	# res+="Per Annum "
	# for i in range(len(escl_dates_pannum)):
	# 	res+=escl_dates_pannum[i]
	# res+="per annum Fixed Rate "
	# for i in range(len(escl_dates_pafr)):
	# 	res+=escl_dates_pafr[i]

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
def generate_report(docname,cnt):
	doc = frappe.get_doc("Lease Management",docname)
	date_format = "%Y-%m-%d"
	date_str1 = str(doc.agreement_start_date)
	date_str2 = str(doc.agreement_end_date)
	date1 = datetime.strptime(date_str1, date_format)
	date2 = datetime.strptime(date_str2, date_format)
	# date_difference = date2 - date1
	# total_days = date_difference.days

	# n=31

	# mlp=int(doc.monthly_rent)

	# pv=mlp/((1+daily_rate)**n)

	# depre=(n/total_days)*1877278.34360599

	output = generate_lease_report(date1, date2,docname,cnt)
	

	# return "Report Generated Successfully pv="+str(pv)+" total days="+str(total_days)+" Depre= "+str(depre)+" "+month_range_output+" "
	# return "Report Generated Successfully \n"+str(output)+" "
	return output




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
	
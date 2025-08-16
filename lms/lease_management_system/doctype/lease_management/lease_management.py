# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe,pdb
from frappe.model.document import Document
from datetime import datetime,timedelta,time
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

	# month_ranges=[]
	# deprec=[]
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
	
	data=[]
	pv_arr=['']
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
	esc_bd_end_date=None

	for child in doc.escalation:
		escl_type=child.escalation_type
		# if escl_type=="Per Annum":
		# 	etype.append(escl_type+str(child.rate))
		# elif escl_type=="Per Annum and Fixed Amount":
		# 	etype.append(escl_type+str(child.rate))
		if escl_type:
			etype.append(escl_type)
			if "Based On Dates"==escl_type:
				# if len(child.monthly_rent)==0 or child.monthly_rent is None:
				# 	monthly_rent_bdates=0
				# else:
				# 	monthly_rent_bdates=float(child.monthly_rent)
				# if len(child.rate) == 0 or child.rate is None:
				# 	rate_bdates=0
				# else:
				# 	rate_bdates=float(child.rate)
				# if len(child.fixed_amount) == 0 or child.fixed_amount is None:
				# 	fixed_amt_bdates=0
				# else:
				# 	fixed_amt_bdates=float(child.fixed_amount)
				if child.monthly_rent is None:
					monthly_rent_bdates=0
				else:
					monthly_rent_bdates=float(child.monthly_rent)
				if child.rate is None:
					rate_bdates=0
				else:
					rate_bdates=float(child.rate)
				if child.fixed_amount is None:
					fixed_amt_bdates=0
				else:
					fixed_amt_bdates=float(child.fixed_amount)
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
				# dsubkey=str(monthly_rent_bdates)+'-'+str(rate_bdates)+'-'+str(fixed_amt_bdates)
				dsubkey=str(rate_bdates)+'-'+str(monthly_rent_bdates)+'-'+str(fixed_amt_bdates)

				calc_dict[dkey]={dsubkey:escl_dates_bdates}
				# calc_dict.setdefault(dkey, {}).setdefault(monthly_rent_bdates, []).extend(escl_dates_bdates)
				total_escl_dates_bdates+=escl_dates_bdates
				if len(new_start_date)>0:
					l=len(new_start_date)
					for q in range(l):
						if new_start_date[q] in total_escl_dates_bdates:
							new_start_date.remove(new_start_date[q])
							break
				escl_dates_bdates=[]
	for i in range(len(etype)):
			if etype[i]=="Per Annum" or etype[i]=="Per Annum and Fixed Amount":
				if etype[i-1]=="Based On Dates":
					bd_date=doc.escalation[i-1]
					d=bd_date.end_date
					esc_bd_end_date=d+timedelta(days=1)
	if len(total_escl_dates_bdates)>0:
		# date_list = [datetime.strptime(d, '%Y-%m-%d').date() for d in escl_dates_bdates]
		# date_list = [
		# 	datetime.strptime(d.strip(), '%Y-%m-%d').date()
		# 	for d in total_escl_dates_bdates
		# 	if d and d.strip()
		# ]
		date_list=total_escl_dates_bdates

	for child in doc.escalation:
		# if len(child.monthly_rent) == 0 or child.monthly_rent is None:
		# 	monthly_rent=0
		# else:
		# 	monthly_rent=float(child.monthly_rent)
		# if len(child.rate) == 0 or child.rate is None:
		# 	rate=0
		# else:
		# 	rate=float(child.rate)
		# if len(child.fixed_amount) == 0 or child.fixed_amount is None:
		# 	fixed_amt=0
		# else:
		# 	fixed_amt=float(child.fixed_amount)
		if child.monthly_rent is None:
			monthly_rent=0
		else:
			monthly_rent=float(child.monthly_rent)
		if child.rate is None:
			rate=0
		else:
			rate=float(child.rate)
		if child.fixed_amount is None:
			fixed_amt=0
		else:
			fixed_amt=float(child.fixed_amount)
		if child.escalation_type=="Per Annum":
			cnt_etype+=1
			# escl_rate_pannum=float(child.rate)
			for i in range(diff_years):
				if i==0 and cnt_etype==1:
					# for j in range(len(new_start_date)):
					# 	if new_date>=new_start_date[j]:
					# 		new_date=new_start_date[j]
					# 	elif new_date<new_start_date[j]:
					# 		new_date = start_date + relativedelta(years=1)
					# if len(new_start_date)==0:
					# 	new_date = start_date + relativedelta(years=1)
					if esc_bd_end_date is None:
						new_date=start_date + relativedelta(years=1)
					else:
						new_date=esc_bd_end_date
					if new_date not in date_list:
						if isinstance(new_date, datetime):
							new_date = new_date.date()
						escl_dates_pannum.append(new_date)
						new_date=new_date + relativedelta(years=1)
				else:
					if new_date in date_list:
						new_date=new_date + relativedelta(years=1)
						break
					if isinstance(new_date, datetime):
						new_date = new_date.date()
					if new_date<end_date.date() and new_date not in date_list:
						escl_dates_pannum.append(new_date)	
						new_date=new_date + relativedelta(years=1)
			dkey="Per Annum"+'-'+str(rate)
			dsubkey=str(rate)+'-'+str(monthly_rent)+'-'+str(fixed_amt)
			calc_dict[dkey]={dsubkey:escl_dates_pannum}
			escl_dates_pannum=[]
		
		elif child.escalation_type=="Per Annum and Fixed Amount":
			cnt_etype+=1
			# escl_rate_pafr=float(child.rate)
			# fixed_amt_pafr=float(child.fixed_amount)
			for i in range(diff_years):
				if i==0 and cnt_etype==1:
					# for j in range(len(new_start_date)):
					# 	if new_date>=new_start_date[j]:
					# 		new_date=new_start_date[j]
					# 	elif new_date<new_start_date[j]:
					# 		new_date = start_date + relativedelta(years=1)
					# if len(new_start_date)==0:
						# new_date = start_date + relativedelta(years=1)
					if esc_bd_end_date is None:
						new_date=start_date + relativedelta(years=1)
					else:
						new_date=esc_bd_end_date

					if new_date not in date_list:
						if isinstance(new_date, datetime):
							new_date = new_date.date()
						escl_dates_pafr.append(new_date)
						new_date=new_date + relativedelta(years=1)
				else:
					if new_date in date_list:
						new_date=new_date + relativedelta(years=1)
						break
					if isinstance(new_date, datetime):
						new_date = new_date.date()
					if new_date<end_date.date() and new_date not in date_list:
						escl_dates_pafr.append(new_date)
						new_date=new_date + relativedelta(years=1)	
			dkey="Per Annum and Fixed Amount"+'-'+str(rate)+'-'+str(fixed_amt)
			dsubkey=str(rate)+'-'+str(monthly_rent)+'-'+str(fixed_amt)
			calc_dict[dkey]={dsubkey:escl_dates_pafr}	
			escl_dates_pafr=[]

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
			subkey=next(iter(sub_dict))
			# rate_val=next(iter(sub_dict))
			# pa_rate=float(rate_val)
			edates_pannum+=sub_dict[subkey]
			dict_ed_pannum[subkey]=sub_dict[subkey]

		elif calc_escl_type=="Based On Dates":
			sub_dict=calc_dict[temp_str]
			subkey=next(iter(sub_dict))
			# mrent_val=next(iter(sub_dict))
			# mrent=float(mrent_val)
			edates_bd+=sub_dict[subkey]
			dict_ed_bdates[subkey]=sub_dict[subkey]


		elif calc_escl_type=="Per Annum and Fixed Amount":
			sub_dict=calc_dict[temp_str]
			# temp_val=next(iter(sub_dict))
			# pafa_rate,famt=temp_val
			subkey=next(iter(sub_dict))
			# temp=temp_val.split('-')
			# pafa_rate=temp[0]
			# famt=temp[1]
			edates_pafa+=sub_dict[subkey]
			dict_ed_pafa[subkey]=sub_dict[subkey]
			

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
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_pannum[k]
					if current_date.date() in escl:
						# pa_rate=rate_pa
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp=mrent
							mlp=mlp*n/total_days_of_month
						if mrent==0 and rate==0 and famt==0:
							mlp=0
						mlp=mlp+(rate*mlp/100)+famt
						break
				# mlp=mlp+(pa_rate*mlp/100)
			elif current_date.date() in edates_bd:
				for k in dict_ed_bdates.keys():
					# rpm=float(k)
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_bdates[k]
					if current_date.date() in escl:
						# mrent=rpm
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp=mrent
							mlp=mlp*n/total_days_of_month
						if mrent==0 and rate==0 and famt==0:
							mlp=0
						mlp=mlp+(rate*mlp/100)+famt
						
						break
				# mlp=mrent
			elif current_date.date() in edates_pafa:
				for k in dict_ed_pafa.keys():
					temp_val=k
					temp=temp_val.split('-')
					# rate_pa=temp[0]
					# f=temp[1]
					escl=dict_ed_pafa[k]
					if current_date.date() in escl:
						# pafa_rate=float(rate_pa)
						# famt=float(f)
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp=mrent
							mlp=mlp*n/total_days_of_month
						if mrent==0 and rate==0 and famt==0:
							mlp=0
						mlp=mlp+(rate*mlp/100)+famt
						break
				# mlp=mlp+(pafa_rate*mlp/100)+famt
			
			total_mlp+=mlp
			if cnt==1:
				pv=mlp
				pv_arr.append(pv)
			else:
				pv=mlp/((1+daily_rate)**ndays)
				pv_arr.append(pv)
			mlp=prev_mlp
			if mrent==0 and rate==0 and famt==0:
				mlp=prev_mlp

		else:
			prev_mlp=mlp
			# if current_date.date() in edates_pannum and len(edates_pannum)>0:
			# 	for k in dict_ed_pannum.keys():
			# 		rate_pa=float(k)
			# 		escl=dict_ed_pannum[k]
			# 		if current_date.date() in escl:
			# 			pa_rate=rate_pa
			# 			break
			# 	mlp=mlp+(pa_rate*mlp/100)
				
			# elif current_date.date() in edates_bd and len(edates_bd)>0:
			# 	for k in dict_ed_bdates.keys():
			# 		rpm=float(k)
			# 		escl=dict_ed_bdates[k]
			# 		if current_date.date() in escl:
			# 			mrent=rpm
			# 			break
			# 	mlp=mrent

			# elif current_date.date() in edates_pafa and len(edates_pafa)>0:
			# 	for k in dict_ed_pafa.keys():
			# 		# rate_pa,f=k
			# 		temp_val=k
			# 		temp=temp_val.split('-')
			# 		rate_pa=temp[0]
			# 		f=temp[1]
			# 		escl=dict_ed_pafa[k]
			# 		if current_date.date() in escl:
			# 			pafa_rate=float(rate_pa)
			# 			famt=float(f)
			# 			break
			# 	mlp=mlp+(pafa_rate*mlp/100)+famt
			
			if current_date.date() in edates_pannum:
				for k in dict_ed_pannum.keys():
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_pannum[k]
					if current_date.date() in escl:
						# pa_rate=rate_pa
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp=mrent
						mlp=mlp+(rate*mlp/100)+famt
						break
				# mlp=mlp+(pa_rate*mlp/100)
			elif current_date.date() in edates_bd:
				for k in dict_ed_bdates.keys():
					# rpm=float(k)
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_bdates[k]
					if current_date.date() in escl:
						# mrent=rpm
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp=mrent
						if mrent==0 and rate==0 and famt==0:
							mlp=0
						mlp=mlp+(rate*mlp/100)+famt
						
						break
				# mlp=mrent
			elif current_date.date() in edates_pafa:
				for k in dict_ed_pafa.keys():
					temp_val=k
					temp=temp_val.split('-')
					# rate_pa=temp[0]
					# f=temp[1]
					escl=dict_ed_pafa[k]
					if current_date.date() in escl:
						# pafa_rate=float(rate_pa)
						# famt=float(f)
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp=mrent
						mlp=mlp+(rate*mlp/100)+famt
						break
				# mlp=mlp+(pafa_rate*mlp/100)+famt
			

			total_mlp+=mlp
			if cnt==1:
				pv=mlp
				pv_arr.append(pv)
			else:
				pv=mlp/((1+daily_rate)**ndays)
				pv_arr.append(pv)
			if mrent==0 and rate==0 and famt==0:
				mlp=prev_mlp

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

		if (doc.previous_wdv)!=0:
			prev_closing_liability_wdv=float(doc.previous_wdv)
			depreciation=(n/total_days)*prev_closing_liability_wdv
			total_depre+=depreciation
		else:
			depreciation=(n/total_days)*prev_closing_liability
			total_depre+=depreciation
		
		if month_end>end_date:
			month_end=end_date

		if current_date2.month==12:
			current_date2=datetime(current_date2.year + 1, 1, 1)
		else:
			current_date2=datetime(current_date2.year, current_date2.month + 1, 1)		
	if (doc.previous_wdv)!=0:
		prev_wdv=float(doc.previous_wdv)
		# prev_closing_liability=float(doc.previous_wdv)
	else:
		prev_wdv=total_depre
	wdv=prev_wdv
	closing_liability=prev_closing_liability
	total_interest_cost=0
	data.insert(0,['','','','','',round(wdv,3),'',round(closing_liability,3)])

	# calc depre,wdv
	while current_date3<=end_date:
		cnt2+=1
		month_start=current_date3

		_,last_day=monthrange(current_date3.year, current_date3.month)
		month_end=datetime(current_date3.year, current_date3.month, last_day)

		month_start2=current_date3.replace(day=1)
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
			# if current_date3.date() in edates_pannum:
			# 	for k in dict_ed_pannum.keys():
			# 		rate_pa=float(k)
			# 		escl=dict_ed_pannum[k]
			# 		if current_date3.date() in escl:
			# 			pa_rate=rate_pa
			# 			break
			# 	mlp2=mlp2+(pa_rate*mlp2/100)
			# elif current_date3.date() in edates_bd:
			# 	for k in dict_ed_bdates.keys():
			# 		rpm=float(k)
			# 		escl=dict_ed_bdates[k]
			# 		if current_date3.date() in escl:
			# 			mrent=rpm
			# 			break
			# 	mlp2=mrent
			# elif current_date3.date() in edates_pafa:
			# 	for k in dict_ed_pafa.keys():
			# 		# rate_pa,f=k
			# 		temp_val=k
			# 		temp=temp_val.split('-')
			# 		rate_pa=temp[0]
			# 		f=temp[1]
			# 		escl=dict_ed_pafa[k]
			# 		if current_date3.date() in escl:
			# 			pafa_rate=float(rate_pa)
			# 			famt=float(f)
			# 			break
				# mlp2=mlp2+(pafa_rate*mlp2/100)+famt
			if current_date3.date() in edates_pannum:
				for k in dict_ed_pannum.keys():
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_pannum[k]
					if current_date3.date() in escl:
						# pa_rate=rate_pa
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp2=mrent
							mlp2=mlp2*n/total_days_of_month
						mlp2=mlp2+(rate*mlp2/100)+famt
						break
				# mlp=mlp+(pa_rate*mlp/100)
			elif current_date3.date() in edates_bd:
				for k in dict_ed_bdates.keys():
					# rpm=float(k)
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_bdates[k]
					if current_date3.date() in escl:
						# mrent=rpm
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp2=mrent
							mlp2=mlp2*n/total_days_of_month
						mlp2=mlp2+(rate*mlp2/100)+famt
						
						break
				# mlp=mrent
			elif current_date3.date() in edates_pafa:
				for k in dict_ed_pafa.keys():
					temp_val=k
					temp=temp_val.split('-')
					# rate_pa=temp[0]
					# f=temp[1]
					escl=dict_ed_pafa[k]
					if current_date3.date() in escl:
						# pafa_rate=float(rate_pa)
						# famt=float(f)
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp2=mrent
							mlp2=mlp2*n/total_days_of_month
						mlp2=mlp2+(rate*mlp2/100)+famt
						break
				# mlp=mlp+(pafa_rate*mlp/100)+famt
			

			interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
			total_interest_cost+=interest_cost
			closing_liability=closing_liability+interest_cost-mlp2

			depreciation=(n/total_days)*prev_closing_liability
			wdv-=depreciation

			data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
						round(closing_liability, 3)])
			if mrent==0 and rate==0 and famt==0:
				mlp2=prev_mlp2
			mlp2=prev_mlp2

		else:
			prev_mlp2=mlp2
			# if current_date3.date() in edates_pannum and len(edates_pannum)>0:
			# 	for k in dict_ed_pannum.keys():
			# 		rate_pa=float(k)
			# 		escl=dict_ed_pannum[k]
			# 		if current_date3.date() in escl:
			# 			pa_rate=rate_pa
			# 			break
			# 	mlp2=mlp2+(pa_rate*mlp2/100)
				
			# elif current_date3.date() in edates_bd and len(edates_bd)>0:
			# 	for k in dict_ed_bdates.keys():
			# 		rpm=float(k)
			# 		escl=dict_ed_bdates[k]
			# 		if current_date3.date() in escl:
			# 			mrent=rpm
			# 			break
			# 	mlp2=mrent

			# elif current_date3.date() in edates_pafa and len(edates_pafa)>0:
			# 	for k in dict_ed_pafa.keys():
			# 		# rate_pa,f=k
			# 		temp_val=k
			# 		temp=temp_val.split('-')
			# 		rate_pa=temp[0]
			# 		f=temp[1]
			# 		escl=dict_ed_pafa[k]
			# 		if current_date3.date() in escl:
			# 			pafa_rate=float(rate_pa)
			# 			famt=float(f)
			# 			break
			# 	mlp2=mlp2+(pafa_rate*mlp2/100)+famt

			if current_date3.date() in edates_pannum:
				for k in dict_ed_pannum.keys():
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_pannum[k]
					if current_date3.date() in escl:
						# pa_rate=rate_pa
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp2=mrent
						mlp2=mlp2+(rate*mlp2/100)+famt
						break
				# mlp=mlp+(pa_rate*mlp/100)
			elif current_date3.date() in edates_bd:
				for k in dict_ed_bdates.keys():
					# rpm=float(k)
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_bdates[k]
					if current_date3.date() in escl:
						# mrent=rpm
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp2=mrent
						if mrent==0 and rate==0 and famt==0:
							mlp2=0
						mlp2=mlp2+(rate*mlp2/100)+famt
						break
				# mlp=mrent
			elif current_date3.date() in edates_pafa:
				for k in dict_ed_pafa.keys():
					temp_val=k
					temp=temp_val.split('-')
					# rate_pa=temp[0]
					# f=temp[1]
					escl=dict_ed_pafa[k]
					if current_date3.date() in escl:
						# pafa_rate=float(rate_pa)
						# famt=float(f)
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp2=mrent
						mlp2=mlp2+(rate*mlp2/100)+famt
						break
				# mlp=mlp+(pafa_rate*mlp/100)+famt
			
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

			data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
						round(closing_liability, 3)])
			if mrent==0 and rate==0 and famt==0:
				mlp2=prev_mlp2

		if month_end>end_date:
			month_end=end_date

		if current_date3.month==12:
			current_date3=datetime(current_date3.year + 1, 1, 1)
		else:
			current_date3=datetime(current_date3.year, current_date3.month + 1, 1)
			

	# Store Calculated Data in Dataframe and Save it in Excel File 	
	if not data:
		frappe.msgprint("No Data Calculated")

	for i in range(len(data)):
		data[i].insert(4,pv_arr[i])

	data.append(['','',total_days,round(total_mlp,3),round(total_pv,3),round(total_depre,3),'',round(total_interest_cost,3),''])
	
	df = pd.DataFrame(data, columns=columns)

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


# ===================================================================================
def generate_lease_report_month_based(start_date,end_date,docname,cnt_time):
	doc = frappe.get_doc("Lease Management",docname)
	mlp=float(doc.monthly_rent)
	mlp2=float(doc.monthly_rent)
	
	# Discounting Rate
	disc_doc=(float(doc.discounting_rate)/100)

	if doc.calculation_rate_type=="Monthly Rate":
		daily_rate=(1+(disc_doc))**(1/12)-1
		columns=["Month Start Date","Month End Date", "Month","Minimum Lease Payment (MLP)","Present Value of MLP","Days in Month", "Depreciation on Right to Use", "Written Down Value (WDV)", "Interest Cost", "Closing Liability"]

	arg_sd=start_date
	arg_ed=end_date+ timedelta(days=1)
	diff_years = relativedelta(arg_ed,arg_sd)
	diff_years=int(str(diff_years.years))

	current_date=start_date
	current_date2=start_date
	current_date3=start_date
	cnt=0
	cnt1=0
	cnt2=0
	ndays=0
	nmonths=0
	ndays_pv=0
	total_mlp=0
	total_pv=0
	total_depre=0
	data=[]
	pv_arr=['']
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
	esc_bd_end_date=None

	for child in doc.escalation:
		escl_type=child.escalation_type
		
		if escl_type:
			etype.append(escl_type)
			if "Based On Dates"==escl_type:
				# monthly_rent_bdates=float(child.monthly_rent)
				# rate_bdates=float(child.rate)
				# fixed_amt_bdates=float(child.fixed_amount)
				# if len(child.monthly_rent) == 0 or child.monthly_rent is None:
				# 	monthly_rent_bdates=0
				# else:
				# 	monthly_rent_bdates=float(child.monthly_rent)
				# if len(child.rate) == 0 or child.rate is None:
				# 	rate_bdates=0
				# else:
				# 	rate_bdates=float(child.rate)
				# if len(child.fixed_amount) == 0 or child.fixed_amount is None:
				# 	fixed_amt_bdates=0
				# else:
				# 	fixed_amt_bdates=float(child.fixed_amount)
				if child.monthly_rent is None:
					monthly_rent_bdates=0
				else:
					monthly_rent_bdates=float(child.monthly_rent)
				if child.rate is None:
					rate_bdates=0
				else:
					rate_bdates=float(child.rate)
				if child.fixed_amount is None:
					fixed_amt_bdates=0
				else:
					fixed_amt_bdates=float(child.fixed_amount)
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
				dsubkey=str(rate_bdates)+'-'+str(monthly_rent_bdates)+'-'+str(fixed_amt_bdates)
				calc_dict[dkey]={dsubkey:escl_dates_bdates}
				total_escl_dates_bdates+=escl_dates_bdates
				if len(new_start_date)>0:
					l=len(new_start_date)
					for q in range(l):
						if new_start_date[q] in total_escl_dates_bdates:
							new_start_date.remove(new_start_date[q])
							break
				escl_dates_bdates=[]
	for i in range(len(etype)):
		if etype[i]=="Per Annum" or etype[i]=="Per Annum and Fixed Amount":
			if etype[i-1]=="Based On Dates":
				bd_date=doc.escalation[i-1]
				d=bd_date.end_date
				esc_bd_end_date=d+timedelta(days=1)
	if len(total_escl_dates_bdates)>0:
		date_list=total_escl_dates_bdates
	
	for child in doc.escalation:
		# monthly_rent=float(child.monthly_rent)
		# rate=float(child.rate)
		# fixed_amt=float(child.fixed_amount)
		# if len(child.monthly_rent) == 0 or child.monthly_rent is None:
		# 	monthly_rent=0
		# else:
		# 	monthly_rent=float(child.monthly_rent)
		# if len(child.rate) == 0 or child.rate is None:
		# 	rate=0
		# else:
		# 	rate=float(child.rate)
		# if len(child.fixed_amount) == 0 or child.fixed_amount is None:
		# 	fixed_amt=0
		# else:
		# 	fixed_amt=float(child.fixed_amount)
		if child.monthly_rent is None:
			monthly_rent=0
		else:
			monthly_rent=float(child.monthly_rent)
		if child.rate is None:
			rate=0
		else:
			rate=float(child.rate)
		if child.fixed_amount is None:
			fixed_amt=0
		else:
			fixed_amt=float(child.fixed_amount)
		if child.escalation_type=="Per Annum":
			cnt_etype+=1
			# escl_rate_pannum=float(child.rate)
			for i in range(diff_years):
				if i==0 and cnt_etype==1:
					# for j in range(len(new_start_date)):
					# 	if new_date>=new_start_date[j]:
					# 		new_date=new_start_date[j]
					# 	elif new_date<new_start_date[j]:
					# 		new_date = start_date + relativedelta(years=1)
					# if len(new_start_date)==0:
					# 	new_date = start_date + relativedelta(years=1)
					if esc_bd_end_date is None:
						new_date=start_date + relativedelta(years=1)
					else:
						new_date=esc_bd_end_date
					if new_date not in date_list:
						if isinstance(new_date, datetime):
							new_date = new_date.date()
						escl_dates_pannum.append(new_date)
						new_date=new_date + relativedelta(years=1)
				else:
					if new_date in date_list:
						new_date=new_date + relativedelta(years=1)
						break
					if isinstance(new_date, datetime):
							new_date = new_date.date()
					if new_date<end_date.date() and new_date not in date_list:
						escl_dates_pannum.append(new_date)	
						new_date=new_date + relativedelta(years=1)
			dkey="Per Annum"+'-'+str(rate)
			dsubkey=str(rate)+'-'+str(monthly_rent)+'-'+str(fixed_amt)
			calc_dict[dkey]={dsubkey:escl_dates_pannum}
			escl_dates_pannum=[]
		
		elif child.escalation_type=="Per Annum and Fixed Amount":
			cnt_etype+=1
			# escl_rate_pafr=float(child.rate)
			# fixed_amt_pafr=float(child.fixed_amount)
			for i in range(diff_years):
				if i==0 and cnt_etype==1:
					# for j in range(len(new_start_date)):
					# 	if new_date>=new_start_date[j]:
					# 		new_date=new_start_date[j]
					# 	elif new_date<new_start_date[j]:
					# 		new_date = start_date + relativedelta(years=1)
					# if len(new_start_date)==0:
					# 	new_date = start_date + relativedelta(years=1)
					if esc_bd_end_date is None:
						new_date=start_date + relativedelta(years=1)
					else:
						new_date=esc_bd_end_date

					if new_date not in date_list:
						if isinstance(new_date, datetime):
							new_date = new_date.date()
						escl_dates_pafr.append(new_date)
						new_date=new_date + relativedelta(years=1)
				else:
					if new_date in date_list:
						new_date=new_date + relativedelta(years=1)
						break
					if isinstance(new_date, datetime):
							new_date = new_date.date()
					if new_date<end_date.date() and new_date not in date_list:
						escl_dates_pafr.append(new_date)
						new_date=new_date + relativedelta(years=1)	
			dkey="Per Annum and Fixed Amount"+'-'+str(rate)+'-'+str(fixed_amt)
			# dsubkey=str(escl_rate_pafr)+'-'+str(fixed_amt_pafr)
			dsubkey=str(rate)+'-'+str(monthly_rent)+'-'+str(fixed_amt)
			calc_dict[dkey]={dsubkey:escl_dates_pafr}	
			escl_dates_pafr=[]
	# res=[]
	for key in calc_dict:
		calc_keys.append(key)

	edates_pannum=[]
	edates_bd=[]
	edates_pafa=[]
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
			subkey=next(iter(sub_dict))
			# rate_val=next(iter(sub_dict))
			# pa_rate=float(rate_val)
			edates_pannum+=sub_dict[subkey]
			dict_ed_pannum[subkey]=sub_dict[subkey]

		elif calc_escl_type=="Based On Dates":
			sub_dict=calc_dict[temp_str]
			subkey=next(iter(sub_dict))
			# mrent_val=next(iter(sub_dict))
			# mrent=float(mrent_val)
			edates_bd+=sub_dict[subkey]
			dict_ed_bdates[subkey]=sub_dict[subkey]


		elif calc_escl_type=="Per Annum and Fixed Amount":
			sub_dict=calc_dict[temp_str]
			subkey=next(iter(sub_dict))
			# temp_val=next(iter(sub_dict))
			# temp=temp_val.split('-')
			# pafa_rate=temp[0]
			# famt=temp[1]
			edates_pafa+=sub_dict[subkey]
			dict_ed_pafa[subkey]=sub_dict[subkey]
			

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
		if doc.calculation_rate_type=="Monthly Rate":
			n=cnt
			nmonths_val=date_difference.days +1

		if doc.calculation_rate_type=="Monthly Rate":
			if current_date.date() in edates_pannum and len(edates_pannum)>0:
				for k in dict_ed_pannum.keys():
					# rate_pa=float(k)
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_pannum[k]
					if current_date.date() in escl:
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp=mrent
						mlp=mlp+(rate*mlp/100)+famt
						break
				# mlp=mlp+(pa_rate*mlp/100)
				
			elif current_date.date() in edates_bd and len(edates_bd)>0:
				for k in dict_ed_bdates.keys():
					# rpm=float(k)
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_bdates[k]
					if current_date.date() in escl:
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp=mrent
						if mrent==0 and rate==0 and famt==0:
							mlp=0
						mlp=mlp+(rate*mlp/100)+famt
						break
				mlp=mrent

			elif current_date.date() in edates_pafa and len(edates_pafa)>0:
				for k in dict_ed_pafa.keys():
					# rate_pa,f=k
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_pafa[k]
					if current_date.date() in escl:
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp=mrent
						mlp=mlp+(rate*mlp/100)+famt
						break
				# mlp=mlp+(pafa_rate*mlp/100)+famt

			total_mlp+=mlp
			if cnt==1:
				pv=mlp
				pv_arr.append(pv)
			else:
				pv=mlp/((1+daily_rate)**ndays_pv)
				pv_arr.append(pv)

		# total_mlp+=mlp
		total_pv=total_pv+pv
		ndays+=n
		nmonths+=nmonths_val
		ndays_pv+=1

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
		cnt1+=1
		month_start=current_date2

		_,last_day=monthrange(current_date2.year, current_date2.month)
		month_end=datetime(current_date2.year, current_date2.month, last_day)

		if end_date<month_end:
			month_end=end_date

		date_difference = month_end - month_start
		if doc.calculation_rate_type=="Monthly Rate":
			n=cnt1
			n_depre=date_difference.days +1

		if (doc.previous_wdv)!=0:
			prev_closing_liability_wdv=float(doc.previous_wdv)
			depreciation=(n/total_days)*prev_closing_liability_wdv
			total_depre+=depreciation
		else:
			# depreciation=(n/total_days)*prev_closing_liability
			depreciation=(n_depre/nmonths)*prev_closing_liability
			total_depre+=depreciation
		
		if month_end>end_date:
			month_end=end_date

		if current_date2.month==12:
			current_date2=datetime(current_date2.year + 1, 1, 1)
		else:
			current_date2=datetime(current_date2.year, current_date2.month + 1, 1)		
	if (doc.previous_wdv)!=0:
		prev_wdv=float(doc.previous_wdv)
	else:
		prev_wdv=total_depre
	wdv=prev_wdv
	closing_liability=prev_closing_liability
	total_interest_cost=0
	data.insert(0,['','','','','','',round(wdv,3),'',round(closing_liability,3)])

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
		if doc.calculation_rate_type=="Monthly Rate":
			n=cnt2
			n_days_of_month = date_difference.days +1

		if doc.calculation_rate_type=="Monthly Rate":
			if current_date3.date() in edates_pannum and len(edates_pannum)>0:
				for k in dict_ed_pannum.keys():
					# rate_pa=float(k)
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_pannum[k]
					if current_date3.date() in escl:
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp2=mrent
						mlp2=mlp2+(rate*mlp2/100)+famt
						break
				# mlp2=mlp2+(pa_rate*mlp2/100)
				
			elif current_date3.date() in edates_bd and len(edates_bd)>0:
				for k in dict_ed_bdates.keys():
					# rpm=float(k)
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_bdates[k]
					if current_date3.date() in escl:
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp2=mrent
						if mrent==0 and rate==0 and famt==0:
							mlp2=0
						mlp2=mlp2+(rate*mlp2/100)+famt
						break
				# mlp2=mrent

			elif current_date3.date() in edates_pafa and len(edates_pafa)>0:
				for k in dict_ed_pafa.keys():
					# rate_pa,f=k
					temp_val=k
					temp=temp_val.split('-')
					escl=dict_ed_pafa[k]
					if current_date3.date() in escl:
						rate=float(temp[0])
						mrent=float(temp[1])
						famt=float(temp[2])
						if mrent!=0:
							mlp2=mrent
						mlp2=mlp2+(rate*mlp2/100)+famt
						break
				# mlp2=mlp2+(pafa_rate*mlp2/100)+famt
			# n_inter=n_inter+n_days_of_month
			interest_cost=((closing_liability-mlp2)*daily_rate)
			total_interest_cost+=interest_cost
			closing_liability=closing_liability+interest_cost-mlp2

			if (doc.previous_wdv)!=0:
				prev_closing_liability_wdv=float(doc.previous_wdv)
				depreciation=(n/total_days)*prev_closing_liability_wdv
				wdv-=depreciation
			else:
				depreciation=(n_days_of_month/nmonths)*prev_closing_liability
				wdv-=depreciation

			data.append([month_start.date(),month_end.date(), n,mlp2,n_days_of_month, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),round(closing_liability, 3)])

		if month_end>end_date:
			month_end=end_date

		if current_date3.month==12:
			current_date3=datetime(current_date3.year + 1, 1, 1)
		else:
			current_date3=datetime(current_date3.year, current_date3.month + 1, 1)
			

	# Store Calculated Data in Dataframe and Save it in Excel File 	
	if not data:
		frappe.msgprint("No Data Calculated")

	for i in range(len(data)):
		data[i].insert(4,pv_arr[i])

	data.append(['','',total_days,round(total_mlp,3),round(total_pv,3),nmonths,round(total_depre,3),'',round(total_interest_cost,3),''])
	
	df = pd.DataFrame(data, columns=columns)

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
	file_name = f"lms_report_month_based{docname}_{cnt_time}.xlsx"
	folder = "Home"
	
	file_doc = save_file(file_name, output.read(), dt="Lease Management", dn=docname, folder=folder, decode=False)

	return {
    	"file_url": file_doc.file_url
	}

# ===================================================================================
def generate_lease_report_without_escalation(start_date,end_date,docname,cnt_time):
	doc = frappe.get_doc("Lease Management",docname)
	mlp=float(doc.monthly_rent)
	mlp2=float(doc.monthly_rent)

	# # Discounting Rate
	disc_doc=(float(doc.discounting_rate)/100)

	if doc.calculation_rate_type=="Daily Rate":
		daily_rate=(1+(disc_doc))**(1/365)-1

	arg_sd=start_date
	arg_ed=end_date+ timedelta(days=1)
	diff_years = relativedelta(arg_ed,arg_sd)
	diff_years=int(str(diff_years.years))

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
	data=[]
	pv_arr=['']
	
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

		if (doc.previous_wdv)!=0:
			prev_closing_liability_wdv=float(doc.previous_wdv)
			depreciation=(n/total_days)*prev_closing_liability_wdv
			total_depre+=depreciation
		else:
			depreciation=(n/total_days)*prev_closing_liability
			total_depre+=depreciation
		
		if month_end>end_date:
			month_end=end_date

		if current_date2.month==12:
			current_date2=datetime(current_date2.year + 1, 1, 1)
		else:
			current_date2=datetime(current_date2.year, current_date2.month + 1, 1)		
	if (doc.previous_wdv)!=0:
		prev_wdv=float(doc.previous_wdv)
	else:
		prev_wdv=total_depre
	wdv=prev_wdv
	closing_liability=prev_closing_liability
	total_interest_cost=0
	data.insert(0,['','','','','',round(wdv,3),'',round(closing_liability,3)])

	# calc depre,wdv
	while current_date3<=end_date:
		cnt2+=1
		month_start=current_date3

		_,last_day=monthrange(current_date3.year, current_date3.month)
		month_end=datetime(current_date3.year, current_date3.month, last_day)

		month_start2=current_date3.replace(day=1)
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

			data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
						round(closing_liability, 3)])
			mlp2=prev_mlp2

		else:

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
			

	# Store Calculated Data in Dataframe and Save it in Excel File 	
	if not data:
		frappe.msgprint("No Data Calculated")

	for i in range(len(data)):
		data[i].insert(4,pv_arr[i])

	data.append(['','',total_days,round(total_mlp,3),round(total_pv,3),round(total_depre,3),'',round(total_interest_cost,3),''])
	
	df = pd.DataFrame(data, columns=columns)

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
	file_name = f"lease_management_report_WE{docname}_{cnt_time}.xlsx"
	folder = "Home"
	
	file_doc = save_file(file_name, output.read(), dt="Lease Management", dn=docname, folder=folder, decode=False)

	return {
    	"file_url": file_doc.file_url
	}

# ===================================================================================
def generate_lease_report_month_based_without_escalation(start_date,end_date,docname,cnt_time):
	doc = frappe.get_doc("Lease Management",docname)
	mlp=float(doc.monthly_rent)
	mlp2=float(doc.monthly_rent)
	
	# Discounting Rate
	disc_doc=(float(doc.discounting_rate)/100)

	if doc.calculation_rate_type=="Monthly Rate":
		daily_rate=(1+(disc_doc))**(1/12)-1
		columns=["Month Start Date","Month End Date", "Month","Minimum Lease Payment (MLP)","Present Value of MLP","Days in Month", "Depreciation on Right to Use", "Written Down Value (WDV)", "Interest Cost", "Closing Liability"]

	arg_sd=start_date
	arg_ed=end_date+ timedelta(days=1)
	diff_years = relativedelta(arg_ed,arg_sd)
	diff_years=int(str(diff_years.years))

	current_date=start_date
	current_date2=start_date
	current_date3=start_date
	cnt=0
	cnt1=0
	cnt2=0
	ndays=0
	nmonths=0
	ndays_pv=0
	total_mlp=0
	total_pv=0
	total_depre=0
	data=[]
	pv_arr=['']
	
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
		if doc.calculation_rate_type=="Monthly Rate":
			n=cnt
			nmonths_val=date_difference.days +1

		if doc.calculation_rate_type=="Monthly Rate":
			total_mlp+=mlp
			if cnt==1:
				pv=mlp
				pv_arr.append(pv)
			else:
				pv=mlp/((1+daily_rate)**ndays_pv)
				pv_arr.append(pv)

		total_pv=total_pv+pv
		ndays+=n
		nmonths+=nmonths_val
		ndays_pv+=1

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
		cnt1+=1
		month_start=current_date2

		_,last_day=monthrange(current_date2.year, current_date2.month)
		month_end=datetime(current_date2.year, current_date2.month, last_day)

		if end_date<month_end:
			month_end=end_date

		date_difference = month_end - month_start
		if doc.calculation_rate_type=="Monthly Rate":
			n=cnt1
			n_depre=date_difference.days +1

		if (doc.previous_wdv)!=0:
			prev_closing_liability_wdv=float(doc.previous_wdv)
			depreciation=(n/total_days)*prev_closing_liability_wdv
			total_depre+=depreciation
		else:
			# depreciation=(n/total_days)*prev_closing_liability
			depreciation=(n_depre/nmonths)*prev_closing_liability
			total_depre+=depreciation
		
		if month_end>end_date:
			month_end=end_date

		if current_date2.month==12:
			current_date2=datetime(current_date2.year + 1, 1, 1)
		else:
			current_date2=datetime(current_date2.year, current_date2.month + 1, 1)		
	if (doc.previous_wdv)!=0:
		prev_wdv=float(doc.previous_wdv)
	else:
		prev_wdv=total_depre
	wdv=prev_wdv
	closing_liability=prev_closing_liability
	total_interest_cost=0
	data.insert(0,['','','','','','',round(wdv,3),'',round(closing_liability,3)])

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
		if doc.calculation_rate_type=="Monthly Rate":
			n=cnt2
			n_days_of_month = date_difference.days +1

		if doc.calculation_rate_type=="Monthly Rate":
			
			interest_cost=((closing_liability-mlp2)*daily_rate)
			total_interest_cost+=interest_cost
			closing_liability=closing_liability+interest_cost-mlp2

			if (doc.previous_wdv)!=0:
				prev_closing_liability_wdv=float(doc.previous_wdv)
				depreciation=(n/total_days)*prev_closing_liability_wdv
				wdv-=depreciation
			else:
				depreciation=(n_days_of_month/nmonths)*prev_closing_liability
				wdv-=depreciation

			data.append([month_start.date(),month_end.date(), n,mlp2,n_days_of_month, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
						round(closing_liability, 3)])

		if month_end>end_date:
			month_end=end_date

		if current_date3.month==12:
			current_date3=datetime(current_date3.year + 1, 1, 1)
		else:
			current_date3=datetime(current_date3.year, current_date3.month + 1, 1)
			

	# Store Calculated Data in Dataframe and Save it in Excel File 	
	if not data:
		frappe.msgprint("No Data Calculated")

	for i in range(len(data)):
		data[i].insert(4,pv_arr[i])

	data.append(['','',total_days,round(total_mlp,3),round(total_pv,3),nmonths,round(total_depre,3),'',round(total_interest_cost,3),''])
	
	df = pd.DataFrame(data, columns=columns)

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
	file_name = f"lms_report_month_based_WE{docname}_{cnt_time}.xlsx"
	folder = "Home"
	
	file_doc = save_file(file_name, output.read(), dt="Lease Management", dn=docname, folder=folder, decode=False)

	return {
    	"file_url": file_doc.file_url
	}

# ===================================================================================

@frappe.whitelist()
def generate_report(docname,cnt):
	doc = frappe.get_doc("Lease Management",docname)
	date_format = "%Y-%m-%d"
	date_str1 = str(doc.agreement_start_date)
	date_str2 = str(doc.agreement_end_date)
	date1 = datetime.strptime(date_str1, date_format)
	date2 = datetime.strptime(date_str2, date_format)
	if doc.calculation_rate_type=="Monthly Rate":
		if doc.lease_period=="Short Term (Less Than 12 Months)":
			output = generate_lease_report_month_based_without_escalation(date1, date2,docname,cnt)
		else:
			output = generate_lease_report_month_based(date1, date2,docname,cnt)
	elif doc.calculation_rate_type=="Daily Rate":
		if doc.lease_period=="Short Term (Less Than 12 Months)":
			output = generate_lease_report_without_escalation(date1, date2,docname,cnt)
		else:
			output = generate_lease_report(date1, date2,docname,cnt)

	# output=get_all_active_lease_rent_data()
	return output

# def user_has_vendor_role(user):
# 	roles=frappe.get_role(user)
# 	return "Vendor" in roles
@frappe.whitelist()
def get_all_active_lease_rent_data():
	today=frappe.utils.nowdate()
	if isinstance(today, str):
		today = datetime.strptime(today, "%Y-%m-%d")
	current_month = today.strftime("%Y-%m")
	previous_month = (today - relativedelta(months=1)).strftime("%Y-%m")
	next_month = (today + relativedelta(months=1)).strftime("%Y-%m")
	leases=frappe.get_all("Lease Management",filters={"agreement_start_date": ("<=", today),"agreement_end_date": (">=", today)},fields=["name"])
	monthly_totals = {
		"Previous Month": 0.0,
		"Current Month": 0.0,
		"Next Month": 0.0
	}
	# res=[]
	
	for lease in leases:
		lease_doc = frappe.get_doc("Lease Management", lease.name)
		timeline_l = lease_doc.get_lease_rent_timeline()  

		monthly_totals["Previous Month"] += timeline_l.get(previous_month, 0)
		monthly_totals["Current Month"] += timeline_l.get(current_month, 0)
		monthly_totals["Next Month"] += timeline_l.get(next_month, 0)

		# res.append({lease.name:timeline_l})
	return monthly_totals

@frappe.whitelist()
def get_lease_rent_dashboard_chart():
    data = get_all_active_lease_rent_data()

    return {
        "labels": list(data.keys()),  # ["Previous Month", "Current Month", "Next Month"]
        "datasets": [
            {
                "name": "Lease Rent",
                "values": list(data.values())  # [1000.0, 1200.0, 1400.0]
            }
        ],
        "type": "bar",       # chart type
        "colors": ["#7cd6fd"]  # optional
    }

class LeaseManagement(Document):
	# pass
	def validate(self):
		for row in self.escalation:
			# if row.escalation_type=='Per Annum' and not row.rate:
			# 	frappe.throw("Rate Field Required in Escalation")
			if row.escalation_type=='Based On Dates' and not row.start_date:
				frappe.throw("Start Date Field Required in Escalation")
			if row.escalation_type=='Based On Dates' and not row.end_date:
				frappe.throw("End Date Field Required in Escalation")
			# if row.escalation_type=='Based On Dates' and not row.monthly_rent:
			# 	frappe.throw("Monthly Rent Field Required in Escalation")
			# if row.escalation_type=='Per Annum and Fixed Amount' and not row.rate:
			# 	frappe.throw("Rate Field Required in Escalation")
			# if row.escalation_type=='Per Annum and Fixed Amount' and not row.fixed_amount:
			# 	frappe.throw("Fixed Amount Field Required in Escalation")

	# def before_insert(self):
    # 	# On new record creation, populate invoice_details
	# 	if self.agreement_start_date and self.agreement_end_date:
	# 		self.populate_invoice_details()

	# def before_save(self):
	# 	# On updates, check if agreement dates changed
	# 	old_doc = self.get_doc_before_save()
	# 	if old_doc:
	# 		if (old_doc.agreement_start_date != self.agreement_start_date) or (old_doc.agreement_end_date != self.agreement_end_date):
	# 			# Clear existing rows first
	# 			self.set("invoice_details", [])
	# 			# Re-populate
	# 			if self.agreement_start_date and self.agreement_end_date:
	# 				self.populate_invoice_details()

	# def populate_invoice_details(self):
	# 	# Convert string dates to date objects
	# 	start_date = datetime.strptime(self.agreement_start_date, "%Y-%m-%d").date()
	# 	end_date = datetime.strptime(self.agreement_end_date, "%Y-%m-%d").date()
	# 	current_date = start_date

	# 	while current_date <= end_date:
	# 		self.append("invoice_details", {
	# 			"month": current_date.strftime("%B %Y"),
	# 			"invoice_date": current_date,
	# 			"invoice_attachment": ''  # initialize empty
	# 		})
	# 		current_date += relativedelta(months=1)

	def get_lease_rent_timeline(self):
		doc = frappe.get_doc("Lease Management",self.name)
		mlp=float(doc.monthly_rent)
		start_date = doc.agreement_start_date
		end_date = doc.agreement_end_date
		if isinstance(doc.agreement_start_date, datetime):
			start_date = doc.agreement_start_date
		else:
			start_date = datetime.combine(doc.agreement_start_date, datetime.min.time())

		if isinstance(doc.agreement_end_date, datetime):
			end_date = doc.agreement_end_date
		else:
			end_date = datetime.combine(doc.agreement_end_date, datetime.min.time())
		# # Discounting Rate
		# disc_doc=(float(doc.discounting_rate)/100)

		# if doc.calculation_rate_type=="Daily Rate":
		# 	daily_rate=(1+(disc_doc))**(1/365)-1
		# elif doc.calculation_rate_type=="Monthly Rate":
		# 	daily_rate=(1+(disc_doc))**(1/12)-1
		arg_sd=start_date
		arg_ed=end_date+ timedelta(days=1)
		diff_years = relativedelta(arg_ed,arg_sd)
		diff_years=int(str(diff_years.years))

		# month_ranges=[]
		# deprec=[]
		timeline={}
		current_date=start_date
		cnt=0
		etype=[]
		escl_dates_pafr=[]
		escl_dates_bdates=[]
		total_escl_dates_bdates=[]
		escl_dates_pannum=[]
		date_list=[]
		calc_dict={}
		calc_keys=[]
		esc_bd_end_date=None
		bd_start_date=""
		bd_end_date=""
		cnt_etype=0
		mrent=None
		rate=None
		famt=None
		new_start_date=[]

		for child in doc.escalation:
			escl_type=child.escalation_type
			if escl_type:
				etype.append(escl_type)
				if "Based On Dates"==escl_type:
					if child.monthly_rent is None:
						monthly_rent_bdates=0
					else:
						monthly_rent_bdates=float(child.monthly_rent)
					if child.rate is None:
						rate_bdates=0
					else:
						rate_bdates=float(child.rate)
					if child.fixed_amount is None:
						fixed_amt_bdates=0
					else:
						fixed_amt_bdates=float(child.fixed_amount)
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
					# dsubkey=str(monthly_rent_bdates)+'-'+str(rate_bdates)+'-'+str(fixed_amt_bdates)
					dsubkey=str(rate_bdates)+'-'+str(monthly_rent_bdates)+'-'+str(fixed_amt_bdates)

					calc_dict[dkey]={dsubkey:escl_dates_bdates}
					# calc_dict.setdefault(dkey, {}).setdefault(monthly_rent_bdates, []).extend(escl_dates_bdates)
					total_escl_dates_bdates+=escl_dates_bdates
					if len(new_start_date)>0:
						l=len(new_start_date)
						for q in range(l):
							if new_start_date[q] in total_escl_dates_bdates:
								new_start_date.remove(new_start_date[q])
								break
					escl_dates_bdates=[]

		for i in range(len(etype)):
			if etype[i]=="Per Annum" or etype[i]=="Per Annum and Fixed Amount":
				if etype[i-1]=="Based On Dates":
					bd_date=doc.escalation[i-1]
					d=bd_date.end_date
					esc_bd_end_date=d+timedelta(days=1)
					
		if len(total_escl_dates_bdates)>0:
			date_list=total_escl_dates_bdates

		for child in doc.escalation:
			if child.monthly_rent is None:
				monthly_rent=0
			else:
				monthly_rent=float(child.monthly_rent)
			if child.rate is None:
				rate=0
			else:
				rate=float(child.rate)
			if child.fixed_amount is None:
				fixed_amt=0
			else:
				fixed_amt=float(child.fixed_amount)
			if child.escalation_type=="Per Annum":
				cnt_etype+=1
				# escl_rate_pannum=float(child.rate)
				for i in range(diff_years):
					if i==0 and cnt_etype==1:
						# for j in range(len(new_start_date)):
						# 	if new_date>=new_start_date[j]:
						# 		new_date=new_start_date[j]
						# 	elif new_date<new_start_date[j]:
						# 		new_date = start_date + relativedelta(years=1)
						# if len(new_start_date)==0:
						# 	new_date = start_date + relativedelta(years=1)
						if esc_bd_end_date is None:
							new_date=start_date + relativedelta(years=1)
						else:
							new_date=esc_bd_end_date
						if new_date not in date_list:
							if isinstance(new_date, datetime):
								new_date = new_date.date()
							escl_dates_pannum.append(new_date)
							new_date=new_date + relativedelta(years=1)
					else:
						if new_date in date_list:
							new_date=new_date + relativedelta(years=1)
							break
						if isinstance(new_date, datetime):
							new_date = new_date.date()
						if new_date<end_date.date() and new_date not in date_list:
							escl_dates_pannum.append(new_date)	
							new_date=new_date + relativedelta(years=1)
				dkey="Per Annum"+'-'+str(rate)
				dsubkey=str(rate)+'-'+str(monthly_rent)+'-'+str(fixed_amt)
				calc_dict[dkey]={dsubkey:escl_dates_pannum}
				escl_dates_pannum=[]
			
			elif child.escalation_type=="Per Annum and Fixed Amount":
				cnt_etype+=1
				# escl_rate_pafr=float(child.rate)
				# fixed_amt_pafr=float(child.fixed_amount)
				for i in range(diff_years):
					if i==0 and cnt_etype==1:
						# for j in range(len(new_start_date)):
						# 	if new_date>=new_start_date[j]:
						# 		new_date=new_start_date[j]
						# 	elif new_date<new_start_date[j]:
						# 		new_date = start_date + relativedelta(years=1)
						# if len(new_start_date)==0:
						# 	new_date = start_date + relativedelta(years=1)
						if esc_bd_end_date is None:
							new_date=start_date + relativedelta(years=1)
						else:
							new_date=esc_bd_end_date

						if new_date not in date_list:
							if isinstance(new_date, datetime):
								new_date = new_date.date()
							escl_dates_pafr.append(new_date)
							new_date=new_date + relativedelta(years=1)
					else:
						if new_date in date_list:
							new_date=new_date + relativedelta(years=1)
							break
						if isinstance(new_date, datetime):
							new_date = new_date.date()
						if new_date<end_date.date() and new_date not in date_list:
							escl_dates_pafr.append(new_date)
							new_date=new_date + relativedelta(years=1)	
				dkey="Per Annum and Fixed Amount"+'-'+str(rate)+'-'+str(fixed_amt)
				dsubkey=str(rate)+'-'+str(monthly_rent)+'-'+str(fixed_amt)
				calc_dict[dkey]={dsubkey:escl_dates_pafr}	
				escl_dates_pafr=[]

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
				subkey=next(iter(sub_dict))
				# rate_val=next(iter(sub_dict))
				# pa_rate=float(rate_val)
				edates_pannum+=sub_dict[subkey]
				dict_ed_pannum[subkey]=sub_dict[subkey]

			elif calc_escl_type=="Based On Dates":
				sub_dict=calc_dict[temp_str]
				subkey=next(iter(sub_dict))
				# mrent_val=next(iter(sub_dict))
				# mrent=float(mrent_val)
				edates_bd+=sub_dict[subkey]
				dict_ed_bdates[subkey]=sub_dict[subkey]


			elif calc_escl_type=="Per Annum and Fixed Amount":
				sub_dict=calc_dict[temp_str]
				# temp_val=next(iter(sub_dict))
				# pafa_rate,famt=temp_val
				subkey=next(iter(sub_dict))
				# temp=temp_val.split('-')
				# pafa_rate=temp[0]
				# famt=temp[1]
				edates_pafa+=sub_dict[subkey]
				dict_ed_pafa[subkey]=sub_dict[subkey]
				

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
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pannum[k]
						if current_date.date() in escl:
							# pa_rate=rate_pa
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							mlp=mlp+(rate*mlp/100)+famt
							break
					# mlp=mlp+(pa_rate*mlp/100)
				elif current_date.date() in edates_bd:
					for k in dict_ed_bdates.keys():
						# rpm=float(k)
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_bdates[k]
						if current_date.date() in escl:
							# mrent=rpm
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							if mrent==0 and rate==0 and famt==0:
								mlp=0
							mlp=mlp+(rate*mlp/100)+famt
							
							break
					# mlp=mrent
				elif current_date.date() in edates_pafa:
					for k in dict_ed_pafa.keys():
						temp_val=k
						temp=temp_val.split('-')
						# rate_pa=temp[0]
						# f=temp[1]
						escl=dict_ed_pafa[k]
						if current_date.date() in escl:
							# pafa_rate=float(rate_pa)
							# famt=float(f)
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							mlp=mlp+(rate*mlp/100)+famt
							
							break
				timeline[current_date.date().strftime("%Y-%m")] = round(mlp, 3)
				mlp=prev_mlp
				if mrent==0 and rate==0 and famt==0:
					mlp=prev_mlp
			else:
				prev_mlp=mlp
				
				if current_date.date() in edates_pannum:
					for k in dict_ed_pannum.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pannum[k]
						if current_date.date() in escl:
							# pa_rate=rate_pa
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							mlp=mlp+(rate*mlp/100)+famt
							break
					# mlp=mlp+(pa_rate*mlp/100)
				elif current_date.date() in edates_bd:
					for k in dict_ed_bdates.keys():
						# rpm=float(k)
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_bdates[k]
						if current_date.date() in escl:
							# mrent=rpm
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							if mrent==0 and rate==0 and famt==0:
								mlp=0
							mlp=mlp+(rate*mlp/100)+famt
							break
					# mlp=mrent
				elif current_date.date() in edates_pafa:
					for k in dict_ed_pafa.keys():
						temp_val=k
						temp=temp_val.split('-')
						# rate_pa=temp[0]
						# f=temp[1]
						escl=dict_ed_pafa[k]
						if current_date.date() in escl:
							# pafa_rate=float(rate_pa)
							# famt=float(f)
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							mlp=mlp+(rate*mlp/100)+famt
							break
				timeline[current_date.date().strftime("%Y-%m")] = round(mlp, 3)
				if mrent==0 and rate==0 and famt==0:
					mlp=prev_mlp
			if month_end>end_date:
				month_end=end_date

			if current_date.month==12:
				current_date=datetime(current_date.year + 1, 1, 1)
			else:
				current_date=datetime(current_date.year, current_date.month + 1, 1)
		return timeline

	def get_lease_monthly_data(self):
		doc = frappe.get_doc("Lease Management",self.name)
		mlp=float(doc.monthly_rent)
		start_date = doc.agreement_start_date
		end_date = doc.agreement_end_date
		if isinstance(doc.agreement_start_date, datetime):
			start_date = doc.agreement_start_date
		else:
			start_date = datetime.combine(doc.agreement_start_date, datetime.min.time())

		if isinstance(doc.agreement_end_date, datetime):
			end_date = doc.agreement_end_date
		else:
			end_date = datetime.combine(doc.agreement_end_date, datetime.min.time())
		arg_sd=start_date
		arg_ed=end_date+ timedelta(days=1)
		diff_years = relativedelta(arg_ed,arg_sd)
		diff_years=int(str(diff_years.years))
		monthly_data={}
		current_date=start_date
		cnt=0
		etype=[]
		escl_dates_pafr=[]
		escl_dates_bdates=[]
		total_escl_dates_bdates=[]
		escl_dates_pannum=[]
		date_list=[]
		calc_dict={}
		calc_keys=[]
		esc_bd_end_date=None
		bd_start_date=""
		bd_end_date=""
		cnt_etype=0
		new_start_date=[]

		for child in doc.escalation:
			escl_type=child.escalation_type
			if escl_type:
				etype.append(escl_type)
				if "Based On Dates"==escl_type:
					if child.monthly_rent is None:
						monthly_rent_bdates=0
					else:
						monthly_rent_bdates=float(child.monthly_rent)
					if child.rate is None:
						rate_bdates=0
					else:
						rate_bdates=float(child.rate)
					if child.fixed_amount is None:
						fixed_amt_bdates=0
					else:
						fixed_amt_bdates=float(child.fixed_amount)
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
					# dsubkey=str(monthly_rent_bdates)+'-'+str(rate_bdates)+'-'+str(fixed_amt_bdates)
					dsubkey=str(rate_bdates)+'-'+str(monthly_rent_bdates)+'-'+str(fixed_amt_bdates)

					calc_dict[dkey]={dsubkey:escl_dates_bdates}
					# calc_dict.setdefault(dkey, {}).setdefault(monthly_rent_bdates, []).extend(escl_dates_bdates)
					total_escl_dates_bdates+=escl_dates_bdates
					if len(new_start_date)>0:
						l=len(new_start_date)
						for q in range(l):
							if new_start_date[q] in total_escl_dates_bdates:
								new_start_date.remove(new_start_date[q])
								break
					escl_dates_bdates=[]

		for i in range(len(etype)):
			if etype[i]=="Per Annum" or etype[i]=="Per Annum and Fixed Amount":
				if etype[i-1]=="Based On Dates":
					bd_date=doc.escalation[i-1]
					d=bd_date.end_date
					esc_bd_end_date=d+timedelta(days=1)
					
		if len(total_escl_dates_bdates)>0:
			date_list=total_escl_dates_bdates

		for child in doc.escalation:
			if child.monthly_rent is None:
				monthly_rent=0
			else:
				monthly_rent=float(child.monthly_rent)
			if child.rate is None:
				rate=0
			else:
				rate=float(child.rate)
			if child.fixed_amount is None:
				fixed_amt=0
			else:
				fixed_amt=float(child.fixed_amount)
			if child.escalation_type=="Per Annum":
				cnt_etype+=1
				for i in range(diff_years):
					if i==0 and cnt_etype==1:
						if esc_bd_end_date is None:
							new_date=start_date + relativedelta(years=1)
						else:
							new_date=esc_bd_end_date
						if new_date not in date_list:
							if isinstance(new_date, datetime):
								new_date = new_date.date()
							escl_dates_pannum.append(new_date)
							new_date=new_date + relativedelta(years=1)
					else:
						if new_date in date_list:
							new_date=new_date + relativedelta(years=1)
							break
						if isinstance(new_date, datetime):
							new_date = new_date.date()
						if new_date<end_date.date() and new_date not in date_list:
							escl_dates_pannum.append(new_date)	
							new_date=new_date + relativedelta(years=1)
				dkey="Per Annum"+'-'+str(rate)
				dsubkey=str(rate)+'-'+str(monthly_rent)+'-'+str(fixed_amt)
				calc_dict[dkey]={dsubkey:escl_dates_pannum}
				escl_dates_pannum=[]
			
			elif child.escalation_type=="Per Annum and Fixed Amount":
				cnt_etype+=1
				for i in range(diff_years):
					if i==0 and cnt_etype==1:
						if esc_bd_end_date is None:
							new_date=start_date + relativedelta(years=1)
						else:
							new_date=esc_bd_end_date

						if new_date not in date_list:
							if isinstance(new_date, datetime):
								new_date = new_date.date()
							escl_dates_pafr.append(new_date)
							new_date=new_date + relativedelta(years=1)
					else:
						if new_date in date_list:
							new_date=new_date + relativedelta(years=1)
							break
						if isinstance(new_date, datetime):
							new_date = new_date.date()
						if new_date<end_date.date() and new_date not in date_list:
							escl_dates_pafr.append(new_date)
							new_date=new_date + relativedelta(years=1)	
				dkey="Per Annum and Fixed Amount"+'-'+str(rate)+'-'+str(fixed_amt)
				dsubkey=str(rate)+'-'+str(monthly_rent)+'-'+str(fixed_amt)
				calc_dict[dkey]={dsubkey:escl_dates_pafr}	
				escl_dates_pafr=[]

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
				subkey=next(iter(sub_dict))
				# rate_val=next(iter(sub_dict))
				# pa_rate=float(rate_val)
				edates_pannum+=sub_dict[subkey]
				dict_ed_pannum[subkey]=sub_dict[subkey]

			elif calc_escl_type=="Based On Dates":
				sub_dict=calc_dict[temp_str]
				subkey=next(iter(sub_dict))
				# mrent_val=next(iter(sub_dict))
				# mrent=float(mrent_val)
				edates_bd+=sub_dict[subkey]
				dict_ed_bdates[subkey]=sub_dict[subkey]


			elif calc_escl_type=="Per Annum and Fixed Amount":
				sub_dict=calc_dict[temp_str]
				# temp_val=next(iter(sub_dict))
				# pafa_rate,famt=temp_val
				subkey=next(iter(sub_dict))
				# temp=temp_val.split('-')
				# pafa_rate=temp[0]
				# famt=temp[1]
				edates_pafa+=sub_dict[subkey]
				dict_ed_pafa[subkey]=sub_dict[subkey]
				

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
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pannum[k]
						if current_date.date() in escl:
							# pa_rate=rate_pa
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							mlp=mlp+(rate*mlp/100)+famt
							break
					# mlp=mlp+(pa_rate*mlp/100)
				elif current_date.date() in edates_bd:
					for k in dict_ed_bdates.keys():
						# rpm=float(k)
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_bdates[k]
						if current_date.date() in escl:
							# mrent=rpm
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							if mrent==0 and rate==0 and famt==0:
								mlp=0
							mlp=mlp+(rate*mlp/100)+famt
							
							break
					# mlp=mrent
				elif current_date.date() in edates_pafa:
					for k in dict_ed_pafa.keys():
						temp_val=k
						temp=temp_val.split('-')
						# rate_pa=temp[0]
						# f=temp[1]
						escl=dict_ed_pafa[k]
						if current_date.date() in escl:
							# pafa_rate=float(rate_pa)
							# famt=float(f)
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							mlp=mlp+(rate*mlp/100)+famt
							
							break
				val=[month_start.date(),month_end.date()]
				monthly_data[current_date.date().strftime("%Y-%m")] = val
				mlp=prev_mlp
				if mrent==0 and rate==0 and famt==0:
					mlp=prev_mlp
			else:
				prev_mlp=mlp
				
				if current_date.date() in edates_pannum:
					for k in dict_ed_pannum.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pannum[k]
						if current_date.date() in escl:
							# pa_rate=rate_pa
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							mlp=mlp+(rate*mlp/100)+famt
							break
					# mlp=mlp+(pa_rate*mlp/100)
				elif current_date.date() in edates_bd:
					for k in dict_ed_bdates.keys():
						# rpm=float(k)
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_bdates[k]
						if current_date.date() in escl:
							# mrent=rpm
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							if mrent==0 and rate==0 and famt==0:
								mlp=0
							mlp=mlp+(rate*mlp/100)+famt
							break
					# mlp=mrent
				elif current_date.date() in edates_pafa:
					for k in dict_ed_pafa.keys():
						temp_val=k
						temp=temp_val.split('-')
						# rate_pa=temp[0]
						# f=temp[1]
						escl=dict_ed_pafa[k]
						if current_date.date() in escl:
							# pafa_rate=float(rate_pa)
							# famt=float(f)
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
							mlp=mlp+(rate*mlp/100)+famt
							break
				val=[month_start.date(),month_end.date()]
				monthly_data[current_date.date().strftime("%Y-%m")] = val
				if mrent==0 and rate==0 and famt==0:
					mlp=prev_mlp
			if month_end>end_date:
				month_end=end_date

			if current_date.month==12:
				current_date=datetime(current_date.year + 1, 1, 1)
			else:
				current_date=datetime(current_date.year, current_date.month + 1, 1)
		return monthly_data

	# def get_lease_rent_timeline(doc):
	# 	# start_date = doc.agreement_start_date
	# 	# end_date = doc.agreement_end_date
	# 	if isinstance(doc.agreement_start_date, datetime):
	# 		start_date = doc.agreement_start_date
	# 	else:
	# 		start_date = datetime.combine(doc.agreement_start_date, datetime.min.time())

	# 	if isinstance(doc.agreement_end_date, datetime):
	# 		end_date = doc.agreement_end_date
	# 	else:
	# 		end_date = datetime.combine(doc.agreement_end_date, datetime.min.time())
	# 	mlp=float(doc.monthly_rent)
	# 	arg_sd=start_date
	# 	arg_ed=end_date+timedelta(days=1)
	# 	diff_years=relativedelta(arg_ed,arg_sd)
	# 	diff_years=int(str(diff_years.years))
	# 	current_date=start_date
	# 	cnt=0
	# 	timeline={}
	# 	etype=[]
	# 	esc_bdates=['']
	# 	esc_bd_end_date=None
	# 	current_rent=mlp

	# 	for child in doc.escalation:
	# 		if child.escalation_type:
	# 			etype.append(child.escalation_type)

	# 	for i in range(len(etype)):
	# 		if etype[i]=="Per Annum" or etype[i]=="Per Annum and Fixed Amount":
	# 			if etype[i-1]=="Based On Dates":
	# 				bd_date=doc.escalation[i-1]
	# 				d=bd_date.end_date
	# 				esc_bd_end_date=d+timedelta(days=1)

	# 	for child in doc.escalation:
	# 		escl_type=child.escalation_type

	# 		if escl_type=="Based On Dates":
	# 			# if isinstance(child.start_date, str) and isinstance(child.end_date, str):
	# 			# 	esc_start = datetime.strptime(child.start_date, "%Y-%m-%d")
	# 			# 	esc_end = datetime.strptime(child.start_date, "%Y-%m-%d")
	# 			# else:
	# 			# 	esc_start=child.start_date
	# 			# 	esc_end=child.end_date
	# 			if isinstance(child.start_date, datetime):
	# 				esc_start = child.start_date
	# 			else:
	# 				esc_start = datetime.combine(child.start_date, datetime.min.time())
	# 			if isinstance(child.end_date, datetime):
	# 				esc_end = child.end_date
	# 			else:
	# 				esc_end = datetime.combine(child.end_date, datetime.min.time())
	# 			loop_current_date=current_date

	# 			end_date = end_date if isinstance(end_date, datetime) else datetime.combine(end_date, datetime.min.time())
		
	# 			while loop_current_date<=end_date:
	# 				loop_current_date = loop_current_date if isinstance(loop_current_date, datetime) else datetime.combine(loop_current_date, datetime.min.time())
	# 				if esc_start <= loop_current_date <= esc_end:
	# 					if child.rate and not (child.fixed_amount):
	# 						current_rent = mlp + (float(child.rate)*mlp/100)
	# 					elif child.rate and child.fixed_amount:
	# 						current_rent = mlp + (float(child.rate)*mlp/100) + float(child.fixed_amount)
	# 					elif child.monthly_rent and not(child.rate) and not(child.fixed_amount):
	# 						current_rent=float(child.monthly_rent)

	# 					timeline[loop_current_date.strftime("%Y-%m")] = round(current_rent, 3)
	# 					esc_bdates.append(loop_current_date)
	# 				if loop_current_date.month==12:
	# 					loop_current_date=datetime(loop_current_date.year + 1, 1, 1)
	# 				else:
	# 					loop_current_date=datetime(loop_current_date.year, loop_current_date.month + 1, 1)

	# 		elif escl_type=="Per Annum":
	# 			if esc_bd_end_date is not None:
	# 				loop_current_date=esc_bd_end_date
	# 			else:
	# 				loop_current_date=current_date

	# 			if isinstance(loop_current_date, str) and loop_current_date.strip():
	# 				try:
	# 					loop_current_date = datetime.strptime(loop_current_date, "%Y-%m-%d")
	# 				except ValueError:
	# 					frappe.throw(f"Invalid date format: {loop_current_date}")
	# 			loop_current_date = loop_current_date if isinstance(loop_current_date, datetime) else datetime.combine(loop_current_date, datetime.min.time())
	# 			while loop_current_date<=end_date:
	# 				if loop_current_date not in esc_bdates:
	# 					if child.rate and not (child.fixed_amount):
	# 						current_rent = mlp + (float(child.rate)*mlp/100)
	# 					elif child.rate and child.fixed_amount:
	# 						current_rent = mlp + (float(child.rate)*mlp/100) + float(child.fixed_amount)
	# 					elif child.monthly_rent and not(child.rate) and not(child.fixed_amount):
	# 						current_rent=float(child.monthly_rent)
	# 					timeline[loop_current_date.strftime("%Y-%m")] = round(current_rent, 3)

	# 				loop_current_date=loop_current_date+relativedelta(years=1)
			
	# 		elif escl_type=="Per Annum and Fixed Amount":
	# 			if esc_bd_end_date is not None:
	# 				loop_current_date=esc_bd_end_date
	# 			else:
	# 				loop_current_date=current_date
	# 			if isinstance(loop_current_date, str) and loop_current_date.strip():
	# 				try:
	# 					loop_current_date = datetime.strptime(loop_current_date, "%Y-%m-%d")
	# 				except ValueError:
	# 					frappe.throw(f"Invalid date format: {loop_current_date}")
	# 			loop_current_date = loop_current_date if isinstance(loop_current_date, datetime) else datetime.combine(loop_current_date, datetime.min.time())
	# 			while loop_current_date<=end_date:
	# 				if loop_current_date not in esc_bdates:
	# 					if child.rate and not (child.fixed_amount):
	# 						current_rent = mlp + (float(child.rate)*mlp/100)
	# 					elif child.rate and child.fixed_amount:
	# 						current_rent = mlp + (float(child.rate)*mlp/100) + float(child.fixed_amount)
	# 					elif child.monthly_rent and not(child.rate) and not(child.fixed_amount):
	# 						current_rent=float(child.monthly_rent)
	# 					timeline[loop_current_date.strftime("%Y-%m")] = round(current_rent, 3)

	# 				loop_current_date=loop_current_date+relativedelta(years=1)

	# 	return timeline

# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe,pdb
from frappe import _
from frappe.model.document import Document
from datetime import datetime,timedelta,time
from calendar import monthrange
import calendar
from dateutil.relativedelta import relativedelta
from frappe import db
import pandas as pd
import io
from frappe.utils.file_manager import save_file
from openpyxl.utils import get_column_letter
from frappe.utils import nowdate, now_datetime

def calculate_daily_rate(doc):
	disc_doc=float(doc.discounting_rate)/100
	if doc.calculation_rate_type == "Daily Rate":
		return (1+disc_doc)**(1/365) - 1
	return (1+disc_doc)**(1/12) - 1

def get_diff_years(start_date,end_date):
	arg_sd=start_date
	arg_ed=end_date+ timedelta(days=1)
	diff_years = relativedelta(arg_ed,arg_sd)
	diff_years=int(str(diff_years.years))
	return diff_years

def get_month_details(date):
	month_start=date
	_,last_day=monthrange(date.year, date.month)
	month_end=datetime(date.year, date.month, last_day)

	month_start2=date.replace(day=1)
	_,last_day2=monthrange(date.year, date.month)
	month_end2=datetime(date.year, date.month, last_day2)
	date_difference2 = month_end2 - month_start2
	total_days_of_month = date_difference2.days +1

	return month_start, month_end,month_start2, month_end2, total_days_of_month

def get_escalation_dates(doc,current_date,start_date,end_date,diff_years):
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
	famt=0
	mrent=0
	rate=0
	esc_bd_end_date=None
	escalation=True
	edates_pannum=[]
	edates_bd=[]
	edates_pafa=[]
	dict_ed_pannum={}
	dict_ed_pafa={}
	dict_ed_bdates={}
	diff_annually=False
	per_annum_rows = [child for child in doc.escalation if child.escalation_type == "Per Annum"]
	if len(per_annum_rows) == 1:
		row = per_annum_rows[0]
		rate_val = float(row.rate) if row.rate is not None else 0
		rent_val = float(row.monthly_rent) if row.monthly_rent is not None else 0
		fixed_amt_val = float(row.fixed_amount) if row.fixed_amount is not None else 0

		if rate_val == 0 and rent_val == 0 and fixed_amt_val == 0:
			escalation = False
			return escalation, [], [], [], {}, {}, {}, None, False, 0, 0, 0

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
	else:
		if not doc.escalation:
			escalation=False
	
	if escalation:
		for i in range(len(etype)):
				if etype[i]=="Per Annum" or etype[i]=="Per Annum and Fixed Amount":
					if etype[i-1]=="Based On Dates":
						bd_date=doc.escalation[i-1]
						d=bd_date.end_date
						esc_bd_end_date=d+timedelta(days=1)
		if len(total_escl_dates_bdates)>0:
			date_list=total_escl_dates_bdates

		for child in doc.escalation :
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
							continue
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

		for key in calc_dict :
			calc_keys.append(key)

	if escalation:
		for i in range(len(calc_keys)):
			temp_str=calc_keys[i]
			temp=calc_keys[i].split('-')
			calc_escl_type=temp[0]

			if calc_escl_type=="Per Annum":
				sub_dict=calc_dict[temp_str]
				subkey=next(iter(sub_dict))
				edates_pannum+=sub_dict[subkey]
				dict_ed_pannum[subkey]=sub_dict[subkey]

			elif calc_escl_type=="Based On Dates":
				sub_dict=calc_dict[temp_str]
				subkey=next(iter(sub_dict))
				edates_bd+=sub_dict[subkey]
				dict_ed_bdates[subkey]=sub_dict[subkey]


			elif calc_escl_type=="Per Annum and Fixed Amount":
				sub_dict=calc_dict[temp_str]
				subkey=next(iter(sub_dict))
				edates_pafa+=sub_dict[subkey]
				dict_ed_pafa[subkey]=sub_dict[subkey]

	if (len(etype)==1 and etype[0]=="Per Annum") or (len(etype)==1 and etype[0]=="Per Annum and Fixed Amount"):
		month_start=current_date

		_,last_day=monthrange(current_date.year, current_date.month)
		month_end=datetime(current_date.year, current_date.month, last_day)

		month_start2=current_date.replace(day=1)
		_,last_day2=monthrange(current_date.year, current_date.month)
		month_end2=datetime(current_date.year, current_date.month, last_day2)
		date_difference2 = month_end2 - month_start2
		total_days_of_month = date_difference2.days +1

		date_difference = month_end - month_start
		n = date_difference.days +1

		if n<total_days_of_month:
			diff_annually=True

	return escalation,edates_pannum,edates_bd,edates_pafa,dict_ed_pannum,dict_ed_bdates,dict_ed_pafa,esc_bd_end_date,diff_annually,rate,mrent,famt

def get_n(current_date,diff_annually):
	n_prior=0
	if diff_annually:
		if current_date.month==12:
			prior_month=1
			prior_date=datetime(current_date.year+1, prior_month,current_date.day)
		else:
			prior_month=current_date.month+1
			prior_date=datetime(current_date.year, prior_month,current_date.day)
		prior_day=current_date.day
		prior_month_end=datetime(prior_date.year, prior_date.month,prior_day)

		prior_month_start=prior_date.replace(day=1)

		diff_prior_month = prior_month_end - prior_month_start
		n_prior = diff_prior_month.days
	return n_prior

def calculate_depreciation(doc,n,total_days,prev_closing_liability):
	if doc.previous_wdv:
		prev_closing_liability_wdv=float(doc.previous_wdv)
		if prev_closing_liability_wdv!=0:
			return (n/total_days)*prev_closing_liability_wdv
	return (n/total_days)*(prev_closing_liability)

def date_increment(current_date,diff_annually):
	if current_date.month==12:
		if diff_annually:
			current_date=datetime(current_date.year+1, 1,current_date.day) - relativedelta(days=1)
		else:
			current_date=datetime(current_date.year + 1, 1, 1)
	else:
		if diff_annually:
			current_date=datetime(current_date.year, current_date.month + 1,current_date.day) - relativedelta(days=1)
		else:
			current_date=datetime(current_date.year, current_date.month + 1, 1)
	return current_date

def generate_excel_report(data,columns,docname,cnt_time):
	df = pd.DataFrame(data,columns=columns)
	output = io.BytesIO()

	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		df.to_excel(writer, index=False, sheet_name='Sheet1')
		worksheet = writer.sheets['Sheet1']

		for i, col in enumerate(df.columns):
			max_length = max(
            	df[col].astype(str).map(len).max(),
            	len(col)
        	)
			col_letter = get_column_letter(i + 1)
			worksheet.column_dimensions[col_letter].width = max_length + 2

	output.seek(0)
	file_name = f"lease_agreement_report_{docname}_{cnt_time}.xlsx"
	folder = "Home"
	
	file_doc = save_file(file_name, output.read(), dt="Lease Management", dn=docname, folder=folder, decode=False)

	return {
    	"file_url": file_doc.file_url
	}

#generate lease agreement report based on daily rate
def generate_lease_report_new(start_date,end_date,docname,cnt_time):
	doc=frappe.get_doc("Lease Management",docname)
	mlp=mlp2=float(doc.monthly_rent)
	daily_rate=calculate_daily_rate(doc)
	current_date = current_date2 = current_date3 = start_date
	data=[]
	pv_arr=['']
	prev_mlp_escl=None
	prev_mlp_escl2=None
	ndays = total_mlp = total_pv = total_depre = cnt = cnt1 = cnt2 = 0

	columns=["Month Start Date","Month End Date", "Days in Month","Minimum Lease Payment (MLP)","Present Value of MLP", "Depreciation on Right to Use", "Written Down Value (WDV)", "Interest Cost", "Closing Liability"]
	diff_years=get_diff_years(start_date,end_date)
	escalation,edates_pannum,edates_bd,edates_pafa,dict_ed_pannum,dict_ed_bdates,dict_ed_pafa,esc_bd_end_date,diff_annually,rate,mrent,famt=get_escalation_dates(doc,current_date,start_date,end_date,diff_years)

	while current_date<=end_date:
		cnt+=1
		if diff_annually:
			if cnt>1:
				if current_date!=end_date:
					current_date=current_date + timedelta(days=1)
		month_start, month_end,month_start2, month_end2, total_days_of_month=get_month_details(current_date)
		n_prior=get_n(current_date,diff_annually)

		if end_date<month_end:
			month_end=end_date

		if diff_annually:
			if month_end<month_end2 and month_end==end_date:
				month_end=current_date
				month_start=current_date.replace(day=1)
			date_difference = month_end - month_start
			n_next = date_difference.days +1
			n= total_days_of_month
		else:
			date_difference = month_end - month_start
			n=date_difference.days +1

		if current_date==start_date or month_end==end_date:
			date_difference = month_end - month_start
			n = date_difference.days +1
			n_prior=n
		
		if n_prior<total_days_of_month or n<total_days_of_month:
			prev_mlp=mlp
			if not diff_annually:
				mlp=mlp*n/total_days_of_month
				if current_date.date() in edates_pannum and escalation:
					for k in dict_ed_pannum.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pannum[k]
						if current_date.date() in escl:
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
								mlp=mlp*n/total_days_of_month
							if mrent==0 and rate==0 and famt==0:
								mlp=0
							mlp=mlp+(rate*mlp/100)+famt
							prev_mlp_escl=mlp
							break
				elif current_date.date() in edates_bd and escalation:
					for k in dict_ed_bdates.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_bdates[k]
						if current_date.date() in escl:
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
								mlp=mlp*n/total_days_of_month
							if mrent==0 and rate==0 and famt==0:
								mlp=0
							mlp=mlp+(rate*mlp/100)+famt
							prev_mlp_escl=mlp
							break
				elif current_date.date() in edates_pafa and escalation:
					for k in dict_ed_pafa.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pafa[k]
						if current_date.date() in escl:
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
								mlp=mlp*n/total_days_of_month
							if mrent==0 and rate==0 and famt==0:
								mlp=0
							mlp=mlp+(rate*mlp/100)+famt
							prev_mlp_escl=mlp
							break
				total_mlp+=mlp
				if cnt==1:
					pv=mlp
					pv_arr.append(pv)
				else:
					pv=mlp/((1+daily_rate)**ndays)
					pv_arr.append(pv)
				if prev_mlp_escl is None:
					mlp=prev_mlp
				else:
					mlp=prev_mlp_escl
				if mrent==0 and rate==0 and famt==0 and escalation:
					mlp=prev_mlp
			else:
				mlp_1=mlp*n_prior/total_days_of_month
				mlp_2=0
				if current_date==start_date or month_end==end_date:
					mlp=mlp_1
				mlp_new=mlp
				if current_date.date() in edates_pannum and escalation:
					for k in dict_ed_pannum.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pannum[k]
						if current_date.date() in escl:
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
								mlp=mlp*n/total_days_of_month
							if mrent==0 and rate==0 and famt==0:
								mlp=0
							mlp=mlp+(rate*mlp/100)+famt
							mlp_2=mlp*n_next/total_days_of_month
							mlp_new=mlp_1+mlp_2
							prev_mlp_escl=mlp
							break		
				elif current_date.date() in edates_pafa and escalation:
					for k in dict_ed_pafa.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pafa[k]
						if current_date.date() in escl:
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp=mrent
								mlp=mlp*n/total_days_of_month
							if mrent==0 and rate==0 and famt==0:
								mlp=0
							mlp=mlp+(rate*mlp/100)+famt
							mlp_2=mlp*n_next/total_days_of_month
							mlp_new=mlp_1+mlp_2
							prev_mlp_escl=mlp
							break
				mlp=mlp_new
				total_mlp+=mlp
				if cnt==1:
					pv=mlp
					pv_arr.append(pv)
				else:
					pv=mlp/((1+daily_rate)**ndays)
					pv_arr.append(pv)
				if prev_mlp_escl is None:
					mlp=prev_mlp
				else:
					mlp=prev_mlp_escl
				if mrent==0 and rate==0 and famt==0 and escalation:
					mlp=prev_mlp

		else:
			prev_mlp=mlp
			if current_date.date() in edates_pannum and escalation:
				for k in dict_ed_pannum.keys():
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
			elif current_date.date() in edates_bd and escalation:
				for k in dict_ed_bdates.keys():
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
			elif current_date.date() in edates_pafa and escalation:
				for k in dict_ed_pafa.keys():
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
			total_mlp+=mlp
			if cnt==1:
				pv=mlp
				pv_arr.append(pv)
			else:
				pv=mlp/((1+daily_rate)**ndays)
				pv_arr.append(pv)
			if mrent==0 and rate==0 and famt==0 and escalation:
				mlp=prev_mlp
		total_pv=total_pv+pv
		ndays+=n

		current_date=date_increment(current_date,diff_annually)

	prev_closing_liability=total_pv
	total_days=ndays

	while current_date2<=end_date:
		cnt1+=1
		month_start=current_date2
		_,last_day=monthrange(current_date2.year, current_date2.month)
		month_end=datetime(current_date2.year, current_date2.month, last_day)

		if end_date<month_end:
			month_end=end_date

		date_difference = month_end - month_start
		n = date_difference.days +1

		depreciation=calculate_depreciation(doc,n,total_days,prev_closing_liability)
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

	while current_date3<=end_date:
		cnt2+=1
		if diff_annually:
			if cnt2>1:
				if current_date3!=end_date:
					current_date3=current_date3+timedelta(days=1)
		month_start, month_end,month_start2, month_end2, total_days_of_month=get_month_details(current_date3)
		if diff_annually:
			if current_date3.month==12:
				prior_month=1
				prior_date=datetime(current_date3.year+1, prior_month,current_date3.day)
			else:
				prior_month=current_date3.month+1
				prior_date=datetime(current_date3.year, prior_month,current_date3.day)
			prior_day=current_date3.day
			prior_month_end=datetime(prior_date.year, prior_date.month,prior_day)

			prior_month_start=prior_date.replace(day=1)

			diff_prior_month = prior_month_end - prior_month_start
			n_prior = diff_prior_month.days
		
		if end_date<month_end:
			month_end=end_date

		if diff_annually:
			if month_end<month_end2 and month_end==end_date:
				month_start=current_date3.replace(day=1)
			date_difference = month_end - month_start
			n_next = date_difference.days +1
			if not current_date3==start_date:
				month_start=current_date3.replace(day=1)
			n= total_days_of_month
		else:
			date_difference = month_end - month_start
			n=date_difference.days +1
			
		if current_date3==start_date or month_end==end_date:
			date_difference = month_end - month_start
			n = date_difference.days +1
			n_prior=n

		if n_prior<total_days_of_month or n<total_days_of_month:
			prev_mlp2=mlp2
			if not diff_annually:
				mlp2=mlp2*n/total_days_of_month
				if current_date3.date() in edates_pannum and escalation:
					for k in dict_ed_pannum.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pannum[k]
						if current_date3.date() in escl:
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp2=mrent
								mlp2=mlp2*n/total_days_of_month
							mlp2=mlp2+(rate*mlp2/100)+famt
							prev_mlp_escl2=mlp2
							break
				elif current_date3.date() in edates_bd and escalation:
					for k in dict_ed_bdates.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_bdates[k]
						if current_date3.date() in escl:
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp2=mrent
								mlp2=mlp2*n/total_days_of_month
							mlp2=mlp2+(rate*mlp2/100)+famt
							prev_mlp_escl2=mlp2
							break
				elif current_date3.date() in edates_pafa and escalation:
					for k in dict_ed_pafa.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pafa[k]
						if current_date3.date() in escl:
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp2=mrent
								mlp2=mlp2*n/total_days_of_month
							mlp2=mlp2+(rate*mlp2/100)+famt
							prev_mlp_escl2=mlp2
							break
				
				interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
				total_interest_cost+=interest_cost
				closing_liability=closing_liability+interest_cost-mlp2
				depreciation=calculate_depreciation(doc,n,total_days,prev_closing_liability)
				wdv-=depreciation

				data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
							round(closing_liability, 3)])
				if mrent==0 and rate==0 and famt==0:
					mlp2=prev_mlp2
				if prev_mlp_escl2 is None:
					mlp2=prev_mlp2
				else:
					mlp2=prev_mlp_escl2
			else:
				mlp2_1=mlp2*n_prior/total_days_of_month
				mlp2_2=0
				if current_date3==start_date or month_end==end_date:
					mlp2=mlp2_1
				mlp_new=mlp2
				if current_date3.date() in edates_pannum and escalation:
					for k in dict_ed_pannum.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pannum[k]
						if current_date3.date() in escl:
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp2=mrent
								mlp2=mlp2*n/total_days_of_month
							mlp2=mlp2+(rate*mlp2/100)+famt
							mlp2_2=mlp2*n_next/total_days_of_month
							mlp_new=mlp2_1+mlp2_2
							prev_mlp_escl2=mlp2
							break			
				elif current_date3.date() in edates_pafa and escalation:
					for k in dict_ed_pafa.keys():
						temp_val=k
						temp=temp_val.split('-')
						escl=dict_ed_pafa[k]
						if current_date3.date() in escl:
							rate=float(temp[0])
							mrent=float(temp[1])
							famt=float(temp[2])
							if mrent!=0:
								mlp2=mrent
								mlp2=mlp2*n/total_days_of_month
							mlp2=mlp2+(rate*mlp2/100)+famt
							mlp2_2=mlp2*n_next/total_days_of_month
							mlp_new=mlp2_1+mlp2_2
							prev_mlp_escl2=mlp2
							break
				
				mlp2=mlp_new
				interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
				total_interest_cost+=interest_cost
				closing_liability=closing_liability+interest_cost-mlp2

				depreciation=calculate_depreciation(doc,n,total_days,prev_closing_liability)
				wdv-=depreciation

				data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),
							round(closing_liability, 3)])
				if mrent==0 and rate==0 and famt==0:
					mlp2=prev_mlp2
				if prev_mlp_escl2 is None:
					mlp2=prev_mlp2
				else:
					mlp2=prev_mlp_escl2
		else:
			prev_mlp2=mlp2
			if current_date3.date() in edates_pannum and escalation:
				for k in dict_ed_pannum.keys():
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
			elif current_date3.date() in edates_bd and escalation:
				for k in dict_ed_bdates.keys():
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
			elif current_date3.date() in edates_pafa and escalation:
				for k in dict_ed_pafa.keys():
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

			interest_cost=((closing_liability-mlp2)*((1+daily_rate)**n-1))
			total_interest_cost+=interest_cost
			closing_liability=closing_liability+interest_cost-mlp2
			depreciation=calculate_depreciation(doc,n,total_days,prev_closing_liability)
			wdv-=depreciation
			
			data.append([month_start.date(),month_end.date(), n,mlp2, round(depreciation, 3), round(wdv, 3), round(interest_cost, 3),round(closing_liability, 3)])
			if mrent==0 and rate==0 and famt==0 and escalation:
				mlp2=prev_mlp2

		if month_end>end_date:
			month_end=end_date

		current_date3=date_increment(current_date3,diff_annually)

	if not data:
		frappe.msgprint("No Data Calculated")

	for i in range(len(data)):
		data[i].insert(4,pv_arr[i])

	data.append(['','',total_days,round(total_mlp,3),round(total_pv,3),round(total_depre,3),'',round(total_interest_cost,3),''])

	if data:
		return generate_excel_report(data,columns,docname,cnt_time)
	frappe.msgprint("No Data Calculated")
	return {"file_url":None}

#generate lease agreement report based on monthly rate
def generate_lease_report_month_based_new(start_date,end_date,docname,cnt_time):
	doc=frappe.get_doc("Lease Management",docname)
	mlp=mlp2=float(doc.monthly_rent)
	daily_rate=calculate_daily_rate(doc)
	current_date = current_date2 = current_date3 = start_date
	data=[]
	pv_arr=['']
	# prev_mlp_escl=None
	# prev_mlp_escl2=None
	ndays = nmonths = ndays_pv = total_mlp = total_pv = total_depre = cnt = cnt1 = cnt2 = 0
	columns=["Month Start Date","Month End Date", "Month","Minimum Lease Payment (MLP)","Present Value of MLP","Days in Month", "Depreciation on Right to Use", "Written Down Value (WDV)", "Interest Cost", "Closing Liability"]
	diff_years=get_diff_years(start_date,end_date)
	escalation,edates_pannum,edates_bd,edates_pafa,dict_ed_pannum,dict_ed_bdates,dict_ed_pafa,esc_bd_end_date,diff_annually,rate,mrent,famt=get_escalation_dates(doc,current_date,start_date,end_date,diff_years)
	
	while current_date<=end_date:
		cnt+=1
		month_start, month_end,month_start2, month_end2, total_days_of_month=get_month_details(current_date)
		if end_date<month_end:
			month_end=end_date
		date_difference = month_end - month_start
		if doc.calculation_rate_type=="Monthly Rate":
			n=cnt
			nmonths_val=date_difference.days +1
		
		if current_date.date() in edates_pannum and len(edates_pannum)>0 and escalation:
			for k in dict_ed_pannum.keys():
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
			
		elif current_date.date() in edates_bd and len(edates_bd)>0 and escalation:
			for k in dict_ed_bdates.keys():
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

		elif current_date.date() in edates_pafa and len(edates_pafa)>0 and escalation:
			for k in dict_ed_pafa.keys():
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

		current_date=date_increment(current_date,diff_annually)
	prev_closing_liability=total_pv
	total_days=ndays

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

	while current_date3<=end_date:
		cnt2+=1
		month_start, month_end,month_start2, month_end2, total_days_of_month=get_month_details(current_date3)

		if end_date<month_end:
			month_end=end_date

		date_difference = month_end - month_start
		if doc.calculation_rate_type=="Monthly Rate":
			n=cnt2
			n_days_of_month = date_difference.days +1

		if doc.calculation_rate_type=="Monthly Rate":
			if current_date3.date() in edates_pannum and len(edates_pannum)>0 and escalation:
				for k in dict_ed_pannum.keys():
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
				
			elif current_date3.date() in edates_bd and len(edates_bd)>0 and escalation:
				for k in dict_ed_bdates.keys():
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

			elif current_date3.date() in edates_pafa and len(edates_pafa)>0 and escalation:
				for k in dict_ed_pafa.keys():
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

		current_date3=date_increment(current_date3,diff_annually)
	if not data:
		frappe.msgprint("No Data Calculated")

	for i in range(len(data)):
		data[i].insert(4,pv_arr[i])

	data.append(['','',total_days,round(total_mlp,3),round(total_pv,3),nmonths,round(total_depre,3),'',round(total_interest_cost,3),''])
	if data:
		return generate_excel_report(data,columns,docname,cnt_time)
	frappe.msgprint("No Data Calculated")
	return {"file_url":None}
	

#====================================================================================
@frappe.whitelist()
def generate_report(docname,cnt):
	doc = frappe.get_doc("Lease Management",docname)
	date_format = "%Y-%m-%d"
	date_str1 = str(doc.agreement_start_date)
	date_str2 = str(doc.agreement_end_date)
	date1 = datetime.strptime(date_str1, date_format)
	date2 = datetime.strptime(date_str2, date_format)
	if doc.calculation_rate_type=="Monthly Rate":
		output = generate_lease_report_month_based_new(date1, date2,docname,cnt)
	elif doc.calculation_rate_type=="Daily Rate":
		output = generate_lease_report_new(date1, date2,docname,cnt)

	return output

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
	
	for lease in leases:
		lease_doc = frappe.get_doc("Lease Management", lease.name)
		timeline_l = lease_doc.get_lease_rent_timeline()  

		monthly_totals["Previous Month"] += timeline_l.get(previous_month, 0)
		monthly_totals["Current Month"] += timeline_l.get(current_month, 0)
		monthly_totals["Next Month"] += timeline_l.get(next_month, 0)

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

@frappe.whitelist()
def bulk_update_agreement_status():
	today = nowdate()

	updated_count =frappe.db.sql("""
		UPDATE `tabLease Management`
		SET status = 'Agreement Expired'
		WHERE agreement_end_date < %s
		AND status != 'Agreement Expired'
	""", (today,))
	frappe.db.commit()
	return {"updated":True, "count": updated_count}

@frappe.whitelist()
def has_expired_agreements():
	today = nowdate()
	count = frappe.db.count(
		"Lease Management",
        {
            "status": ["!=", "Agreement Expired"],
            "agreement_end_date": ["<", today]
        }
	)
	
	return {"needs_update": count > 0, "count": count}


@frappe.whitelist()
def delete_invoice_attachment(parent_doctype, parent_name, attachment_name, delete_file=False):
    """
    Deletes a child row Invoice Attachment (attachment_name) under parent_name.
    If delete_file=True and we can map file_docname, also delete the File doc.
    """
    # simple guards
    if not frappe.has_permission(parent_doctype, ptype='write', doc=parent_name):
        frappe.throw(_("Not permitted"))

    # delete the child row doc (Invoice Attachment)
    try:
        # grab file_docname before deleting
        file_docname = frappe.db.get_value('Invoice Attachments', attachment_name, 'file_docname')
        frappe.delete_doc('Invoice Attachments', attachment_name, force=True)
        if delete_file and file_docname:
            # ensure File exists and is safe to delete
            try:
                frappe.delete_doc('File', file_docname, force=True)
            except Exception:
                # swallow or log
                frappe.log_error(f"Could not delete File {file_docname}")
        return "ok"
    except Exception as e:
        frappe.log_error(frappe.get_traceback())
        frappe.throw(_("Could not delete attachment: {0}").format(e))

@frappe.whitelist()
def get_invoice_attachments(filters=None):
    if not filters:
        return []

    # always parse, since frappe.call sends args as strings
    filters = frappe.parse_json(filters)

    return frappe.get_all(
        "Invoice Attachments",
        filters=filters,
        fields=["name", "file", "uploaded_by", "uploaded_on"]
    )

# ===================================================================================
class LeaseManagement(Document):
	# pass
	def autoname(self):
		start_date = datetime.strptime(self.agreement_start_date, "%Y-%m-%d").date()
		end_date = datetime.strptime(self.agreement_end_date, "%Y-%m-%d").date()

		start_month = calendar.month_abbr[start_date.month].upper()
		start_year = str(start_date.year)[-2:]

		end_month = calendar.month_abbr[end_date.month].upper()
		end_year = str(end_date.year)[-2:]

		full_seq = frappe.model.naming.getseries("LMS-", 4)

		seq_num_str = full_seq.replace("LMS-", "")
		seq_num = int(seq_num_str)

		self.name = f"LMS-{start_month}{start_year}_{end_month}{end_year}-{seq_num}"

	def validate(self):
		if self.invoice_details and len(self.invoice_details)>0:
			self.validate_invoice_details()
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
		invoice_row_names = [r.custom_row_id for r in self.invoice_details]
		for a in list(self.invoice_attachments):
			if a.invoice_row not in invoice_row_names:
				# remove it
				frappe.db.delete('Invoice Attachments', a.name)

		for idx, row in enumerate(self.invoice_details, start=1):
			if row.from_date and row.to_date:
				from_str = frappe.utils.formatdate(row.from_date, "dd-MM-yyyy")
				to_str = frappe.utils.formatdate(row.to_date, "dd-MM-yyyy")
				row.custom_row_id = f"{self.name}-row-{idx}-{from_str}-to-{to_str}"

	def before_insert(self):
    	# On new record creation, populate invoice_details
		if self.agreement_start_date and self.agreement_end_date:
			# self.populate_invoice_details()
			if not self.escalation and len(self.escalation)==0:
				self.populate_escalation_record()

	def populate_escalation_record(self):
		start_date = datetime.strptime(self.agreement_start_date, "%Y-%m-%d").date()
		end_date = datetime.strptime(self.agreement_end_date, "%Y-%m-%d").date()
		# self.escalation=[]
		# if self.escalation and len(self.escalation)==0:
		self.append("escalation",{
			"escalation_type":"Per Annum",
			"start_date":start_date,
			"end_date":end_date,
			"monthly_rent":0,
			"rate":0,
			"fixed_amount":0
		})

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
			
		diff_years=get_diff_years(start_date,end_date)

		timeline={}
		current_date=start_date
		cnt=0
		prev_mlp_escl=None
		
		escalation,edates_pannum,edates_bd,edates_pafa,dict_ed_pannum,dict_ed_bdates,dict_ed_pafa,esc_bd_end_date,diff_annually,rate,mrent,famt=get_escalation_dates(doc,current_date,start_date,end_date,diff_years)

		# Calculate Previous Closing Liability from Present Value and Total Days
		while current_date<=end_date:
			cnt+=1
			if diff_annually:
				if cnt>1:
					if current_date!=end_date:
						current_date=current_date + timedelta(days=1)
			month_start, month_end,month_start2, month_end2, total_days_of_month=get_month_details(current_date)
			n_prior=get_n(current_date,diff_annually)

			if end_date<month_end:
				month_end=end_date

			if diff_annually:
				if month_end<month_end2 and month_end==end_date:
					month_end=current_date
					month_start=current_date.replace(day=1)
				date_difference = month_end - month_start
				n_next = date_difference.days +1

				n= total_days_of_month
			else:
				date_difference = month_end - month_start
				n=date_difference.days +1

			if current_date==start_date or month_end==end_date:
				date_difference = month_end - month_start
				n = date_difference.days +1
				n_prior=n

			if n_prior<total_days_of_month or n<total_days_of_month:
				prev_mlp=mlp
				if not diff_annually:
					mlp=mlp*n/total_days_of_month
					if current_date.date() in edates_pannum:
						for k in dict_ed_pannum.keys():
							temp_val=k
							temp=temp_val.split('-')
							escl=dict_ed_pannum[k]
							if current_date.date() in escl:
								rate=float(temp[0])
								mrent=float(temp[1])
								famt=float(temp[2])
								if mrent!=0:
									mlp=mrent
									mlp=mlp*n/total_days_of_month
								if mrent==0 and rate==0 and famt==0:
									mlp=0
								mlp=mlp+(rate*mlp/100)+famt
								prev_mlp_escl=mlp
								break
					elif current_date.date() in edates_bd:
						for k in dict_ed_bdates.keys():
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
								prev_mlp_escl=mlp
								break
					elif current_date.date() in edates_pafa:
						for k in dict_ed_pafa.keys():
							temp_val=k
							temp=temp_val.split('-')
							escl=dict_ed_pafa[k]
							if current_date.date() in escl:
								rate=float(temp[0])
								mrent=float(temp[1])
								famt=float(temp[2])
								if mrent!=0:
									mlp=mrent
									mlp=mlp*n/total_days_of_month
								if mrent==0 and rate==0 and famt==0:
									mlp=0
								mlp=mlp+(rate*mlp/100)+famt
								prev_mlp_escl=mlp
								break
					timeline[current_date.date().strftime("%Y-%m")] = round(mlp, 3)
					# timeline[current_date.date().strftime("%Y-%m")] = mlp
					if prev_mlp_escl is None:
						mlp=prev_mlp
					else:
						mlp=prev_mlp_escl
					if mrent==0 and rate==0 and famt==0 and escalation:
						mlp=prev_mlp
				else:
					mlp_1=mlp*n_prior/total_days_of_month
					mlp_2=0
					if current_date==start_date or month_end==end_date:
						mlp=mlp_1
					mlp_new=mlp
					if current_date.date() in edates_pannum:
						for k in dict_ed_pannum.keys():
							temp_val=k
							temp=temp_val.split('-')
							escl=dict_ed_pannum[k]
							if current_date.date() in escl:
								rate=float(temp[0])
								mrent=float(temp[1])
								famt=float(temp[2])
								if mrent!=0:
									mlp=mrent
									mlp=mlp*n/total_days_of_month
								if mrent==0 and rate==0 and famt==0:
									mlp=0
								mlp=mlp+(rate*mlp/100)+famt
								mlp_2=mlp*n_next/total_days_of_month
								mlp_new=mlp_1+mlp_2
								prev_mlp_escl=mlp
								break
					elif current_date.date() in edates_pafa:
						for k in dict_ed_pafa.keys():
							temp_val=k
							temp=temp_val.split('-')
							escl=dict_ed_pafa[k]
							if current_date.date() in escl:
								rate=float(temp[0])
								mrent=float(temp[1])
								famt=float(temp[2])
								if mrent!=0:
									mlp=mrent
									mlp=mlp*n/total_days_of_month
								if mrent==0 and rate==0 and famt==0:
									mlp=0
								mlp=mlp+(rate*mlp/100)+famt
								mlp_2=mlp*n_next/total_days_of_month
								mlp_new=mlp_1+mlp_2
								prev_mlp_escl=mlp
								
								break
					mlp=mlp_new
					timeline[current_date.date().strftime("%Y-%m")] = round(mlp_new, 3)
					# timeline[current_date.date().strftime("%Y-%m")] = mlp_new
					# mlp=prev_mlp
					if prev_mlp_escl is None:
						mlp=prev_mlp
					else:
						mlp=prev_mlp_escl
					if mrent==0 and rate==0 and famt==0 and escalation:
						mlp=prev_mlp	

			else:
				prev_mlp=mlp
				if current_date.date() in edates_pannum:
					for k in dict_ed_pannum.keys():
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
				elif current_date.date() in edates_bd:
					for k in dict_ed_bdates.keys():
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
				# timeline[current_date.date().strftime("%Y-%m")] = mlp
				if mrent==0 and rate==0 and famt==0 and escalation:
					mlp=prev_mlp
			if month_end>end_date:
				month_end=end_date

			current_date=date_increment(current_date,diff_annually)
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
		diff_years=get_diff_years(start_date,end_date)
		monthly_data={}
		current_date=start_date
		cnt=0
		prev_mlp_escl=None
		escalation,edates_pannum,edates_bd,edates_pafa,dict_ed_pannum,dict_ed_bdates,dict_ed_pafa,esc_bd_end_date,diff_annually,rate,mrent,famt=get_escalation_dates(doc,current_date,start_date,end_date,diff_years)

		# Calculate Previous Closing Liability from Present Value and Total Days
		while current_date<=end_date:
			cnt+=1
			if diff_annually:
				if cnt>1:
					if current_date!=end_date:
						current_date=current_date+timedelta(days=1)
			month_start, month_end,month_start2, month_end2, total_days_of_month=get_month_details(current_date)
			n_prior=get_n(current_date,diff_annually)

			if end_date<month_end:
				month_end=end_date

			if diff_annually:
				if month_end<month_end2 and month_end==end_date:
					month_end=current_date
					month_start=current_date.replace(day=1)
				date_difference = month_end - month_start
				# n_next = date_difference.days +1

				n= total_days_of_month
			else:
				date_difference = month_end - month_start
				n=date_difference.days +1

			if current_date==start_date or month_end==end_date:
				date_difference = month_end - month_start
				n = date_difference.days +1
				n_prior=n

			if n_prior<total_days_of_month or n<total_days_of_month:
				prev_mlp=mlp
				if not diff_annually:
					mlp=mlp*n/total_days_of_month
					if current_date.date() in edates_pannum and escalation:
						for k in dict_ed_pannum.keys():
							temp_val=k
							temp=temp_val.split('-')
							escl=dict_ed_pannum[k]
							if current_date.date() in escl:
								rate=float(temp[0])
								mrent=float(temp[1])
								famt=float(temp[2])
								if mrent!=0:
									mlp=mrent
									mlp=mlp*n/total_days_of_month
								if mrent==0 and rate==0 and famt==0:
									mlp=0
								mlp=mlp+(rate*mlp/100)+famt
								prev_mlp_escl=mlp
								break
					elif current_date.date() in edates_bd and escalation:
						for k in dict_ed_bdates.keys():
							temp_val=k
							temp=temp_val.split('-')
							escl=dict_ed_bdates[k]
							if current_date.date() in escl:
								rate=float(temp[0])
								mrent=float(temp[1])
								famt=float(temp[2])
								if mrent!=0:
									mlp=mrent
									mlp=mlp*n/total_days_of_month
								if mrent==0 and rate==0 and famt==0:
									mlp=0
								mlp=mlp+(rate*mlp/100)+famt
								prev_mlp_escl=mlp
								break
					elif current_date.date() in edates_pafa and escalation:
						for k in dict_ed_pafa.keys():
							temp_val=k
							temp=temp_val.split('-')
							escl=dict_ed_pafa[k]
							if current_date.date() in escl:
								rate=float(temp[0])
								mrent=float(temp[1])
								famt=float(temp[2])
								if mrent!=0:
									mlp=mrent
									mlp=mlp*n/total_days_of_month
								if mrent==0 and rate==0 and famt==0:
									mlp=0
								mlp=mlp+(rate*mlp/100)+famt
								prev_mlp_escl=mlp
								break
					
					if current_date==start_date:
						month_start=current_date
						if month_end>end_date:
							month_end=end_date
					else:
						month_start=current_date.replace(day=1)
					val=[month_start.date(),month_end.date()]
					monthly_data[current_date.date().strftime("%Y-%m")] = val
					if prev_mlp_escl is None:
						mlp=prev_mlp
					else:
						mlp=prev_mlp_escl
					if mrent==0 and rate==0 and famt==0 and escalation:
						mlp=prev_mlp
				else:
					mlp_1=mlp*n_prior/total_days_of_month
					# mlp_2=0
					if current_date==start_date or month_end==end_date:
						mlp=mlp_1
					# mlp_new=mlp
					if current_date.date() in edates_pannum and escalation:
						for k in dict_ed_pannum.keys():
							temp_val=k
							temp=temp_val.split('-')
							escl=dict_ed_pannum[k]
							if current_date.date() in escl:
								rate=float(temp[0])
								mrent=float(temp[1])
								famt=float(temp[2])
								if mrent!=0:
									mlp=mrent
									mlp=mlp*n/total_days_of_month
								if mrent==0 and rate==0 and famt==0:
									mlp=0
								mlp=mlp+(rate*mlp/100)+famt
								# mlp_2=mlp*n_next/total_days_of_month
								# mlp_new=mlp_1+mlp_2
								prev_mlp_escl=mlp
								break
					
					elif current_date.date() in edates_pafa and escalation:
						for k in dict_ed_pafa.keys():
							temp_val=k
							temp=temp_val.split('-')
							escl=dict_ed_pafa[k]
							if current_date.date() in escl:
								rate=float(temp[0])
								mrent=float(temp[1])
								famt=float(temp[2])
								if mrent!=0:
									mlp=mrent
									mlp=mlp*n/total_days_of_month
								if mrent==0 and rate==0 and famt==0:
									mlp=0
								mlp=mlp+(rate*mlp/100)+famt
								# mlp_2=mlp*n_next/total_days_of_month
								# mlp_new=mlp_1+mlp_2
								prev_mlp_escl=mlp
								break
					if current_date==start_date:
						month_start=current_date
						if month_end>end_date:
							month_end=end_date
					else:
						month_start=current_date.replace(day=1)
					val=[month_start.date(),month_end.date()]
					monthly_data[current_date.date().strftime("%Y-%m")] = val
					if prev_mlp_escl is None:
						mlp=prev_mlp
					else:
						mlp=prev_mlp_escl
					if mrent==0 and rate==0 and famt==0 and escalation:
						mlp=prev_mlp

			else:
				prev_mlp=mlp
				
				if current_date.date() in edates_pannum and escalation:
					for k in dict_ed_pannum.keys():
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
				elif current_date.date() in edates_bd and escalation:
					for k in dict_ed_bdates.keys():
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
				elif current_date.date() in edates_pafa and escalation:
					for k in dict_ed_pafa.keys():
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
				
				if current_date==start_date:
					month_start=current_date
					if month_end>end_date:
						month_end=end_date
				else:
					month_start=current_date.replace(day=1)
				val=[month_start.date(),month_end.date()]
				monthly_data[current_date.date().strftime("%Y-%m")] = val
				if mrent==0 and rate==0 and famt==0 and escalation:
					mlp=prev_mlp
			if month_end>end_date:
				month_end=end_date

			current_date=date_increment(current_date,diff_annually)
		return monthly_data

	def validate_invoice_details(self):
		rent_timeline=self.get_lease_rent_timeline()
		# monthly_data=self.get_lease_monthly_data()
		for row in self.invoice_details:
			from_date = datetime.strptime(row.from_date, "%Y-%m-%d")
			to_date = datetime.strptime(row.to_date, "%Y-%m-%d")
			date_ranges=[]
			exp_rent=[]
			current=from_date
			while current<=to_date:
				start_date=current
				_,last_day=monthrange(current.year, current.month)
				end_date=datetime(current.year, current.month, last_day)

				if end_date>to_date:
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
			# frappe.msgprint(str(expected_rent))
			# inv_month=from_date.strftime("%Y-%m")
			# expected_rent=rent_timeline.get(inv_month)

			if expected_rent is None:
				row.is_mismatch=1
				continue

			actual_amount=float(row.amount)
			tax=float(row.tax)
			if int(row.with_tax)==1:
				calc_amount=expected_rent+((tax*expected_rent)/100)
				if round(calc_amount,3) != round(actual_amount,3):
					row.is_mismatch=1
				else:
					row.is_mismatch=0

			else:
				if round(actual_amount,3) != round(expected_rent,3):
					row.is_mismatch=1
					# frappe.msgprint("row is_mismatch at row no. "+str(row.idx)+" "+str(round(expected_rent,3))+" /"+str(row.amount))
				else:
					row.is_mismatch=0
			
def get_permission_query_conditions(user):
	if not user:
		return ""
	
	roles=frappe.get_roles(user)
	if "System Manager" in roles or "Accounts" in roles:
		return ""
	
	if "Vendor" in roles:
		vendor=frappe.db.get_value("Vendor Master",{"email_address":user},"name")

		if not vendor:
			return "1=0"
		
		return f"`tabLease Management`.`vendor`='{vendor}'"
	
	return ""

def has_permission(doc,user):
	roles=frappe.get_roles(user)
	if "System Manager" in roles or "Accounts" in roles:
		return True
	
	if "Vendor" in roles:
		vendor=frappe.db.get_value("Vendor Master",{"email_address":user},"name")
		return doc.vendor==vendor
	
	return False	

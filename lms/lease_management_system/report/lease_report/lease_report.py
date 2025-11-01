# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data
import calendar
from calendar import monthrange
from collections import Counter
from datetime import date, datetime, timedelta

import frappe
from dateutil.relativedelta import relativedelta
from frappe import _ as translate


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

	if isinstance(start_date, date) and not isinstance(start_date, datetime):
		start_date = datetime.combine(start_date, datetime.min.time())
	if isinstance(end_date, date) and not isinstance(end_date, datetime):
		end_date = datetime.combine(end_date, datetime.min.time())

	mlp = float(doc.monthly_rent)
	mlp2 = float(doc.monthly_rent)

	disc_doc = float(doc.discounting_rate) / 100
	if doc.calculation_rate_type == "Daily Rate":
		daily_rate = (1 + disc_doc) ** (1 / 365) - 1

	arg_sd = start_date
	arg_ed = end_date + timedelta(days=1)
	diff_years = relativedelta(arg_ed, arg_sd)
	diff_years = int(str(diff_years.years))

	columns = [
		{"label": "Month Start Date", "fieldname": "month_start_date", "fieldtype": "Date", "width": 120},
		{"label": "Month End Date", "fieldname": "month_end_date", "fieldtype": "Date", "width": 120},
		{"label": "Days in Month", "fieldname": "days_in_month", "fieldtype": "Int", "width": 120},
		{
			"label": translate("Minimum Lease Payment (MLP)"),
			"fieldname": "mlp",
			"fieldtype": "Currency",
			"width": 180,
			"precision": 4,
		},
		{"label": "Present Value of MLP", "fieldname": "pv", "fieldtype": "Currency", "width": 180},
		{
			"label": translate("Depreciation on Right to Use"),
			"fieldname": "depreciation",
			"fieldtype": "Currency",
			"width": 200,
		},
		{"label": "Written Down Value (WDV)", "fieldname": "wdv", "fieldtype": "Currency", "width": 180},
		{"label": "Interest Cost", "fieldname": "interest_cost", "fieldtype": "Currency", "width": 150},
		{
			"label": translate("Closing Liability"),
			"fieldname": "closing_liability",
			"fieldtype": "Currency",
			"width": 180,
		},
	]

	current_date = start_date
	ndays = 0
	# nmonths = 0
	# ndays_pv = 0
	total_mlp = 0
	total_pv = 0
	total_depre = 0
	pv_arr = [""]
	cnt = 0
	data = []
	etype = []
	escl_dates_pafr = []
	escl_dates_bdates = []
	total_escl_dates_bdates = []
	escl_dates_pannum = []
	date_list = []
	calc_dict = {}
	calc_keys = []
	bd_start_date = ""
	bd_end_date = ""
	cnt_etype = 0
	new_start_date = []

	escalation = True
	diff_annually = False
	prev_mlp_escl = None
	prev_mlp_escl2 = None

	for child in doc.escalation:
		escl_type = child.escalation_type

		if escl_type:
			etype.append(escl_type)
			if "Based On Dates" == escl_type:
				if child.monthly_rent is None:
					monthly_rent_bdates = 0
				else:
					monthly_rent_bdates = float(child.monthly_rent)
				if child.rate is None:
					rate_bdates = 0
				else:
					rate_bdates = float(child.rate)
				if child.fixed_amount is None:
					fixed_amt_bdates = 0
				else:
					fixed_amt_bdates = float(child.fixed_amount)
				bd_start_date = child.start_date
				bd_end_date = child.end_date
				# escl_dates_bdates=[]
				new_date = current_date
				new_date = new_date.date()
				while new_date <= bd_end_date:
					if new_date >= bd_start_date and new_date <= bd_end_date:
						escl_dates_bdates.append(new_date)
						new_date = new_date + timedelta(days=1)
					else:
						new_date = new_date + timedelta(days=1)

				if new_date > bd_end_date:
					new_start_date.append(new_date)
				dkey = "Based On Dates" + "-" + str(monthly_rent_bdates)
				# dsubkey=str(monthly_rent_bdates)+'-'+str(rate_bdates)+'-'+str(fixed_amt_bdates)
				dsubkey = str(rate_bdates) + "-" + str(monthly_rent_bdates) + "-" + str(fixed_amt_bdates)

				calc_dict[dkey] = {dsubkey: escl_dates_bdates}
				# calc_dict.setdefault(dkey, {}).setdefault(monthly_rent_bdates, []).extend(escl_dates_bdates)
				total_escl_dates_bdates += escl_dates_bdates
				if len(new_start_date) > 0:
					l = len(new_start_date)
					for q in range(l):
						if new_start_date[q] in total_escl_dates_bdates:
							new_start_date.remove(new_start_date[q])
							break
				escl_dates_bdates = []
	else:
		if not doc.escalation:
			escalation = False
	# if escalation:
	esc_bd_end_date = None
	if escalation:
		for i in range(len(etype)):
			if etype[i] == "Per Annum" or etype[i] == "Per Annum and Fixed Amount":
				if etype[i - 1] == "Based On Dates":
					bd_date = doc.escalation[i - 1]
					d = bd_date.end_date
					esc_bd_end_date = d + timedelta(days=1)
		if len(total_escl_dates_bdates) > 0:
			date_list = total_escl_dates_bdates

		for child in doc.escalation:
			if child.monthly_rent is None:
				monthly_rent = 0
			else:
				monthly_rent = float(child.monthly_rent)
			if child.rate is None:
				rate = 0
			else:
				rate = float(child.rate)
			if child.fixed_amount is None:
				fixed_amt = 0
			else:
				fixed_amt = float(child.fixed_amount)

			if child.escalation_type == "Per Annum":
				cnt_etype += 1
				for i in range(diff_years):
					if i == 0 and cnt_etype == 1:
						if esc_bd_end_date is None:
							new_date = start_date + relativedelta(years=1)
						else:
							new_date = esc_bd_end_date
						if new_date not in date_list:
							if isinstance(new_date, datetime):
								new_date = new_date.date()
							escl_dates_pannum.append(new_date)

							new_date = new_date + relativedelta(years=1)
							continue
					else:
						if new_date in date_list:
							new_date = new_date + relativedelta(years=1)
							break
						if isinstance(new_date, datetime):
							new_date = new_date.date()

						if new_date < end_date.date() and new_date not in date_list:
							escl_dates_pannum.append(new_date)
							new_date = new_date + relativedelta(years=1)
				dkey = "Per Annum" + "-" + str(rate)
				dsubkey = str(rate) + "-" + str(monthly_rent) + "-" + str(fixed_amt)
				calc_dict[dkey] = {dsubkey: escl_dates_pannum}
				escl_dates_pannum = []

			elif child.escalation_type == "Per Annum and Fixed Amount":
				cnt_etype += 1
				for i in range(diff_years):
					if i == 0 and cnt_etype == 1:
						if esc_bd_end_date is None:
							new_date = start_date + relativedelta(years=1)
						else:
							new_date = esc_bd_end_date

						if new_date not in date_list:
							if isinstance(new_date, datetime):
								new_date = new_date.date()
							escl_dates_pafr.append(new_date)
							new_date = new_date + relativedelta(years=1)
					else:
						if new_date in date_list:
							new_date = new_date + relativedelta(years=1)
							break
						if isinstance(new_date, datetime):
							new_date = new_date.date()
						if new_date < end_date.date() and new_date not in date_list:
							escl_dates_pafr.append(new_date)
							new_date = new_date + relativedelta(years=1)
				dkey = "Per Annum and Fixed Amount" + "-" + str(rate) + "-" + str(fixed_amt)
				dsubkey = str(rate) + "-" + str(monthly_rent) + "-" + str(fixed_amt)
				calc_dict[dkey] = {dsubkey: escl_dates_pafr}
				escl_dates_pafr = []

			# if child.escalation_type=="Per Annum":
			# 	cnt_etype+=1

			# 	for i in range(diff_years):
			# 		if i==0 and cnt_etype==1:
			# 			for j in range(len(new_start_date)):
			# 				if new_date>=new_start_date[j]:
			# 					new_date=new_start_date[j]
			# 				elif new_date<new_start_date[j]:
			# 					new_date = start_date + relativedelta(years=1)
			# 			if len(new_start_date)==0:
			# 				new_date = start_date + relativedelta(years=1)
			# 			if new_date not in date_list:
			# 				if isinstance(new_date, datetime):
			# 					new_date = new_date.date()
			# 				escl_dates_pannum.append(new_date)
			# 				new_date=new_date + relativedelta(years=1)
			# 		else:
			# 			if new_date in date_list:
			# 				new_date=new_date + relativedelta(years=1)
			# 				break
			# 			if isinstance(new_date, datetime):
			# 				new_date = new_date.date()
			# 			if new_date<end_date.date() and new_date not in date_list:
			# 				escl_dates_pannum.append(new_date)
			# 				new_date=new_date + relativedelta(years=1)
			# 	dkey="Per Annum"+'-'+str(rate)
			# 	dsubkey=str(rate)+'-'+str(monthly_rent)+'-'+str(fixed_amt)
			# 	calc_dict[dkey]={dsubkey:escl_dates_pannum}
			# 	escl_dates_pannum=[]

			# elif child.escalation_type=="Per Annum and Fixed Amount":
			# 	cnt_etype+=1

			# 	for i in range(diff_years):
			# 		if i==0 and cnt_etype==1:
			# 			for j in range(len(new_start_date)):
			# 				if new_date>=new_start_date[j]:
			# 					new_date=new_start_date[j]
			# 				elif new_date<new_start_date[j]:
			# 					new_date = start_date + relativedelta(years=1)
			# 			if len(new_start_date)==0:
			# 				new_date = start_date + relativedelta(years=1)

			# 			if new_date not in date_list:
			# 				if isinstance(new_date, datetime):
			# 					new_date = new_date.date()
			# 				escl_dates_pafr.append(new_date)
			# 				new_date=new_date + relativedelta(years=1)
			# 		else:
			# 			if new_date in date_list:
			# 				new_date=new_date + relativedelta(years=1)
			# 				break
			# 			if isinstance(new_date, datetime):
			# 				new_date = new_date.date()
			# 			if new_date<end_date.date() and new_date not in date_list:
			# 				escl_dates_pafr.append(new_date)
			# 				new_date=new_date + relativedelta(years=1)
			# 	dkey="Per Annum and Fixed Amount"+'-'+str(rate)+'-'+str(fixed_amt)
			# 	dsubkey=str(rate)+'-'+str(monthly_rent)+'-'+str(fixed_amt)
			# 	calc_dict[dkey]={dsubkey:escl_dates_pafr}
			# 	escl_dates_pafr=[]

		for key in calc_dict:
			calc_keys.append(key)

	per_annum_rows = [child for child in doc.escalation if child.escalation_type == "Per Annum"]
	if len(per_annum_rows) == 1:
		row = per_annum_rows[0]
		rate_val = float(row.rate) if row.rate is not None else 0
		rent_val = float(row.monthly_rent) if row.monthly_rent is not None else 0
		fixed_amt_val = float(row.fixed_amount) if row.fixed_amount is not None else 0

		if rate_val == 0 and rent_val == 0 and fixed_amt_val == 0:
			escalation = False
	edates_pannum = []
	edates_bd = []
	edates_pafa = []
	# pa_rate=0
	# pafa_rate=0
	famt = 0
	mrent = 0
	rate = 0
	dict_ed_pannum = {}
	dict_ed_pafa = {}
	dict_ed_bdates = {}

	if escalation:
		for i in range(len(calc_keys)):
			temp_str = calc_keys[i]
			temp = calc_keys[i].split("-")
			calc_escl_type = temp[0]

			if calc_escl_type == "Per Annum":
				sub_dict = calc_dict[temp_str]
				subkey = next(iter(sub_dict))

				edates_pannum += sub_dict[subkey]
				dict_ed_pannum[subkey] = sub_dict[subkey]

			elif calc_escl_type == "Based On Dates":
				sub_dict = calc_dict[temp_str]
				subkey = next(iter(sub_dict))

				edates_bd += sub_dict[subkey]
				dict_ed_bdates[subkey] = sub_dict[subkey]

			elif calc_escl_type == "Per Annum and Fixed Amount":
				sub_dict = calc_dict[temp_str]

				subkey = next(iter(sub_dict))

				edates_pafa += sub_dict[subkey]
				dict_ed_pafa[subkey] = sub_dict[subkey]
	if (len(etype) == 1 and etype[0] == "Per Annum") or (
		len(etype) == 1 and etype[0] == "Per Annum and Fixed Amount"
	):
		month_start = current_date

		_, last_day = monthrange(current_date.year, current_date.month)
		month_end = datetime(current_date.year, current_date.month, last_day)

		month_start2 = current_date.replace(day=1)
		_, last_day2 = monthrange(current_date.year, current_date.month)
		month_end2 = datetime(current_date.year, current_date.month, last_day2)
		date_difference2 = month_end2 - month_start2
		total_days_of_month = date_difference2.days + 1

		date_difference = month_end - month_start
		n = date_difference.days + 1

		if n < total_days_of_month:
			diff_annually = True
	if len(edates_pannum) > 0:
		if edates_pannum[0] != edates_pannum[0].replace(day=1) and current_date != current_date.replace(
			day=1
		):
			diff_annually = True
	if len(edates_pafa) > 0:
		if edates_pafa[0] != edates_pafa[0].replace(day=1) and current_date != current_date.replace(day=1):
			diff_annually = True

	cnt_keys = len(dict_ed_bdates)
	dict_new = {}
	common_month = []
	common_dict = {}
	if dict_ed_bdates is not None and escalation and cnt_keys > 1:
		for key in dict_ed_bdates.keys():
			temp_val = key
			temp = temp_val.split("-")
			escl = dict_ed_bdates[key]
			escl_months = []
			escl_months = [f"{d.year}-{d.month:02d}" for d in escl]
			month_count = dict(Counter(escl_months))
			month_count = dict(sorted(month_count.items()))
			dict_new[key] = month_count
		keys = list(dict_new.keys())
		if len(keys) > 1:
			for i in range(len(keys) - 1):
				k1, k2 = keys[i], keys[i + 1]
				month_1 = set(dict_new[k1].keys())
				month_2 = set(dict_new[k2].keys())
				common = sorted(month_1.intersection(month_2))
				common_month.extend(common)
			if len(common_month) > 0:
				for i in range(len(common_month)):
					total_mlp_escl = 0
					for k in range(len(keys)):
						key_n = keys[k]
						date_dict = dict_new[key_n]
						if common_month[i] in date_dict.keys():
							temp = key_n.split("-")
							cmonth = common_month[i]
							year, month = map(int, cmonth.split("-"))
							total_days_of_month = calendar.monthrange(year, month)[1]
							n = date_dict[common_month[i]]
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp_escl = mrent
								mlp_escl = mlp_escl * n / total_days_of_month
							if mrent == 0 and rate == 0 and famt == 0:
								mlp_escl = 0
							mlp_escl = mlp_escl + (rate * mlp_escl / 100) + famt
							total_mlp_escl += mlp_escl
					common_dict[cmonth] = total_mlp_escl

	if esc_bd_end_date is not None:
		if esc_bd_end_date != esc_bd_end_date.replace(day=1):
			mid_diff_annually = True
		else:
			mid_diff_annually = False
	else:
		mid_diff_annually = False
	# First loop PV calculations
	while current_date <= end_date:
		cnt += 1
		if diff_annually:
			if cnt > 1:
				if current_date != end_date:
					current_date = current_date + timedelta(days=1)
		month_start = current_date
		_, last_day = monthrange(current_date.year, current_date.month)
		month_end = datetime(current_date.year, current_date.month, last_day)
		month_start2 = current_date.replace(day=1)
		_, last_day2 = monthrange(current_date.year, current_date.month)
		month_end2 = datetime(current_date.year, current_date.month, last_day2)
		date_difference2 = month_end2 - month_start2
		total_days_of_month = date_difference2.days + 1

		if diff_annually:
			if current_date.month == 12:
				prior_month = 1
				prior_date = datetime(current_date.year + 1, prior_month, current_date.day)
			else:
				prior_month = current_date.month + 1
				prior_date = datetime(current_date.year, prior_month, current_date.day)
			prior_day = current_date.day
			prior_month_end = datetime(prior_date.year, prior_date.month, prior_day)

			prior_month_start = prior_date.replace(day=1)
			diff_prior_month = prior_month_end - prior_month_start
			n_prior = diff_prior_month.days

		if end_date < month_end:
			month_end = end_date

		if diff_annually and not mid_diff_annually:
			if month_end < month_end2 and month_end == end_date:
				month_end = current_date
				month_start = current_date.replace(day=1)
			date_difference = month_end - month_start
			n_next = date_difference.days + 1
			n = total_days_of_month
		elif mid_diff_annually:
			if month_end < month_end2 and month_end != end_date:
				month_end = current_date
				month_start = current_date.replace(day=1)
			if month_end == end_date:
				month_end = end_date
				month_start = current_date.replace(day=1)
			date_difference = month_end - month_start
			n_next = date_difference.days + 1
			n = total_days_of_month
		else:
			date_difference = month_end - month_start
			n = date_difference.days + 1
			n_next = 0
		if current_date.strftime("%Y-%m") == end_date.strftime("%Y-%m"):
			month_end = end_date
		if current_date == start_date or month_end == end_date:
			date_difference = month_end - month_start
			n = date_difference.days + 1
			n_prior = n

		if n_prior < total_days_of_month or n < total_days_of_month:
			prev_mlp = mlp
			if not diff_annually:
				mlp = mlp * n / total_days_of_month
				if current_date.date() in edates_pannum:
					for k in dict_ed_pannum.keys():
						temp_val = k
						temp = temp_val.split("-")
						escl = dict_ed_pannum[k]
						if current_date.date() in escl:
							# pa_rate=rate_pa
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp = mrent
								mlp = mlp * n / total_days_of_month
							if mrent == 0 and rate == 0 and famt == 0:
								mlp = 0
							mlp = mlp + (rate * mlp / 100) + famt
							prev_mlp_escl = mlp
							break
					# mlp=mlp+(pa_rate*mlp/100)
				elif current_date.date() in edates_bd:
					for k in dict_ed_bdates.keys():
						# rpm=float(k)
						temp_val = k
						temp = temp_val.split("-")
						escl = dict_ed_bdates[k]
						current_month_str = current_date.strftime("%Y-%m")
						if len(common_month) > 0:
							mlp_common_dict = common_dict.get(current_month_str)
							if mlp_common_dict is not None:
								mlp = mlp_common_dict
								prev_mlp_escl = mlp
								break
						if current_date.date() in escl:
							# mrent=rpm
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp = mrent
								mlp = mlp * n / total_days_of_month
							if mrent == 0 and rate == 0 and famt == 0:
								mlp = 0
							mlp = mlp + (rate * mlp / 100) + famt
							prev_mlp_escl = mlp
							break
					# mlp=mrent
				elif current_date.date() in edates_pafa:
					for k in dict_ed_pafa.keys():
						temp_val = k
						temp = temp_val.split("-")
						# rate_pa=temp[0]
						# f=temp[1]
						escl = dict_ed_pafa[k]
						if current_date.date() in escl:
							# pafa_rate=float(rate_pa)
							# famt=float(f)
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp = mrent
								mlp = mlp * n / total_days_of_month
							if mrent == 0 and rate == 0 and famt == 0:
								mlp = 0
							mlp = mlp + (rate * mlp / 100) + famt
							prev_mlp_escl = mlp
							break
					# mlp=mlp+(pafa_rate*mlp/100)+famt

				total_mlp += mlp
				if cnt == 1:
					pv = mlp
					pv_arr.append(pv)
				else:
					pv = mlp / ((1 + daily_rate) ** ndays)
					pv_arr.append(pv)
				if prev_mlp_escl is None:
					mlp = prev_mlp
				else:
					mlp = prev_mlp_escl
				if mrent == 0 and rate == 0 and famt == 0 and escalation:
					mlp = prev_mlp
			else:
				mlp_1 = mlp * n_prior / total_days_of_month
				mlp_2 = 0
				if current_date == start_date or month_end == end_date:
					mlp = mlp_1
				mlp_new = mlp
				if current_date.date() == start_date.date() and escalation and edates_pafa is not None:
					for k in dict_ed_pafa.keys():
						temp_val = k
						temp = temp_val.split("-")
						famt = float(temp[2])
						new_famt = famt * n_prior / total_days_of_month
						mlp_new = mlp_new + new_famt
						prev_mlp_escl = prev_mlp + famt
						break
				if current_date.date() in edates_pannum and escalation:
					for k in dict_ed_pannum.keys():
						temp_val = k
						temp = temp_val.split("-")
						escl = dict_ed_pannum[k]
						if current_date.date() in escl:
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp = mrent
								mlp = mlp * n / total_days_of_month
							if mrent == 0 and rate == 0 and famt == 0:
								mlp = 0
							mlp = mlp + (rate * mlp / 100) + famt
							mlp_2 = mlp * n_next / total_days_of_month
							mlp_new = mlp_1 + mlp_2
							prev_mlp_escl = mlp
							break
				elif current_date.date() in edates_bd and escalation:
					for k in dict_ed_bdates.keys():
						temp_val = k
						temp = temp_val.split("-")
						escl = dict_ed_bdates[k]
						if current_date.date() in escl:
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp = mrent
								mlp = mlp * n / total_days_of_month
							if mrent == 0 and rate == 0 and famt == 0:
								mlp = 0
							mlp = mlp + (rate * mlp / 100) + famt
							mlp_new = mlp
							prev_mlp_escl = mlp
							break
				elif current_date.date() in edates_pafa and escalation:
					for k in dict_ed_pafa.keys():
						temp_val = k
						temp = temp_val.split("-")
						escl = dict_ed_pafa[k]
						if current_date.date() in escl:
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp = mrent
								mlp = mlp * n / total_days_of_month
							if mrent == 0 and rate == 0 and famt == 0:
								mlp = 0
							mlp = mlp + (rate * mlp / 100) + famt
							mlp_2 = mlp * n_next / total_days_of_month
							mlp_new = mlp_1 + mlp_2
							prev_mlp_escl = mlp
							break

				mlp = mlp_new
				total_mlp += mlp
				if cnt == 1:
					pv = mlp
					pv_arr.append(pv)
				else:
					pv = mlp / ((1 + daily_rate) ** ndays)
					pv_arr.append(pv)
				if prev_mlp_escl is None:
					mlp = prev_mlp
				else:
					mlp = prev_mlp_escl
				if mrent == 0 and rate == 0 and famt == 0 and escalation:
					mlp = prev_mlp
		else:
			if current_date.date() == start_date.date() and escalation and edates_pafa is not None:
				for k in dict_ed_pafa.keys():
					temp_val = k
					temp = temp_val.split("-")
					famt = float(temp[2])
					mlp = mlp + famt
					break
			if current_date.date() in edates_pannum:
				for k in dict_ed_pannum.keys():
					temp_val = k
					temp = temp_val.split("-")
					escl = dict_ed_pannum[k]
					if current_date.date() in escl:
						# pa_rate=rate_pa
						rate = float(temp[0])
						mrent = float(temp[1])
						famt = float(temp[2])
						if mrent != 0:
							mlp = mrent
						mlp = mlp + (rate * mlp / 100) + famt
						break
				# mlp=mlp+(pa_rate*mlp/100)
			elif current_date.date() in edates_bd:
				for k in dict_ed_bdates.keys():
					# rpm=float(k)
					temp_val = k
					temp = temp_val.split("-")
					escl = dict_ed_bdates[k]
					current_month_str = current_date.strftime("%Y-%m")
					if len(common_month) > 0:
						mlp_common_dict = common_dict.get(current_month_str)
						if mlp_common_dict is not None:
							mlp = mlp_common_dict
							prev_mlp_escl = mlp
							break
					if current_date.date() in escl:
						# mrent=rpm
						rate = float(temp[0])
						mrent = float(temp[1])
						famt = float(temp[2])
						if mrent != 0:
							mlp = mrent
						if mrent == 0 and rate == 0 and famt == 0:
							mlp = 0
						mlp = mlp + (rate * mlp / 100) + famt
						break
				# mlp=mrent
			elif current_date.date() in edates_pafa:
				for k in dict_ed_pafa.keys():
					temp_val = k
					temp = temp_val.split("-")
					# rate_pa=temp[0]
					# f=temp[1]
					escl = dict_ed_pafa[k]
					if current_date.date() in escl:
						# pafa_rate=float(rate_pa)
						# famt=float(f)
						rate = float(temp[0])
						mrent = float(temp[1])
						famt = float(temp[2])
						if mrent != 0:
							mlp = mrent
						mlp = mlp + (rate * mlp / 100) + famt
						break
				# mlp=mlp+(pafa_rate*mlp/100)+famt

			total_mlp += mlp
			if cnt == 1:
				pv = mlp
				pv_arr.append(pv)
			else:
				pv = mlp / ((1 + daily_rate) ** ndays)
				pv_arr.append(pv)

		total_pv += pv
		ndays += n
		if esc_bd_end_date is not None:
			if esc_bd_end_date != esc_bd_end_date.replace(day=1):
				if current_date.month == 12:
					next_current_date = datetime(current_date.year + 1, 1, 1)
				else:
					next_current_date = datetime(current_date.year, current_date.month + 1, 1)
				if next_current_date.strftime("%Y-%m") == esc_bd_end_date.strftime("%Y-%m"):
					diff_annually = True
		# Move to next month
		if current_date.month == 12:
			if diff_annually and not mid_diff_annually:
				current_date = datetime(current_date.year + 1, 1, current_date.day) - relativedelta(days=1)
			elif diff_annually and mid_diff_annually:
				current_date = datetime(current_date.year + 1, 1, esc_bd_end_date.day) - relativedelta(days=1)
			else:
				current_date = datetime(current_date.year + 1, 1, 1)
		else:
			if diff_annually and not mid_diff_annually:
				current_date = datetime(
					current_date.year, current_date.month + 1, current_date.day
				) - relativedelta(days=1)
			elif diff_annually and mid_diff_annually:
				current_date = datetime(
					current_date.year, current_date.month + 1, esc_bd_end_date.day
				) - relativedelta(days=1)
			else:
				current_date = datetime(current_date.year, current_date.month + 1, 1)
		if current_date.strftime("%Y-%m") == end_date.strftime("%Y-%m"):
			current_date = current_date.replace(day=1)
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
		n = date_difference.days + 1

		if (doc.previous_wdv) != 0:
			prev_closing_liability_wdv = float(doc.previous_wdv)
			depreciation = (n / total_days) * prev_closing_liability_wdv
			total_depre += depreciation
		else:
			depreciation = (n / total_days) * prev_closing_liability
			total_depre += depreciation

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
	data.append(
		{
			"month_start_date": "",
			"month_end_date": "",
			"days_in_month": "",
			"mlp": "",
			"pv": "",
			"depreciation": "",
			"wdv": round(wdv, 3),
			"interest_cost": "",
			"closing_liability": round(closing_liability, 3),
		}
	)

	# Third loop final report generation
	current_date3 = start_date
	cnt2 = 0
	while current_date3 <= end_date:
		cnt2 += 1
		if diff_annually:
			if cnt2 > 1:
				if current_date3 != end_date:
					current_date3 = current_date3 + timedelta(days=1)
		month_start = current_date3
		_, last_day = monthrange(current_date3.year, current_date3.month)
		month_end = datetime(current_date3.year, current_date3.month, last_day)

		if diff_annually:
			if current_date3.month == 12:
				prior_month = 1
				prior_date = datetime(current_date3.year + 1, prior_month, current_date3.day)
			else:
				prior_month = current_date3.month + 1
				prior_date = datetime(current_date3.year, prior_month, current_date3.day)
			prior_day = current_date3.day
			prior_month_end = datetime(prior_date.year, prior_date.month, prior_day)

			prior_month_start = prior_date.replace(day=1)

			diff_prior_month = prior_month_end - prior_month_start
			n_prior = diff_prior_month.days

		if end_date < month_end:
			month_end = end_date

		month_start2 = current_date3.replace(day=1)
		_, last_day2 = monthrange(current_date3.year, current_date3.month)
		month_end2 = datetime(current_date3.year, current_date3.month, last_day2)
		date_difference2 = month_end2 - month_start2
		total_days_of_month = date_difference2.days + 1

		if diff_annually:
			if month_end < month_end2 and month_end == end_date:
				month_start = current_date3.replace(day=1)
			date_difference = month_end - month_start
			n_next = date_difference.days + 1
			if not current_date3 == start_date:
				month_start = current_date3.replace(day=1)
			n = total_days_of_month
		else:
			date_difference = month_end - month_start
			n = date_difference.days + 1

		if current_date3 == start_date or month_end == end_date:
			date_difference = month_end - month_start
			n = date_difference.days + 1
			n_prior = n

		if n_prior < total_days_of_month or n < total_days_of_month:
			prev_mlp2 = mlp2
			if not diff_annually:
				mlp2 = mlp2 * n / total_days_of_month
				if current_date3.date() in edates_pannum:
					for k in dict_ed_pannum.keys():
						temp_val = k
						temp = temp_val.split("-")
						escl = dict_ed_pannum[k]
						if current_date3.date() in escl:
							# pa_rate=rate_pa
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp2 = mrent
								mlp2 = mlp2 * n / total_days_of_month
							mlp2 = mlp2 + (rate * mlp2 / 100) + famt
							prev_mlp_escl2 = mlp2
							break
					# mlp=mlp+(pa_rate*mlp/100)
				elif current_date3.date() in edates_bd:
					for k in dict_ed_bdates.keys():
						# rpm=float(k)
						temp_val = k
						temp = temp_val.split("-")
						escl = dict_ed_bdates[k]
						current_month_str2 = current_date3.strftime("%Y-%m")
						if len(common_month) > 0:
							mlp_common_dict2 = common_dict.get(current_month_str2)
							if mlp_common_dict2 is not None:
								mlp2 = mlp_common_dict2
								prev_mlp_escl2 = mlp2
								break
						if current_date3.date() in escl:
							# mrent=rpm
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp2 = mrent
								mlp2 = mlp2 * n / total_days_of_month
							if mrent == 0 and rate == 0 and famt == 0:
								mlp2 = 0
							mlp2 = mlp2 + (rate * mlp2 / 100) + famt
							prev_mlp_escl2 = mlp2
							break
					# mlp=mrent
				elif current_date3.date() in edates_pafa:
					for k in dict_ed_pafa.keys():
						temp_val = k
						temp = temp_val.split("-")
						# rate_pa=temp[0]
						# f=temp[1]
						escl = dict_ed_pafa[k]
						if current_date3.date() in escl:
							# pafa_rate=float(rate_pa)
							# famt=float(f)
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp2 = mrent
								mlp2 = mlp2 + (rate * mlp2 / 100) + famt
							mlp2 = mlp2 + (rate * mlp2 / 100) + famt
							prev_mlp_escl2 = mlp2
							break
					# mlp=mlp+(pafa_rate*mlp/100)+famt

				interest_cost = (closing_liability - mlp2) * ((1 + daily_rate) ** n - 1)
				total_interest_cost += interest_cost
				closing_liability = closing_liability + interest_cost - mlp2
				if (doc.previous_wdv) != 0:
					prev_closing_liability_wdv = float(doc.previous_wdv)
					depreciation = (n / total_days) * prev_closing_liability_wdv
					wdv -= depreciation
				else:
					depreciation = (n / total_days) * prev_closing_liability
					wdv -= depreciation

				row = {
					"month_start_date": month_start.date(),
					"month_end_date": month_end.date(),
					"days_in_month": n,
					"mlp": mlp2,
					"pv": pv_arr[cnt2] if cnt2 < len(pv_arr) else "",
					"depreciation": round(depreciation, 3),
					"wdv": round(wdv, 3),
					"interest_cost": round(interest_cost, 3),
					"closing_liability": round(closing_liability, 3),
				}
				data.append(row)
				if mrent == 0 and rate == 0 and famt == 0:
					mlp2 = prev_mlp2
				if prev_mlp_escl2 is None:
					mlp2 = prev_mlp2
				else:
					mlp2 = prev_mlp_escl2
			else:
				mlp2_1 = mlp2 * n_prior / total_days_of_month
				mlp2_2 = 0
				if current_date3 == start_date or month_end == end_date:
					mlp2 = mlp2_1
				mlp_new = mlp2
				if current_date3.date() == start_date.date() and escalation and edates_pafa is not None:
					for k in dict_ed_pafa.keys():
						temp_val = k
						temp = temp_val.split("-")
						famt = float(temp[2])
						new_famt = famt * n_prior / total_days_of_month
						mlp_new = mlp_new + new_famt
						prev_mlp_escl2 = prev_mlp2 + famt
						break
				if current_date3.date() in edates_pannum and escalation:
					for k in dict_ed_pannum.keys():
						temp_val = k
						temp = temp_val.split("-")
						escl = dict_ed_pannum[k]
						if current_date3.date() in escl:
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp2 = mrent
								mlp2 = mlp2 * n / total_days_of_month
							mlp2 = mlp2 + (rate * mlp2 / 100) + famt
							mlp2_2 = mlp2 * n_next / total_days_of_month
							mlp_new = mlp2_1 + mlp2_2
							prev_mlp_escl2 = mlp2
							break
				elif current_date3.date() in edates_bd and escalation:
					for k in dict_ed_bdates.keys():
						temp_val = k
						temp = temp_val.split("-")
						escl = dict_ed_bdates[k]
						if current_date3.date() in escl:
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp2 = mrent
								mlp2 = mlp2 * n / total_days_of_month
							if mrent == 0 and rate == 0 and famt == 0:
								mlp2 = 0
							mlp2 = mlp2 + (rate * mlp2 / 100) + famt
							mlp_new = mlp2
							prev_mlp_escl2 = mlp2
							break
				elif current_date3.date() in edates_pafa and escalation:
					for k in dict_ed_pafa.keys():
						temp_val = k
						temp = temp_val.split("-")
						escl = dict_ed_pafa[k]
						if current_date3.date() in escl:
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp2 = mrent
								mlp2 = mlp2 * n / total_days_of_month
							mlp2 = mlp2 + (rate * mlp2 / 100) + famt
							mlp2_2 = mlp2 * n_next / total_days_of_month
							mlp_new = mlp2_1 + mlp2_2
							prev_mlp_escl2 = mlp2
							break

				mlp2 = mlp_new
				interest_cost = (closing_liability - mlp2) * ((1 + daily_rate) ** n - 1)
				total_interest_cost += interest_cost
				closing_liability = closing_liability + interest_cost - mlp2

				if (doc.previous_wdv) != 0:
					prev_closing_liability_wdv = float(doc.previous_wdv)
					depreciation = (n / total_days) * prev_closing_liability_wdv
					wdv -= depreciation
				else:
					depreciation = (n / total_days) * prev_closing_liability
					wdv -= depreciation
				row = {
					"month_start_date": month_start.date(),
					"month_end_date": month_end.date(),
					"days_in_month": n,
					"mlp": mlp2,
					"pv": pv_arr[cnt2] if cnt2 < len(pv_arr) else "",
					"depreciation": round(depreciation, 3),
					"wdv": round(wdv, 3),
					"interest_cost": round(interest_cost, 3),
					"closing_liability": round(closing_liability, 3),
				}
				data.append(row)
				if mrent == 0 and rate == 0 and famt == 0:
					mlp2 = prev_mlp2
				if prev_mlp_escl2 is None:
					mlp2 = prev_mlp2
				else:
					mlp2 = prev_mlp_escl2
		else:
			prev_mlp2 = mlp2
			if current_date3.date() == start_date.date() and escalation and edates_pafa is not None:
				for k in dict_ed_pafa.keys():
					temp_val = k
					temp = temp_val.split("-")
					famt = float(temp[2])
					mlp2 = mlp2 + famt
					break
			if current_date3.date() in edates_pannum:
				for k in dict_ed_pannum.keys():
					temp_val = k
					temp = temp_val.split("-")
					escl = dict_ed_pannum[k]
					if current_date3.date() in escl:
						# pa_rate=rate_pa
						rate = float(temp[0])
						mrent = float(temp[1])
						famt = float(temp[2])
						if mrent != 0:
							mlp2 = mrent
						mlp2 = mlp2 + (rate * mlp2 / 100) + famt
						break
				# mlp=mlp+(pa_rate*mlp/100)
			elif current_date3.date() in edates_bd:
				for k in dict_ed_bdates.keys():
					# rpm=float(k)
					temp_val = k
					temp = temp_val.split("-")
					escl = dict_ed_bdates[k]
					current_month_str2 = current_date3.strftime("%Y-%m")
					if len(common_month) > 0:
						mlp_common_dict2 = common_dict.get(current_month_str2)
						if mlp_common_dict2 is not None:
							mlp2 = mlp_common_dict2
							prev_mlp_escl2 = mlp2
							break
					if current_date3.date() in escl:
						# mrent=rpm
						rate = float(temp[0])
						mrent = float(temp[1])
						famt = float(temp[2])
						if mrent != 0:
							mlp2 = mrent
						if mrent == 0 and rate == 0 and famt == 0:
							mlp2 = 0
						mlp2 = mlp2 + (rate * mlp2 / 100) + famt
						break
				# mlp=mrent
			elif current_date3.date() in edates_pafa:
				for k in dict_ed_pafa.keys():
					temp_val = k
					temp = temp_val.split("-")
					# rate_pa=temp[0]
					# f=temp[1]
					escl = dict_ed_pafa[k]
					if current_date3.date() in escl:
						# pafa_rate=float(rate_pa)
						# famt=float(f)
						rate = float(temp[0])
						mrent = float(temp[1])
						famt = float(temp[2])
						if mrent != 0:
							mlp2 = mrent
						mlp2 = mlp2 + (rate * mlp2 / 100) + famt
						break
				# mlp=mlp+(pafa_rate*mlp/100)+famt

			interest_cost = (closing_liability - mlp2) * ((1 + daily_rate) ** n - 1)
			total_interest_cost += interest_cost
			closing_liability = closing_liability + interest_cost - mlp2

			if (doc.previous_wdv) != 0:
				prev_closing_liability_wdv = float(doc.previous_wdv)
				depreciation = (n / total_days) * prev_closing_liability_wdv
				wdv -= depreciation
			else:
				depreciation = (n / total_days) * prev_closing_liability
				wdv -= depreciation
			row = {
				"month_start_date": month_start.date(),
				"month_end_date": month_end.date(),
				"days_in_month": n,
				"mlp": mlp2,
				"pv": pv_arr[cnt2] if cnt2 < len(pv_arr) else "",
				"depreciation": round(depreciation, 3),
				"wdv": round(wdv, 3),
				"interest_cost": round(interest_cost, 3),
				"closing_liability": round(closing_liability, 3),
			}
			data.append(row)
			if mrent == 0 and rate == 0 and famt == 0 and escalation:
				mlp2 = prev_mlp2
		if month_end > end_date:
			month_end = end_date
		if esc_bd_end_date is not None:
			if esc_bd_end_date != esc_bd_end_date.replace(day=1):
				if current_date3.month == 12:
					next_current_date = datetime(current_date3.year + 1, 1, 1)
				else:
					next_current_date = datetime(current_date3.year, current_date3.month + 1, 1)
				if next_current_date.strftime("%Y-%m") == esc_bd_end_date.strftime("%Y-%m"):
					diff_annually = True

		# Move to next month
		if current_date3.month == 12:
			if diff_annually and not mid_diff_annually:
				current_date3 = datetime(current_date3.year + 1, 1, current_date3.day) - timedelta(days=1)
			elif diff_annually and mid_diff_annually:
				current_date3 = datetime(current_date3.year + 1, 1, esc_bd_end_date.day) - relativedelta(
					days=1
				)
			else:
				current_date3 = datetime(current_date3.year + 1, 1, 1)
		else:
			if diff_annually and not mid_diff_annually:
				current_date3 = datetime(
					current_date3.year, current_date3.month + 1, current_date3.day
				) - timedelta(days=1)
			elif diff_annually and mid_diff_annually:
				current_date3 = datetime(
					current_date3.year, current_date3.month + 1, esc_bd_end_date.day
				) - relativedelta(days=1)
			else:
				current_date3 = datetime(current_date3.year, current_date3.month + 1, 1)
		if current_date3.strftime("%Y-%m") == end_date.strftime("%Y-%m"):
			current_date3 = current_date3.replace(day=1)

	# Add summary row
	data.append(
		{
			"month_start_date": "",
			"month_end_date": "",
			"days_in_month": total_days,
			"mlp": round(total_mlp, 3),
			"pv": round(total_pv, 3),
			"depreciation": round(total_depre, 3),
			"wdv": "",
			"interest_cost": round(total_interest_cost, 3),
			"closing_liability": "",
		}
	)

	return columns, data

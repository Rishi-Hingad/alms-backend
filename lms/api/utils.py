# Methods to be used in Lease Report Calculation
import calendar
from calendar import monthrange
from collections import Counter
from datetime import date, datetime, time, timedelta

import frappe
from dateutil.relativedelta import relativedelta


@frappe.whitelist()
def calculate_daily_rate(doc):
	disc_doc = float(doc.discounting_rate) / 100
	if doc.calculation_rate_type == "Daily Rate":
		return (1 + disc_doc) ** (1 / 365) - 1
	return (1 + disc_doc) ** (1 / 12) - 1


@frappe.whitelist()
def get_diff_years(start_date, end_date):
	arg_sd = start_date
	arg_ed = end_date + timedelta(days=1)
	diff_years = relativedelta(arg_ed, arg_sd)
	diff_years = int(str(diff_years.years))
	return diff_years, arg_sd, arg_ed


@frappe.whitelist()
def get_month_details(cdate):
	month_start = cdate
	_, last_day = monthrange(cdate.year, cdate.month)
	month_end = datetime(cdate.year, cdate.month, last_day)

	month_start2 = cdate.replace(day=1)
	_, last_day2 = monthrange(cdate.year, cdate.month)
	month_end2 = datetime(cdate.year, cdate.month, last_day2)
	date_difference2 = month_end2 - month_start2
	total_days_of_month = date_difference2.days + 1

	return month_start, month_end, month_start2, month_end2, total_days_of_month


@frappe.whitelist()
def get_escalation_dates(doc, current_date, start_date, end_date, diff_years):
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
	famt = 0
	mrent = 0
	rate = 0
	esc_bd_end_date = None
	escalation = True
	edates_pannum = []
	edates_bd = []
	edates_pafa = []
	dict_ed_pannum = {}
	dict_ed_pafa = {}
	dict_ed_bdates = {}
	diff_annually = False
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
		escl_type = child.escalation_type
		if escl_type:
			etype.append(escl_type)
			if "Based On Dates" == escl_type:
				if child.monthly_rent in (
					None,
					"",
				):
					monthly_rent_bdates = 0
				else:
					monthly_rent_bdates = float(child.monthly_rent)
				if child.rate in (
					None,
					"",
				):
					rate_bdates = 0
				else:
					rate_bdates = float(child.rate)
				if child.fixed_amount in (
					None,
					"",
				):
					fixed_amt_bdates = 0
				else:
					fixed_amt_bdates = float(child.fixed_amount)
				bd_start_date = child.start_date
				bd_end_date = child.end_date
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
				dkey = (
					"Based On Dates"
					+ "-"
					+ str(monthly_rent_bdates)
					+ "-"
					+ str(rate_bdates)
					+ "-"
					+ str(fixed_amt_bdates)
					+ "-"
					+ str(bd_start_date)
					+ "-"
					+ str(bd_end_date)
				)
				dsubkey = (
					str(rate_bdates)
					+ "-"
					+ str(monthly_rent_bdates)
					+ "-"
					+ str(fixed_amt_bdates)
					+ "-"
					+ str(bd_start_date)
					+ "-"
					+ str(bd_end_date)
				)

				calc_dict[dkey] = {dsubkey: escl_dates_bdates}
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
			if child.monthly_rent in (
				None,
				"",
			):
				monthly_rent = 0
			else:
				monthly_rent = float(child.monthly_rent)
			if child.rate in (
				None,
				"",
			):
				rate = 0
			else:
				rate = float(child.rate)
			if child.fixed_amount in (
				None,
				"",
			):
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

		for key in calc_dict:
			calc_keys.append(key)

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

	return (
		escalation,
		edates_pannum,
		edates_bd,
		edates_pafa,
		dict_ed_pannum,
		dict_ed_bdates,
		dict_ed_pafa,
		esc_bd_end_date,
		diff_annually,
		rate,
		mrent,
		famt,
	)


@frappe.whitelist()
def get_common_month(doc, dict_ed_bdates, escalation, esc_bd_end_date):
	cnt_keys = len(dict_ed_bdates)
	dict_new = {}
	common_month = []
	common_dict = {}
	prev_mlp_next = {}
	mid_diff_annually = False
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
					mid_mlp_escl = []
					for k in range(len(keys)):
						key_n = keys[k]
						date_dict = dict_new[key_n]
						if common_month[i] in date_dict.keys():
							temp = key_n.split("-")
							cmonth = common_month[i]
							year, month = [int(part) for part in cmonth.split("-")]
							total_days_of_month = calendar.monthrange(year, month)[1]
							n = date_dict[common_month[i]]
							rate = float(temp[0])
							mrent = float(temp[1])
							famt = float(temp[2])
							if mrent != 0:
								mlp_escl = mrent
								# mlp_escl = mlp_escl * n / total_days_of_month
							if mrent == 0 and rate == 0 and famt == 0:
								mlp_escl = 0
							if rate != 0 and mrent == 0:
								if len(mid_mlp_escl) > 0:
									l = len(mid_mlp_escl)
									mlp_escl = mid_mlp_escl[l - 1]
								else:
									mlp_escl = float(doc.monthly_rent)
							mlp_escl = mlp_escl + (rate * mlp_escl / 100) + famt
							mid_mlp_escl.append(mlp_escl)
							prev_mlp_next[cmonth] = mlp_escl
							# if rate!=0 and mrent==0:
							mlp_escl = mlp_escl * n / total_days_of_month
							total_mlp_escl += mlp_escl
					common_dict[cmonth] = total_mlp_escl

	if esc_bd_end_date is not None:
		if esc_bd_end_date != esc_bd_end_date.replace(day=1):
			mid_diff_annually = True
		else:
			mid_diff_annually = False
	else:
		mid_diff_annually = False

	return (dict_new, common_month, common_dict, prev_mlp_next, mid_diff_annually)


def get_q_start_q_end(cnt, current_date, quarterly_months, end_date):
	q_start = current_date
	if cnt == 1 and current_date.day != 15:
		if current_date.month not in quarterly_months:
			if current_date.month >= 10:
				q_end = datetime(current_date.year + 1, 1, 15)
				# break
			else:
				for i in range(len(quarterly_months)):
					if quarterly_months[i] > current_date.month:
						# if current_date.month==2 and current_date.month<3:
						# 	_, last_day = monthrange(current_date.year, current_date.month)
						# 	q_end=datetime(current_date.year, current_date.month, last_day)
						# 	frappe.msgprint("new_date="+str(datetime(current_date.year, current_date.month, last_day)))
						# else:
						q_end = datetime(current_date.year, quarterly_months[i], 15)
						break
		elif current_date.month in quarterly_months:
			q_end = datetime(current_date.year, current_date.month, 15)
		else:
			if current_date.month == 12:
				q_end = datetime(current_date.year + 1, 1, 15)
			else:
				q_end = datetime(current_date.year, current_date.month + 1, 15)
	else:
		if current_date.month == 12:
			q_end = datetime(current_date.year + 1, 1, 15)
			if q_end > end_date:
				q_end = end_date
		else:
			if current_date.month in quarterly_months:
				for i in range(len(quarterly_months)):
					if quarterly_months[i] > current_date.month and current_date.month != 10:
						q_end = datetime(current_date.year, quarterly_months[i], 15)
						break
					else:
						q_end = datetime(current_date.year + 1, 1, 15)
				if current_date.month == 4 and current_date.day == 1:
					q_end = datetime(current_date.year, current_date.month, 15)
				# q_end = datetime(current_date.year, current_date.month+1, 15)
			else:
				q_end = datetime(current_date.year, current_date.month + 1, 15)
			if q_end > end_date:
				q_end = end_date
	if q_start.month == 1 and q_end.month == 4:
		q_end = datetime(current_date.year, 3, 31)
	# if q_end.month==4 and cnt!=1 and q_start.month>=1:
	# 	frappe.msgprint("**"+str(datetime(current_date.year, 3, 31))+"**")
	# frappe.msgprint("q_start="+str(q_start.date())+"--q_end="+str(q_end.date()))
	return (q_start, q_end)


@frappe.whitelist()
def get_mlp(
	escalation,
	n_prior,
	total_days_of_month,
	n,
	n_next,
	mlp,
	diff_annually,
	famt_prev_mlp1,
	current_date,
	start_date,
	end_date,
	month_end,
	edates_pafa,
	dict_ed_pafa,
	edates_pannum,
	dict_ed_pannum,
	edates_bd,
	dict_ed_bdates,
	common_month,
	common_dict,
	prev_mlp_escl,
	prev_mlp_next,
):
	mrent, rate, famt = 0, 0, 0
	if n_prior < total_days_of_month or n < total_days_of_month:
		prev_mlp = mlp
		if not diff_annually:
			if famt_prev_mlp1 != 0 and current_date.date() in edates_pafa:
				mlp = famt_prev_mlp1
			mlp = mlp * n / total_days_of_month
			if current_date.date() == start_date and escalation and edates_pafa is not None:
				for k in dict_ed_pafa.keys():
					temp_val = k
					temp = temp_val.split("-")
					famt = float(temp[2])
					famt_prev_mlp1 = prev_mlp
					new_famt = famt * n / total_days_of_month
					mlp = mlp + new_famt
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
							mlp = mlp * n / total_days_of_month
						if mrent == 0 and rate == 0 and famt == 0:
							mlp = 0
						mlp = mlp + (rate * mlp / 100) + famt
						prev_mlp_escl = mlp
						break
			elif current_date.date() in edates_bd:
				for k in dict_ed_bdates.keys():
					temp_val = k
					temp = temp_val.split("-")
					escl = dict_ed_bdates[k]
					current_month_str = current_date.strftime("%Y-%m")
					if len(common_month) > 0:
						mlp_common_dict = common_dict.get(current_month_str)
						if mlp_common_dict is not None:
							mlp = mlp_common_dict
							if prev_mlp_next[current_month_str] is not None:
								prev_mlp_escl = prev_mlp_next[current_month_str]
								prev_mlp = prev_mlp_escl
							else:
								prev_mlp_escl = prev_mlp
							break
					if current_date.date() in escl:
						rate = float(temp[0])
						mrent = float(temp[1])
						famt = float(temp[2])
						if mrent != 0:
							mlp = mrent
							_, last_day_of_month = monthrange(current_date.year, current_date.month)
							current_month_end = datetime(
								current_date.year, current_date.month, last_day_of_month
							)
							if (
								escl[len(escl) - 1] == current_month_end.date()
								and current_month_end.date() in escl
							) or (
								escl[len(escl) - 1] == end_date.date()
								and end_date.replace(day=1).date() == current_date.date()
								and escl[0] == end_date.replace(day=1).date()
							):
								mlp = mrent
							else:
								mlp = mlp * n / total_days_of_month

						if mrent == 0 and rate == 0 and famt == 0:
							mlp = 0
						if rate != 0 and mrent == 0:
							if escl[0] == current_date.date():
								rate = float(temp[0])
								famt = float(temp[2])
							else:
								rate = famt = 0
						mlp = mlp + (rate * mlp / 100) + famt
						if mrent == 0 and rate == 0 and famt == 0:
							prev_mlp_escl = prev_mlp
							if float(temp[0]) != 0 and rate == 0 and famt == 0:
								prev_mlp_escl = mlp
							else:
								prev_mlp_escl = prev_mlp
						else:
							prev_mlp_escl = mlp
						break
			elif current_date.date() in edates_pafa:
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
						if rate != 0 and mrent != 0:
							if escl[0] == current_date.date():
								mlp = float(temp[1])
								new_famt = famt * n / total_days_of_month
								mlp = mlp + new_famt
							else:
								mlp = prev_mlp_escl
						mlp = mlp + (rate * mlp / 100) + famt
						prev_mlp_escl = mlp
						famt_prev_mlp1 = famt_prev_mlp1 + (famt_prev_mlp1 * rate / 100)
						break
			return (mlp, prev_mlp_escl, famt_prev_mlp1, prev_mlp, mrent, rate, famt)
			# total_mlp += mlp
			# if cnt == 1:
			# 	pv = mlp
			# 	pv_arr.append(pv)
			# else:
			# 	pv = mlp / ((1 + daily_rate) ** ndays)
			# 	pv_arr.append(pv)
			# if prev_mlp_escl is None:
			# 	mlp = prev_mlp
			# else:
			# 	mlp = prev_mlp_escl
			# if mrent == 0 and rate == 0 and famt == 0 and escalation:
			# 	mlp = prev_mlp
		else:
			if famt_prev_mlp1 != 0 and current_date.date() in edates_pafa:
				mlp = famt_prev_mlp1
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
					famt_prev_mlp1 = prev_mlp
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
							# mlp = mlp * n / total_days_of_month
							_, last_day_of_month = monthrange(current_date.year, current_date.month)
							current_month_end = datetime(
								current_date.year, current_date.month, last_day_of_month
							)
							if (
								escl[len(escl) - 1] == current_month_end.date()
								and current_month_end.date() in escl
							) or (
								escl[len(escl) - 1] == end_date.date()
								and end_date.replace(day=1).date() == current_date.date()
								and escl[0] == end_date.replace(day=1).date()
							):
								mlp = mrent
							else:
								mlp = mlp * n / total_days_of_month

						if mrent == 0 and rate == 0 and famt == 0:
							mlp = 0
						if rate != 0 and mrent == 0:
							if escl[0] == current_date.date():
								rate = float(temp[0])
								famt = float(temp[2])
							else:
								rate = famt = 0
						mlp = mlp + (rate * mlp / 100) + famt
						mlp_new = mlp
						if mrent == 0 and rate == 0 and famt == 0:
							if float(temp[0]) != 0 and rate == 0 and famt == 0:
								prev_mlp_escl = mlp
							else:
								prev_mlp_escl = prev_mlp
						else:
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
						if rate != 0 and mrent != 0:
							if escl[0] == current_date.date():
								mlp = float(temp[1])
								new_famt = famt * n / total_days_of_month
								mlp = mlp + new_famt
							else:
								mlp = prev_mlp_escl
						mlp = mlp + (rate * mlp / 100) + famt

						if famt != 0:
							mlp_1 = mlp_1 + (famt * n_prior / total_days_of_month)
						mlp_2 = mlp * n_next / total_days_of_month
						mlp_new = mlp_1 + mlp_2
						prev_mlp_escl = mlp
						famt_prev_mlp1 = famt_prev_mlp1 + (famt_prev_mlp1 * rate / 100)
						break

			return (mlp_new, prev_mlp_escl, famt_prev_mlp1, prev_mlp, mrent, rate, famt)
	else:
		prev_mlp = mlp
		if current_date.date() == start_date.date() and escalation and edates_pafa is not None:
			for k in dict_ed_pafa.keys():
				temp_val = k
				temp = temp_val.split("-")
				famt = float(temp[2])
				famt_prev_mlp1 = prev_mlp
				mlp = mlp + famt
				break
		if current_date.date() in edates_pannum:
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
					mlp = mlp + (rate * mlp / 100) + famt
					prev_mlp_escl = mlp
					break
		elif current_date.date() in edates_bd:
			for k in dict_ed_bdates.keys():
				temp_val = k
				temp = temp_val.split("-")
				escl = dict_ed_bdates[k]
				current_month_str = current_date.strftime("%Y-%m")
				if len(common_month) > 0:
					mlp_common_dict = common_dict.get(current_month_str)
					if mlp_common_dict is not None:
						mlp = mlp_common_dict
						if prev_mlp_next[current_month_str] is not None:
							prev_mlp_escl = prev_mlp_next[current_month_str]
							prev_mlp = prev_mlp_escl
						else:
							prev_mlp_escl = prev_mlp
						break
				if current_date.date() in escl:
					rate = float(temp[0])
					mrent = float(temp[1])
					famt = float(temp[2])
					if mrent != 0:
						mlp = mrent
					if mrent == 0 and rate == 0 and famt == 0:
						mlp = 0
					if rate != 0 and mrent == 0:
						if escl[0] == current_date.date():
							rate = float(temp[0])
							famt = float(temp[2])
						else:
							rate = famt = 0
					mlp = mlp + (rate * mlp / 100) + famt
					break
		elif current_date.date() in edates_pafa:
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
					if rate != 0 and mrent != 0:
						if escl[0] == current_date.date():
							mlp = float(temp[1])
							mlp = mlp + famt
						else:
							mlp = prev_mlp
					mlp = mlp + (rate * mlp / 100) + famt
					break

		return (mlp, prev_mlp_escl, prev_mlp, mrent, rate, famt)

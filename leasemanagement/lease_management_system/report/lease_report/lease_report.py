# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import calendar
from calendar import monthrange
from collections import Counter
from datetime import date, datetime, timedelta

import frappe
from dateutil.relativedelta import relativedelta
from frappe import _ as translate

from leasemanagement.api.utils import (
	calculate_daily_rate,
	get_common_month,
	get_diff_years,
	get_escalation_dates,
	get_mlp,
	get_month_details,
	get_prev_wdv_modification,
	get_q_start_q_end,
)


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

	mlp = mlp2 = float(doc.monthly_rent)
	daily_rate = calculate_daily_rate(doc)
	diff_years, arg_sd, arg_ed = get_diff_years(start_date, end_date)

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
	total_mlp = 0
	total_pv = 0
	total_depre = 0
	pv_arr = [""]
	cnt = 0
	data = []
	quarterly_months = [1, 4, 7, 10]
	diff_annually2 = False
	mid_diff_annually2 = False
	prev_mlp_escl = prev_mlp_escl2 = None
	quarterly_report = False
	add_amount = False
	n_days_quarterly = 0
	famt_prev_mlp1 = 0

	if doc.type_of_asset == "Car":
		if doc.type_of_report == "Quarterly":
			quarterly_report = True
		if not doc.additional_amounts:
			add_amount = False
		else:
			add_amount = True
	(
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
	) = get_escalation_dates(doc, current_date, start_date, end_date, diff_years)
	diff_annually2 = diff_annually
	(dict_new, common_month, common_dict, prev_mlp_next, mid_diff_annually) = get_common_month(
		doc, dict_ed_bdates, escalation, esc_bd_end_date
	)
	mid_diff_annually2 = mid_diff_annually
	# First loop PV calculations
	while current_date <= end_date:
		cnt += 1
		if quarterly_report:
			q_start, q_end = get_q_start_q_end(cnt, current_date, quarterly_months, end_date)
			if cnt == 1:
				for child in doc.additional_amounts:
					if child.start_date == q_start.date() and child.end_date != q_end.date():
						q_end = datetime(child.end_date.year, child.end_date.month, child.end_date.day)
			quarterly_n = (q_end - q_start).days + 1
			n_days_quarterly += quarterly_n
			if (
				q_end.month not in quarterly_months
				and q_start.date() != arg_sd.date()
				and q_end.date() != end_date.date()
				and q_end.month != 3
			):
				if q_end.month == 12:
					current_date = datetime(q_end.year + 1, 1, 16)
				else:
					current_date = datetime(q_end.year, q_end.month, 16)
				cnt -= 1
				ndays += quarterly_n
				continue
		if diff_annually:
			if cnt > 1:
				if current_date != end_date:
					current_date = current_date + timedelta(days=1)
		month_start, month_end, month_start2, month_end2, total_days_of_month = get_month_details(
			current_date
		)
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
		else:
			n_prior = 0

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

		if quarterly_report:
			n = n_prior = total_days_of_month
			diff_annually = mid_diff_annually = False
		if doc.type_of_asset == "Car":
			if n == total_days_of_month:
				n_prior = n

		if n_prior < total_days_of_month or n < total_days_of_month:
			prev_mlp = mlp
			if not diff_annually:
				(mlp, prev_mlp_escl, famt_prev_mlp1, prev_mlp, mrent, rate, famt) = get_mlp(
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
				)

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
				(mlp_new, prev_mlp_escl, famt_prev_mlp1, prev_mlp, mrent, rate, famt) = get_mlp(
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
				)
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
			(mlp, prev_mlp_escl, prev_mlp, mrent, rate, famt) = get_mlp(
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
			)
			if add_amount:
				for child in doc.additional_amounts:
					if quarterly_report:
						if child.start_date == q_start.date() and child.end_date == q_end.date():
							mlp = child.additional_amount
					else:
						if child.start_date == month_start.date() and child.end_date == month_end.date():
							mlp = child.additional_amount

			if quarterly_report:
				if q_end.month == 3:
					total_mlp += 0
				else:
					total_mlp += mlp
			else:
				total_mlp += mlp
			if cnt == 1:
				pv = mlp
				pv_arr.append(pv)
			else:
				pv = mlp / ((1 + daily_rate) ** ndays)
				if quarterly_report:
					if q_end.month == 3:
						pv = 0
				pv_arr.append(pv)
			if (mrent == 0 and rate == 0 and famt == 0 and escalation) or quarterly_report or add_amount:
				mlp = prev_mlp
		total_pv += pv
		if quarterly_report:
			ndays += quarterly_n
		else:
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
			elif quarterly_report:
				if q_end != month_end and q_end != end_date:
					_, last_day_q_end = monthrange(q_end.year, q_end.month)
					if last_day_q_end == q_end.day:
						if q_end.month == 12:
							current_date = datetime(q_end.year + 1, 1, 1)
						else:
							current_date = datetime(q_end.year, q_end.month + 1, 1)
					else:
						current_date = datetime(q_end.year, 1, q_end.day + 1)
				elif q_end == end_date:
					if q_end.month != 12:
						current_date = datetime(q_end.year + 1, q_end.month + 1, 1)
					else:
						current_date = datetime(q_end.year + 1, 1, 1)
				elif q_end.month == 2:
					current_date = datetime(q_end.year, q_end.month + 1, 1)
				elif q_end.month == 3:
					current_date = datetime(q_end.year, q_end.month + 1, 1)
				else:
					current_date = datetime(current_date.year, 1, 16)
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
			elif quarterly_report:
				if q_end != month_end and q_end.month != 3 and q_end != end_date:
					_, last_day_q_end = monthrange(q_end.year, q_end.month)
					if last_day_q_end == q_end.day:
						if q_end.month == 12:
							current_date = datetime(q_end.year + 1, 1, 1)
						else:
							current_date = datetime(q_end.year, q_end.month + 1, 1)
					else:
						current_date = datetime(q_end.year, q_end.month, q_end.day + 1)
				elif q_end == end_date:
					if q_end.month != 12:
						current_date = datetime(q_end.year + 1, q_end.month + 1, 1)
					else:
						current_date = datetime(q_end.year + 1, 1, 1)
				elif q_end.month == 2:
					current_date = datetime(q_end.year, q_end.month + 1, 1)
				elif q_end.month == 3:
					current_date = datetime(q_end.year, q_end.month + 1, 1)
				else:
					current_date = datetime(current_date.year, current_date.month + 1, 16)
			else:
				current_date = datetime(current_date.year, current_date.month + 1, 1)
		if not quarterly_report:
			if current_date.strftime("%Y-%m") == end_date.strftime("%Y-%m"):
				current_date = current_date.replace(day=1)
	prev_closing_liability = total_pv
	total_days = ndays
	if doc.is_modified == 1:
		prev_wdv_mod = get_prev_wdv_modification(
			doc.calculation_rate_type, doc.previous_lease, doc.agreement_start_date, prev_closing_liability
		)
		if prev_wdv_mod is not None:
			doc.previous_wdv = float(prev_wdv_mod)

	# Second loop depreciation calculation
	current_date2 = start_date
	cnt1 = 0
	while current_date2 <= end_date:
		cnt1 += 1
		if quarterly_report:
			q_start, q_end = get_q_start_q_end(cnt1, current_date2, quarterly_months, end_date)
			if cnt1 == 1:
				for child in doc.additional_amounts:
					if child.start_date == q_start.date() and child.end_date != q_end.date():
						q_end = datetime(child.end_date.year, child.end_date.month, child.end_date.day)
			quarterly_n = (q_end - q_start).days + 1
			if (
				q_end.month not in quarterly_months
				and q_start.date() != arg_sd.date()
				and q_end.date() != end_date.date()
				and q_end.month != 3
			):
				if q_end.month == 12:
					current_date2 = datetime(q_end.year + 1, 1, 16)
				else:
					current_date2 = datetime(q_end.year, q_end.month, 16)
				cnt -= 1
				continue

		month_start = current_date2
		_, last_day = monthrange(current_date2.year, current_date2.month)
		month_end = datetime(current_date2.year, current_date2.month, last_day)
		if end_date < month_end:
			month_end = end_date

		date_difference = month_end - month_start
		n = date_difference.days + 1

		if quarterly_report:
			n = quarterly_n

		if (doc.previous_wdv) != 0:
			prev_closing_liability_wdv = float(doc.previous_wdv)
			depreciation = (n / total_days) * prev_closing_liability_wdv
			total_depre += depreciation
		else:
			depreciation = (n / total_days) * prev_closing_liability
			total_depre += depreciation

		# Move to next month
		if current_date2.month == 12:
			if quarterly_report:
				if q_end != month_end and q_end != end_date:
					_, last_day_q_end = monthrange(q_end.year, q_end.month)
					if last_day_q_end == q_end.day:
						if q_end.month == 12:
							current_date2 = datetime(q_end.year + 1, 1, 1)
						else:
							current_date2 = datetime(q_end.year, q_end.month + 1, 1)
					else:
						current_date2 = datetime(q_end.year, 1, q_end.day + 1)
				elif q_end == end_date:
					if q_end.month != 12:
						current_date2 = datetime(q_end.year + 1, q_end.month + 1, 1)
					else:
						current_date2 = datetime(q_end.year + 1, 1, 1)
				elif q_end.month == 2:
					current_date2 = datetime(q_end.year, q_end.month + 1, 1)
				elif q_end.month == 3:
					current_date2 = datetime(q_end.year, q_end.month + 1, 1)
				else:
					current_date2 = datetime(current_date2.year, 1, 16)
			else:
				current_date2 = datetime(current_date2.year + 1, 1, 1)
		else:
			if quarterly_report:
				if q_end != month_end and q_end.month != 3 and q_end != end_date:
					_, last_day_q_end = monthrange(q_end.year, q_end.month)
					if last_day_q_end == q_end.day:
						if q_end.month == 12:
							current_date2 = datetime(q_end.year + 1, 1, 1)
						else:
							current_date2 = datetime(q_end.year, q_end.month + 1, 1)
					else:
						current_date2 = datetime(q_end.year, q_end.month, q_end.day + 1)
				elif q_end == end_date:
					if q_end.month != 12:
						current_date2 = datetime(q_end.year, q_end.month + 1, 1)
					else:
						current_date2 = datetime(q_end.year + 1, 1, 1)
				elif q_end.month == 2:
					current_date2 = datetime(q_end.year, q_end.month + 1, 1)
				elif q_end.month == 3:
					current_date2 = datetime(q_end.year, q_end.month + 1, 1)
				else:
					current_date2 = datetime(current_date2.year, current_date2.month + 1, 16)
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
	famt_prev_mlp2 = 0
	while current_date3 <= end_date:
		cnt2 += 1
		if quarterly_report:
			q_start, q_end = get_q_start_q_end(cnt2, current_date3, quarterly_months, end_date)
			if cnt2 == 1:
				for child in doc.additional_amounts:
					if child.start_date == q_start.date() and child.end_date != q_end.date():
						q_end = datetime(child.end_date.year, child.end_date.month, child.end_date.day)
			quarterly_n = (q_end - q_start).days + 1
			if (
				q_end.month not in quarterly_months
				and q_start.date() != arg_sd.date()
				and q_end.date() != end_date.date()
				and q_end.month != 3
			):
				if q_end.month == 12:
					current_date3 = datetime(q_end.year + 1, 1, 16)
				else:
					current_date3 = datetime(q_end.year, q_end.month, 16)
				cnt -= 1
				continue

		if diff_annually2:
			if cnt2 > 1:
				if current_date3 != end_date:
					current_date3 = current_date3 + timedelta(days=1)
		month_start = current_date3
		_, last_day = monthrange(current_date3.year, current_date3.month)
		month_end = datetime(current_date3.year, current_date3.month, last_day)
		if diff_annually2:
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
		else:
			n_prior = 0

		if end_date < month_end:
			month_end = end_date

		month_start2 = current_date3.replace(day=1)
		_, last_day2 = monthrange(current_date3.year, current_date3.month)
		month_end2 = datetime(current_date3.year, current_date3.month, last_day2)
		date_difference2 = month_end2 - month_start2
		total_days_of_month = date_difference2.days + 1

		if diff_annually2 and not mid_diff_annually2:
			if month_end < month_end2 and month_end == end_date:
				month_end = current_date3
				month_start = current_date3.replace(day=1)
			date_difference = month_end - month_start
			n_next = date_difference.days + 1
			if not current_date3 == start_date:
				month_start = current_date3.replace(day=1)
			n = total_days_of_month
		elif mid_diff_annually2:
			if month_end < month_end2 and month_end != end_date:
				month_end = current_date3
				month_start = current_date3.replace(day=1)
			if month_end == end_date:
				month_end = end_date
				month_start = current_date3.replace(day=1)
			date_difference = month_end - month_start
			n_next = date_difference.days + 1
			n = total_days_of_month
		else:
			date_difference = month_end - month_start
			n = date_difference.days + 1
			n_next = 0
		if current_date3.strftime("%Y-%m") == end_date.strftime("%Y-%m"):
			month_end = end_date
		if current_date3 == start_date or month_end == end_date:
			date_difference = month_end - month_start
			n = date_difference.days + 1
			n_prior = n
		if quarterly_report:
			n = n_prior = total_days_of_month = quarterly_n
			diff_annually2 = mid_diff_annually2 = False
		if doc.type_of_asset == "Car":
			if n == total_days_of_month:
				n_prior = n
		if n_prior < total_days_of_month or n < total_days_of_month:
			prev_mlp2 = mlp2
			if not diff_annually2:
				(mlp2, prev_mlp_escl2, famt_prev_mlp2, prev_mlp2, mrent, rate, famt) = get_mlp(
					escalation,
					n_prior,
					total_days_of_month,
					n,
					n_next,
					mlp2,
					diff_annually2,
					famt_prev_mlp2,
					current_date3,
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
					prev_mlp_escl2,
					prev_mlp_next,
				)
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
				if cnt2 != 1:
					if month_start.date() != month_start.replace(day=1):
						month_start = month_start.replace(day=1)
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
				if prev_mlp_escl2 is None:
					mlp2 = prev_mlp2
				else:
					mlp2 = prev_mlp_escl2
				if mrent == 0 and rate == 0 and famt == 0 and escalation:
					mlp2 = prev_mlp2
			else:
				(mlp_new, prev_mlp_escl2, famt_prev_mlp2, prev_mlp2, mrent, rate, famt) = get_mlp(
					escalation,
					n_prior,
					total_days_of_month,
					n,
					n_next,
					mlp2,
					diff_annually2,
					famt_prev_mlp2,
					current_date3,
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
					prev_mlp_escl2,
					prev_mlp_next,
				)
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
				if cnt2 != 1:
					if month_start.date() != month_start.replace(day=1):
						month_start = month_start.replace(day=1)
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

				if prev_mlp_escl2 is None:
					mlp2 = prev_mlp2
				else:
					mlp2 = prev_mlp_escl2
				if mrent == 0 and rate == 0 and famt == 0 and escalation:
					mlp2 = prev_mlp2

		else:
			(mlp2, prev_mlp_escl2, prev_mlp2, mrent, rate, famt) = get_mlp(
				escalation,
				n_prior,
				total_days_of_month,
				n,
				n_next,
				mlp2,
				diff_annually2,
				famt_prev_mlp2,
				current_date3,
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
				prev_mlp_escl2,
				prev_mlp_next,
			)
			if add_amount:
				for child in doc.additional_amounts:
					if quarterly_report:
						if child.start_date == q_start.date() and child.end_date == q_end.date():
							mlp2 = child.additional_amount
					else:
						if child.start_date == month_start.date() and child.end_date == month_end.date():
							mlp2 = child.additional_amount
			if quarterly_report:
				if q_end.month == 3:
					mlp2 = 0
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
			if quarterly_report:
				row = {
					"month_start_date": q_start.date(),
					"month_end_date": q_end.date(),
					"days_in_month": n,
					"mlp": mlp2,
					"pv": pv_arr[cnt2] if cnt2 < len(pv_arr) else "",
					"depreciation": round(depreciation, 3),
					"wdv": round(wdv, 3),
					"interest_cost": round(interest_cost, 3),
					"closing_liability": round(closing_liability, 3),
				}
			else:
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
			if (mrent == 0 and rate == 0 and famt == 0 and escalation) or (quarterly_report) or (add_amount):
				mlp2 = prev_mlp2

		if month_end > end_date:
			month_end = end_date
		if esc_bd_end_date is not None:
			if esc_bd_end_date != esc_bd_end_date.replace(day=1):
				if current_date3.month == 12:
					next_current_date2 = datetime(current_date3.year + 1, 1, 1)
				else:
					next_current_date2 = datetime(current_date3.year, current_date3.month + 1, 1)
				if next_current_date2.strftime("%Y-%m") == esc_bd_end_date.strftime("%Y-%m"):
					diff_annually2 = True
		# Move to next month
		if current_date3.month == 12:
			if diff_annually2 and not mid_diff_annually2:
				current_date3 = datetime(current_date3.year + 1, 1, current_date3.day) - relativedelta(days=1)
			elif diff_annually2 and mid_diff_annually2:
				current_date3 = datetime(current_date3.year + 1, 1, esc_bd_end_date.day) - relativedelta(
					days=1
				)
			elif quarterly_report:
				if q_end != month_end and q_end != end_date:
					_, last_day_q_end = monthrange(q_end.year, q_end.month)
					if last_day_q_end == q_end.day:
						if q_end.month == 12:
							current_date3 = datetime(q_end.year + 1, 1, 1)
						else:
							current_date3 = datetime(q_end.year, q_end.month + 1, 1)
					else:
						current_date3 = datetime(q_end.year, 1, q_end.day + 1)
				elif q_end == end_date:
					if q_end.month != 12:
						current_date3 = datetime(q_end.year + 1, q_end.month + 1, 1)
					else:
						current_date3 = datetime(q_end.year + 1, 1, 1)
				elif q_end.month == 2:
					current_date3 = datetime(q_end.year, q_end.month + 1, 1)
				elif q_end.month == 3:
					current_date3 = datetime(q_end.year, q_end.month + 1, 1)
				else:
					current_date3 = datetime(current_date3.year, 1, 16)
			else:
				current_date3 = datetime(current_date3.year + 1, 1, 1)
		else:
			if diff_annually2 and not mid_diff_annually2:
				current_date3 = datetime(
					current_date3.year, current_date3.month + 1, current_date3.day
				) - relativedelta(days=1)
			elif diff_annually2 and mid_diff_annually2:
				current_date3 = datetime(
					current_date3.year, current_date3.month + 1, esc_bd_end_date.day
				) - relativedelta(days=1)
			elif quarterly_report:
				if q_end != month_end and q_end.month != 3 and q_end != end_date:
					_, last_day_q_end = monthrange(q_end.year, q_end.month)
					if last_day_q_end == q_end.day:
						if q_end.month == 12:
							current_date3 = datetime(q_end.year + 1, 1, 1)
						else:
							current_date3 = datetime(q_end.year, q_end.month + 1, 1)
					else:
						current_date3 = datetime(q_end.year, q_end.month, q_end.day + 1)
				elif q_end == end_date:
					if q_end.month != 12:
						current_date3 = datetime(q_end.year + 1, q_end.month + 1, 1)
					else:
						current_date3 = datetime(q_end.year + 1, 1, 1)
				elif q_end.month == 2:
					current_date3 = datetime(q_end.year, q_end.month + 1, 1)
				elif q_end.month == 3:
					current_date3 = datetime(q_end.year, q_end.month + 1, 1)
				else:
					current_date3 = datetime(current_date3.year, current_date3.month + 1, 16)
			else:
				current_date3 = datetime(current_date3.year, current_date3.month + 1, 1)
		if not quarterly_report:
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

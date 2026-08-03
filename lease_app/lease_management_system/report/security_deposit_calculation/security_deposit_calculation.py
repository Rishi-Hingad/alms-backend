# Copyright (c) 2026, Shradha_Siddhi and contributors
# For license information, please see license.txt

from datetime import date, datetime, timedelta

import frappe


def get_financial_year_end(dt):
	"""Return 31 March of the FY in which dt falls"""
	if dt.month > 3:
		return date(dt.year + 1, 3, 31)
	return date(dt.year, 3, 31)


def calculate_sd_schedule_fy(deposit_amount, interest_rate, start_date, end_date):
	schedule = []

	# convert strings to date
	start = datetime.strptime(start_date, "%Y-%m-%d").date() if isinstance(start_date, str) else start_date
	end = datetime.strptime(end_date, "%Y-%m-%d").date() if isinstance(end_date, str) else end_date

	rate = interest_rate / 100 if interest_rate > 1 else interest_rate
	total_days_utilised = (end - start).days + 1
	total_days = 0
	dates = []
	current = start

	# Generate FY end dates
	while current < end:
		fy_end = get_financial_year_end(current)
		if fy_end >= end:
			# if fy_end.month > end.month:
			fy_end = end
		dates.append(fy_end)
		current = fy_end + timedelta(days=1)

	prev_days = None
	prev_pv = None
	prev_amortized_cost = None

	for i, dt in enumerate(dates):
		# total days including start date
		days_as = (dt - start).days + 1

		# period days including start date
		period_days = (dt - (start if i == 0 else dates[i - 1] + timedelta(days=1))).days + 1
		if i != 0:
			total_days += period_days
		# frappe.msgprint(str((end - dt).days + 1))
		if i == 0:
			t = total_days_utilised / 365
		else:
			t = days_as / 365

		if i == 0:
			pv = deposit_amount / ((1 + rate) ** t)
			amortised_cost = pv * (((1 + rate) ** (period_days / 365)) - 1)
		else:
			pv = prev_pv + prev_amortized_cost
			if prev_days is not None:
				amortised_cost = pv * (((1 + rate) ** ((total_days - prev_days) / 365)) - 1)

		prepaid_lease = deposit_amount - pv - amortised_cost
		retained_earn = amortised_cost
		schedule.append(
			{
				"period": i + 1,
				"from_date": start if i == 0 else dates[i - 1] + timedelta(days=1),
				"to_date": dt,
				"days_as": days_as,
				"present_value": round(pv, 2),
				"prepaid_lease": round(prepaid_lease, 2),
				"amortised_cost": round(amortised_cost, 2),
				"retained_earnings": round(retained_earn, 2),
				"days_in_period": period_days,
				"total_days": total_days,
				"closing_value": round((pv + amortised_cost), 2),
			}
		)

		prev_days = total_days
		prev_pv = pv
		prev_amortized_cost = amortised_cost

	return schedule


# -----------------------------
# Script Report execute function
# -----------------------------
def execute(filters=None):
	columns = get_columns()
	data = []

	if not filters:
		return columns, data
	lease_id = filters.get("lease_id")
	# deposit_amount = filters.get("deposit_amount")
	# interest_rate = filters.get("interest_rate")
	# start_date = filters.get("start_date")
	# end_date = filters.get("end_date")
	if lease_id:
		res = frappe.get_value(
			"Lease Management",
			{"name": lease_id},
			["agreement_start_date", "agreement_end_date", "security_deposit_amount", "discounting_rate"],
			as_dict=True,
		)
		if res:
			deposit_amount = float(res.security_deposit_amount)
			interest_rate = float(res.discounting_rate)
			start_date = res.agreement_start_date
			end_date = res.agreement_end_date

	if not (deposit_amount and interest_rate and start_date and end_date):
		return columns, data

	schedule = calculate_sd_schedule_fy(deposit_amount, interest_rate, start_date, end_date)

	for row in schedule:
		data.append(
			[
				row["period"],
				row["from_date"],
				row["to_date"],
				row["days_as"],
				row["present_value"],
				row["prepaid_lease"],
				row["amortised_cost"],
				row["retained_earnings"],
				row["days_in_period"],
				row["total_days"],
				row["closing_value"],
			]
		)

	return columns, data


def get_columns():
	return [
		{"label": "Period", "fieldtype": "Int", "width": 80},
		{"label": "From Date", "fieldtype": "Date", "width": 120},
		{"label": "To Date", "fieldtype": "Date", "width": 120},
		{"label": "Days As", "fieldtype": "Int", "width": 120},
		{"label": "Present Value", "fieldtype": "Currency", "width": 150},
		{"label": "Prepaid Lease", "fieldtype": "Currency", "width": 150},
		{"label": "Amortised Cost", "fieldtype": "Currency", "width": 150},
		{"label": "Retained Earnings", "fieldtype": "Currency", "width": 150},
		{"label": "Days (Period)", "fieldtype": "Int", "width": 120},
		{"label": "Total Days", "fieldtype": "Int", "width": 120},
		{"label": "Closing Value", "fieldtype": "Currency", "width": 150},
	]

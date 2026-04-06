# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

from datetime import date, datetime

import frappe
import pandas as pd
from dateutil.relativedelta import relativedelta
from frappe import _ as translate
from frappe.desk.query_report import run


def execute(filters=None):
	columns = [
		{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 150},
		{
			"label": translate("Total Rent"),
			"fieldname": "total_rent",
			"fieldtype": "Currency",
			"width": 150,
			"precision": 4,
		},
	]

	today = frappe.utils.nowdate()
	if isinstance(today, str):
		today = datetime.strptime(today, "%Y-%m-%d")

	# current_month = today.strftime("%Y-%m")
	# previous_month = (today - relativedelta(months=1)).strftime("%Y-%m")
	# next_month = (today + relativedelta(months=1)).strftime("%Y-%m")

	# leases = frappe.get_all(
	# 	"Lease Management",
	# 	# filters={"agreement_start_date": ("<=", today), "agreement_end_date": (">=", today)},
	# 	filters={"agreement_start_date": ("<=", today), "type_of_asset": "Immovable"},
	# 	fields=["name"],
	# )

	monthly_totals = {"Previous Month": 0.0, "Current Month": 0.0, "Next Month": 0.0}

	# Previous Month Total Rent
	prev_report_data = run(
		"Monthly Lease Payment",
		filters={
			"month": (today - relativedelta(months=1)).strftime("%B"),
			"year": (today - relativedelta(months=1)).strftime("%Y"),
		},
	)
	prev_rows = prev_report_data.get("result")
	prev_report_df = pd.DataFrame(prev_rows)
	prev_rent = 0
	for _, row in prev_report_df.iterrows():
		prev_rent += round(row.get("total_rent"), 3)

	# Current Month Total Rent
	cur_report_data = run(
		"Monthly Lease Payment", filters={"month": today.strftime("%B"), "year": today.strftime("%Y")}
	)
	cur_rows = cur_report_data.get("result")
	report_df = pd.DataFrame(cur_rows)
	cur_rent = 0
	for _, row in report_df.iterrows():
		cur_rent += round(row.get("total_rent"), 3)

	# Next Month Total Rent
	next_report_data = run(
		"Monthly Lease Payment",
		filters={
			"month": (today + relativedelta(months=1)).strftime("%B"),
			"year": (today + relativedelta(months=1)).strftime("%Y"),
		},
	)
	next_rows = next_report_data.get("result")
	next_report_df = pd.DataFrame(next_rows)
	next_rent = 0
	for _, row in next_report_df.iterrows():
		next_rent += round(row.get("total_rent"), 3)

	monthly_totals["Previous Month"] = prev_rent
	monthly_totals["Current Month"] = cur_rent
	monthly_totals["Next Month"] = next_rent

	# for lease in leases:
	# 	lease_doc = frappe.get_doc("Lease Management", lease.name)
	# 	timeline_l = lease_doc.get_lease_rent_timeline()
	# 	monthly_totals["Previous Month"] += timeline_l.get(previous_month, 0)
	# 	monthly_totals["Current Month"] += timeline_l.get(current_month, 0)
	# 	monthly_totals["Next Month"] += timeline_l.get(next_month, 0)

	# Prepare rows
	data = []
	for month, total in monthly_totals.items():
		if month == "Previous Month":
			month = (today - relativedelta(months=1)).strftime("%B %Y")
		elif month == "Current Month":
			month = today.strftime("%B %Y")
		elif month == "Next Month":
			month = (today + relativedelta(months=1)).strftime("%B %Y")
		data.append({"month": month, "total_rent": total})

	return columns, data

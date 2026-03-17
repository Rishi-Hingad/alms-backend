# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import math
from calendar import monthrange
from datetime import date, datetime

import frappe
import pandas as pd
from dateutil.relativedelta import relativedelta
from frappe import _
from frappe.desk.query_report import run
from frappe.utils import getdate


def execute(filters=None):
	if not filters:
		return [], []

	company_name = filters.get("company_name")

	if not company_name:
		frappe.throw(_("Please select a Company."))

	data = []
	columns = [
		{"label": _("Lease"), "fieldname": "lease_id", "fieldtype": "Data", "width": 120},
		{"label": _("Vendor"), "fieldname": "vendor", "fieldtype": "Data", "width": 120},
		{
			"label": _("Asset Description"),
			"fieldname": "asset_description",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Opening ROU Asset"),
			"fieldname": "rou_opening",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Additions - ROU Asset"),
			"fieldname": "additions_rou_asset",
			"fieldtype": "Currency",
			"width": 120,
			"precision": 2,
		},
		{
			"label": _("Modification - ROU"),
			"fieldname": "modification_rou",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Termination - ROU"),
			"fieldname": "termination_rou",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Depreciation"),
			"fieldname": "depreciation",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Closing ROU Asset"),
			"fieldname": "rou_closing",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Opening Liability"),
			"fieldname": "liability_opening",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Additions - Lease Liability"),
			"fieldname": "additions_lease_liability",
			"fieldtype": "Currency",
			"width": 120,
			"precision": 2,
		},
		{
			"label": _("Modification - Lease Liability"),
			"fieldname": "modification_lease_liability",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Interest Expense"),
			"fieldname": "interest",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Rent Paid"),
			"fieldname": "rent_paid",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Termination - Lease Liability"),
			"fieldname": "termination_lease_liability",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Closing Liability"),
			"fieldname": "liability_closing",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Check ROU"),
			"fieldname": "check_rou",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": _("Check Lease Liability"),
			"fieldname": "check_liability",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
	]

	fin_start_year = filters.get("fin_start_year")  # output 2025
	fin_end_year = filters.get("fin_end_year")  # output 2026
	fy_start = getdate(f"{fin_start_year}-04-01")
	fy_end = getdate(f"{fin_end_year}-03-31")
	leases = frappe.get_all(
		"Lease Management",
		order_by="name asc",
		filters={
			"Company": company_name,
			"agreement_start_date": ["<=", fy_end],
			"agreement_end_date": [">=", fy_start],
		},
		fields=["name"],
	)

	if len(leases) == 0:
		frappe.throw(_("No Report Available for the Selected Company"))

	grand_total_opening_rou = 0
	grand_total_closing_rou = 0
	grand_total_opening_liability = 0
	grand_total_closing_liability = 0

	for lease in leases:
		lease_doc = frappe.get_doc("Lease Management", lease.name)
		lease_status = lease_doc.status
		if lease_doc.type_of_asset == "Immovable":
			prop_doc = frappe.get_doc("Property Master", lease_doc.property_description)
		else:
			car_desc = frappe.get_doc("Car Description Master", lease_doc.car_description)
		modified_start = None
		terminated_on = None
		terminated = False
		modified = False
		if lease_status == "Discarded":
			if lease_doc.modifications:
				modified_start = frappe.db.get_value(
					"Lease Management", lease_doc.modifications[0].modified_lease, "agreement_start_date"
				)
				sum_modified = datetime(
					modified_start.year, modified_start.month, modified_start.day
				) - relativedelta(days=1)
				lease_doc.agreement_end_date = sum_modified
		if lease_status == "Terminated":
			terminated_on = lease_doc.termination_date + relativedelta(days=1)
			lease_doc.agreement_end_date = lease_doc.termination_date

		msdate = date(int(fin_start_year), 4, 1)
		medate = date(int(fin_end_year), 3, 1)

		if modified_start is not None:
			if modified_start > msdate and modified_start <= medate:
				modified = True

		if terminated_on is not None:
			if terminated_on > msdate and terminated_on <= medate:
				terminated = True

		lease_end = None
		if lease_doc.agreement_end_date:
			lease_end = getdate(lease_doc.agreement_end_date)

		if lease_end and lease_end < msdate:
			continue

		if lease_doc.calculation_rate_type == "Daily Rate":
			lreport = "Lease Report"
		else:
			lreport = "Lease Report Monthly (With Escalation)"
		if lease_doc.status == "Terminated":
			result = run(lreport, filters={"docname": lease.name, "sum_modified": terminated_on})
		else:
			result = run(lreport, filters={"docname": lease.name, "sum_modified": modified_start})
		rows = result.get("result")

		# Convert to DataFrame
		df = pd.DataFrame(rows)

		# Ensure the 'month_start_date' column is datetime
		df["month_start_date"] = pd.to_datetime(df["month_start_date"])

		# # Create a date range for the months
		# date_range = pd.date_range(start=str(msdate), end=str(medate), freq="MS")  # MS = Month Start

		# # Merge your date range with the DataFrame to align months
		# lease_df = pd.DataFrame({"month_start_date": date_range}).merge(df, on="month_start_date", how="left")

		# if lease_doc.type_of_asset=="Car" and lease_doc.type_of_report=="Quarterly":
		# 	sdate = datetime(int(fin_start_year), 3, 31)
		# 	edate = datetime(int(fin_end_year), 3, 31)
		# else:
		sdate = date(int(fin_start_year), 3, 31)
		edate = date(int(fin_end_year), 3, 31)
		mod_rou = 0
		mod_lia = 0
		ter_rou = 0
		ter_lia = 0

		if lease_end < edate:
			# 	edate=lease_end
			medate = date(lease_end.year, lease_end.month, lease_end.day)

		row_opening = df.loc[df["month_end_date"] == sdate]

		if len(row_opening) == 1:
			opening_rou = row_opening["wdv"].iloc[0]
			opening_liability = row_opening["closing_liability"].iloc[0]
		else:
			opening_rou = 0
			opening_liability = 0

		row_closing = df.loc[df["month_end_date"] == edate]
		if len(row_closing) == 1:
			closing_rou = row_closing["wdv"].iloc[0]
			closing_liability = row_closing["closing_liability"].iloc[0]
			if lease_end < edate:
				closing_rou = 0
				closing_liability = 0
		else:
			closing_rou = 0
			closing_liability = 0

		df["month_end_date"] = pd.to_datetime(df["month_end_date"])
		mlp_list, interest_list, depreciation_list = [], [], []
		# if lease_doc.type_of_asset=="Car":
		dates = df["month_start_date"].dropna().dt.date.tolist()
		# dates_end = df["month_end_date"].dropna().dt.date.tolist()
		for i in range(len(dates)):
			if dates[i] >= msdate and dates[i] <= medate:
				val = str(dates[i])
				row = df.loc[df["month_start_date"] == val]
				mlp = row["mlp"].iloc[0]
				interest = row["interest_cost"].iloc[0]
				depre = row["depreciation"].iloc[0]
				mlp_list.append(mlp)
				interest_list.append(interest)
				depreciation_list.append(depre)
		# else:
		# 	# Extract mlp column as a list
		# 	mlp_list = lease_df["mlp"].tolist()
		# 	interest_list = lease_df["interest_cost"].tolist()
		# 	depreciation_list = lease_df["depreciation"].tolist()

		if opening_rou == 0:
			if lease_doc.status != "Modified":
				additions_rou_asset = df["wdv"][0]
				additions_lease_lia = additions_rou_asset
			else:
				additions_rou_asset = additions_lease_lia = 0
		else:
			additions_rou_asset = additions_lease_lia = 0
		total_rent_paid = 0
		total_interest_cost = 0
		total_depreciation = 0

		for i in range(len(mlp_list)):
			if not math.isnan(mlp_list[i]):
				total_rent_paid += mlp_list[i]
			if not math.isnan(interest_list[i]):
				total_interest_cost += interest_list[i]
			if not math.isnan(depreciation_list[i]):
				total_depreciation += depreciation_list[i]

		if modified:
			mod_rou = -(row["wdv"].iloc[0])
			mod_lia = -(row["closing_liability"].iloc[0])
		if lease_status == "Modified":
			if opening_rou == 0 and opening_liability == 0:
				mod_rou = df["wdv"][0]
				mod_lia = df["closing_liability"][0]
		if terminated:
			ter_rou = -(row["wdv"].iloc[0])
			ter_lia = -(row["closing_liability"].iloc[0])
		rou_check = opening_rou - total_depreciation - closing_rou + additions_rou_asset + mod_rou + ter_rou
		liability_check = (
			opening_liability
			+ total_interest_cost
			- total_rent_paid
			- closing_liability
			+ additions_rou_asset
			+ mod_lia
			+ ter_lia
		)
		grand_total_opening_rou += opening_rou
		grand_total_closing_rou += closing_rou
		grand_total_opening_liability += opening_liability
		grand_total_closing_liability += closing_liability

		if lease_doc.type_of_asset == "Immovable":
			data.append(
				{
					"lease_id": lease.name,
					"vendor": prop_doc.vendor,
					"asset_description": prop_doc.address,
					"rou_opening": opening_rou,
					"rou_closing": closing_rou,
					"liability_opening": opening_liability,
					"liability_closing": closing_liability,
					"rent_paid": total_rent_paid,
					"interest": total_interest_cost,
					"depreciation": total_depreciation,
					"additions_rou_asset": additions_rou_asset,
					"additions_lease_liability": additions_lease_lia,
					"check_rou": rou_check,
					"check_liability": liability_check,
					"modification_rou": mod_rou,
					"modification_lease_liability": mod_lia,
					"termination_rou": ter_rou,
					"termination_lease_liability": ter_lia,
				}
			)
		else:
			data.append(
				{
					"lease_id": lease.name,
					"vendor": car_desc.vendor,
					"asset_description": car_desc.employee_name,
					"rou_opening": opening_rou,
					"rou_closing": closing_rou,
					"liability_opening": opening_liability,
					"liability_closing": closing_liability,
					"rent_paid": total_rent_paid,
					"interest": total_interest_cost,
					"depreciation": total_depreciation,
					"additions_rou_asset": additions_rou_asset,
					"additions_lease_liability": additions_lease_lia,
					"check_rou": rou_check,
					"check_liability": liability_check,
					"modification_rou": mod_rou,
					"modification_lease_liability": mod_lia,
					"termination_rou": ter_rou,
					"termination_lease_liability": ter_lia,
				}
			)
	data.append(
		{
			"lease_id": "",
			"vendor": "",
			"asset_description": "",
			"rou_opening": grand_total_opening_rou,
			"rou_closing": grand_total_closing_rou,
			"liability_opening": grand_total_opening_liability,
			"liability_closing": grand_total_closing_liability,
			"rent_paid": "",
			"interest": "",
			"depreciation": "",
			"additions_rou_asset": "",
			"additions_lease_liability": "",
			"check_rou": "",
			"check_liability": "",
			"modification_rou": "",
			"modification_lease_liability": "",
			"termination_rou": "",
			"termination_lease_liability": "",
		}
	)

	return columns, data

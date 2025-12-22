# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import math
from datetime import date, datetime

import frappe
import pandas as pd
from frappe.desk.query_report import run


def execute(filters=None):
	if not filters:
		return [], []

	company_name = filters.get("company_name")

	if not company_name:
		frappe.throw("Please select a Company.")

	data = []
	columns = [
		{"label": "Lease", "fieldname": "lease_id", "fieldtype": "Data", "width": 120},
		{"label": "Vendor", "fieldname": "vendor", "fieldtype": "Data", "width": 120},
		{"label": "Asset Description", "fieldname": "asset_description", "fieldtype": "Data", "width": 150},
		{
			"label": "Opening ROU Asset",
			"fieldname": "rou_opening",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": "Closing ROU Asset",
			"fieldname": "rou_closing",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": "Opening Liability",
			"fieldname": "liability_opening",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": "Closing Liability",
			"fieldname": "liability_closing",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": "Rent Paid",
			"fieldname": "rent_paid",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": "Interest Expense",
			"fieldname": "interest",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": "Depreciation",
			"fieldname": "depreciation",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": "Additions - ROU Asset",
			"fieldname": "additions_rou_asset",
			"fieldtype": "Currency",
			"width": 120,
			"precision": 2,
		},
		{
			"label": "Additions - Lease Liability",
			"fieldname": "additions_lease_liability",
			"fieldtype": "Currency",
			"width": 120,
			"precision": 2,
		},
		{
			"label": "Check ROU",
			"fieldname": "check_rou",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": "Check Lease Liability",
			"fieldname": "check_liability",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
	]

	# def get_financial_year(d=None):
	# 	if d is None:
	# 		d = date.today()

	# 	year = d.year

	# 	# If month is Jan to Mar, the financial year started last year
	# 	if d.month < 4:
	# 		start_year = year - 1
	# 		end_year = year
	# 	else:
	# 		start_year = year
	# 		end_year = year + 1

	# 	return start_year,end_year

	fin_start_year = filters.get("fin_start_year")
	fin_end_year = filters.get("fin_end_year")
	leases = frappe.get_all(
		"Lease Management",
		order_by="name asc",
		filters={
			"Company": company_name,
		},
		fields=["name"],
	)

	if len(leases) == 0:
		frappe.throw("No Report Available for the Selected Company")

	grand_total_opening_rou = 0
	grand_total_closing_rou = 0
	grand_total_opening_liability = 0
	grand_total_closing_liability = 0

	for lease in leases:
		lease_doc = frappe.get_doc("Lease Management", lease.name)
		if lease_doc.type_of_asset == "Immovable":
			prop_doc = frappe.get_doc("Property Master", lease_doc.property_description)
		else:
			car_desc = frappe.get_doc("Car Description Master", lease_doc.car_description)

		msdate = date(int(fin_start_year), 4, 1)
		medate = date(int(fin_end_year), 3, 1)

		lease_end = None
		if lease_doc.agreement_end_date:
			lease_end = datetime.strptime(str(lease_doc.agreement_end_date), "%Y-%m-%d").date()

		if lease_end and lease_end < msdate:
			continue

		if lease_doc.calculation_rate_type == "Daily Rate":
			lreport = "Lease Report"
		else:
			lreport = "Lease Report Monthly (With Escalation)"
		result = run(lreport, filters={"docname": lease.name})
		rows = result.get("result")
		sdate = date(int(fin_start_year), 3, 31)
		edate = date(int(fin_end_year), 3, 31)
		row_opening = next((r for r in rows if str(r.get("month_end_date")) == str(sdate)), None)
		if row_opening:
			opening_rou = row_opening.get("wdv")
			opening_liability = row_opening.get("closing_liability")
		else:
			opening_rou = 0
			opening_liability = 0

		row_closing = next((r for r in rows if str(r.get("month_end_date")) == str(edate)), None)
		if row_closing:
			closing_rou = row_closing.get("wdv")
			closing_liability = row_closing.get("closing_liability")
		else:
			closing_rou = 0
			closing_liability = 0

		# Convert to DataFrame
		df = pd.DataFrame(rows)

		# Ensure the 'month_start_date' column is datetime
		df["month_start_date"] = pd.to_datetime(df["month_start_date"])

		# Create a date range for the months
		date_range = pd.date_range(start=str(msdate), end=str(medate), freq="MS")  # MS = Month Start

		# Merge your date range with the DataFrame to align months
		lease_df = pd.DataFrame({"month_start_date": date_range}).merge(df, on="month_start_date", how="left")

		# Extract mlp column as a list
		mlp_list = lease_df["mlp"].tolist()
		interest_list = lease_df["interest_cost"].tolist()
		depreciation_list = lease_df["depreciation"].tolist()

		if opening_rou == 0:
			wdv_list = df["wdv"].tolist()
			additions_rou_asset = wdv_list[0]
			additions_lease_lia = additions_rou_asset
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

		rou_check = opening_rou - total_depreciation - closing_rou + additions_rou_asset
		liability_check = (
			opening_liability
			+ total_interest_cost
			- total_rent_paid
			- closing_liability
			+ additions_rou_asset
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
		}
	)

	return columns, data

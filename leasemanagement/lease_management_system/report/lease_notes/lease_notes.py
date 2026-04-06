# Copyright (c) 2026, Shradha_Siddhi and contributors
# For license information, please see license.txt

from datetime import date, datetime, timedelta

import frappe
import pandas as pd
from frappe import _ as translate
from frappe.desk.query_report import run
from frappe.utils import getdate

from leasemanagement.api.utils import get_formatted_date, get_sd_amount, get_terminated_lease_data


def execute(filters=None):
	if not filters:
		return [], []

	company_name = filters.get("company_name")

	if not company_name:
		frappe.throw(translate("Please select a Company."))

	fin_start_year = int(filters.get("fin_start_year"))
	fin_end_year = int(filters.get("fin_end_year"))

	if not fin_start_year or not fin_end_year:
		frappe.throw(translate("Please Enter Financial Start Year"))

	data = []
	columns = [
		{"label": translate("Particulars"), "fieldname": "particulars", "fieldtype": "Data", "width": 400},
		{
			"label": translate("Right of Use - Immovable Property"),
			"fieldname": "rou_immovable",
			"fieldtype": "Currency",
			"width": 240,
			"precision": 2,
		},
		{
			"label": translate("Right of Use - Vehicle"),
			"fieldname": "rou_vehicle",
			"fieldtype": "Currency",
			"width": 240,
			"precision": 2,
		},
		{
			"label": translate("Total"),
			"fieldname": "total",
			"fieldtype": "Currency",
			"width": 300,
			"precision": 2,
		},
	]

	cur_summary_result = run(
		"Lease Summary Report",
		filters={
			"company_name": company_name,
			"fin_start_year": fin_start_year,
			"fin_end_year": fin_end_year,
		},
	)
	sum_rows = cur_summary_result.get("result")
	sum_df = pd.DataFrame(sum_rows)
	cur_terminated_leases = []
	prev_terminated_leases = []
	# prev_sd_leases = []
	# cur_sd_leases = []
	cur_ter_gross_wdv_immovable = 0
	cur_ter_gross_wdv_vehicle = 0
	cur_ter_acc_deprec_immovable = 0
	cur_ter_acc_deprec_vehicle = 0
	prev_ter_acc_deprec_vehicle = 0
	prev_ter_acc_deprec_immovable = 0
	prev_ter_gross_wdv_vehicle = 0
	prev_ter_gross_wdv_immovable = 0
	cur_mod_wdv_immovable = 0
	cur_mod_wdv_vehicle = 0
	prev_mod_wdv_immovable = 0
	prev_mod_wdv_vehicle = 0
	for _, row in sum_df.iterrows():
		# cur_security_deposit = frappe.get_value(
		# 	"Lease Management", {"name": row["lease_id"]}, "security_deposit"
		# )
		# if cur_security_deposit == "Paid":
		# 	cur_sd_leases.append(row["lease_id"])
		if row["termination_rou"] != 0 and (
			isinstance(row["termination_rou"], int) or isinstance(row["termination_rou"], float)
		):
			cur_terminated_leases.append(row["lease_id"])
		if row["modification_rou"] != 0 and (
			isinstance(row["modification_rou"], int) or isinstance(row["modification_rou"], float)
		):
			cur_type_of_asset = frappe.get_value(
				"Lease Management", {"name": row["lease_id"]}, "type_of_asset"
			)
			if cur_type_of_asset == "Immovable":
				cur_mod_wdv_immovable += round(row["modification_rou"], 3)
			else:
				cur_mod_wdv_vehicle += round(row["modification_rou"], 3)
			# frappe.msgprint(str(row["lease_id"])+"row['modification_rou']="+str(row["modification_rou"]))
	if len(cur_terminated_leases) > 0:
		(
			cur_ter_acc_deprec_vehicle,
			cur_ter_acc_deprec_immovable,
			cur_ter_gross_wdv_vehicle,
			cur_ter_gross_wdv_immovable,
		) = get_terminated_lease_data(cur_terminated_leases)
	cur_ter_gross_wdv_immovable += round(cur_mod_wdv_immovable, 3)
	cur_ter_gross_wdv_vehicle += round(cur_mod_wdv_vehicle, 3)
	prev_summary_result = run(
		"Lease Summary Report",
		filters={
			"company_name": company_name,
			"fin_start_year": int(fin_start_year) - 1,
			"fin_end_year": fin_start_year,
		},
	)
	prev_sum_rows = prev_summary_result.get("result")
	prev_sum_df = pd.DataFrame(prev_sum_rows)
	for _, row in prev_sum_df.iterrows():
		# prev_security_deposit = frappe.get_value(
		# 	"Lease Management", {"name": row["lease_id"]}, "security_deposit"
		# )
		# if prev_security_deposit == "Paid":
		# 	prev_sd_leases.append(row["lease_id"])
		if row["termination_rou"] != 0 and (
			isinstance(row["termination_rou"], int) or isinstance(row["termination_rou"], float)
		):
			prev_terminated_leases.append(row["lease_id"])
		if row["modification_rou"] != 0 and (
			isinstance(row["modification_rou"], int) or isinstance(row["modification_rou"], float)
		):
			prev_type_of_asset = frappe.get_value(
				"Lease Management", {"name": row["lease_id"]}, "type_of_asset"
			)
			if prev_type_of_asset == "Immovable":
				prev_mod_wdv_immovable += round(row["modification_rou"], 3)
			else:
				prev_mod_wdv_vehicle += round(row["modification_rou"], 3)
	if len(prev_terminated_leases) > 0:
		(
			prev_ter_acc_deprec_vehicle,
			prev_ter_acc_deprec_immovable,
			prev_ter_gross_wdv_vehicle,
			prev_ter_gross_wdv_immovable,
		) = get_terminated_lease_data(prev_terminated_leases)
	prev_ter_gross_wdv_immovable += round(prev_mod_wdv_immovable, 3)
	prev_ter_gross_wdv_vehicle += round(prev_mod_wdv_vehicle, 3)
	cur_result = run(
		"Journal Entries Report",
		filters={
			"company_name": company_name,
			"fin_start_year": fin_start_year,
			"fin_end_year": fin_end_year,
		},
	)
	rows = cur_result.get("result")
	df = pd.DataFrame(rows)
	if not df.empty and len(df) > 15:
		cur_depre_immovable = round(df.iloc[15]["debit"], 3)
		cur_depre_vehicle = round(df.iloc[16]["debit"], 3)
		cur_add_immovable = round(df.iloc[5]["debit"], 3)
		cur_add_vehicle = round(df.iloc[6]["debit"], 3)
	else:
		cur_depre_immovable = 0
		cur_depre_vehicle = 0
		cur_add_immovable = 0
		cur_add_vehicle = 0
	# cur_ter_immovable = round(df.iloc[2]["credit"],3)
	# cur_ter_vehicle = round(df.iloc[3]["credit"],3)
	# frappe.msgprint(str(cur_depre))
	# if len(cur_sd_leases)>0:
	# 	report_data = run("Security Deposit Calculation",filters={"lease_id":cur_sd_leases[0]})
	# 	rows = report_data.get("result", [])
	# 	filtered = [row for row in rows if getdate(row.get("to_date")) == getdate("2025-03-31")]
	# 	frappe.msgprint("filtered"+str(filtered))
	prev_result = run(
		"Journal Entries Report",
		filters={
			"company_name": company_name,
			"fin_start_year": int(fin_start_year) - 1,
			"fin_end_year": fin_start_year,
		},
	)
	prev_rows = prev_result.get("result")
	prev_df = pd.DataFrame(prev_rows)
	# frappe.msgprint("fin_start_year="+str(fin_start_year)+" "+str(get_prev_notes_record(company_name,fin_start_year)))
	# prev_gross_immovable,prev_gross_vehicle,prev_acc_depre_immovable,prev_acc_depre_vehicle= get_prev_notes_record(company_name,fin_start_year)
	if not prev_df.empty and len(prev_df) > 15:
		prev_depre_immovable = round(prev_df.iloc[15]["debit"], 3)
		prev_depre_vehicle = round(prev_df.iloc[16]["debit"], 3)
		prev_add_immovable = round(prev_df.iloc[5]["debit"], 3)
		prev_add_vehicle = round(prev_df.iloc[6]["debit"], 3)
	else:
		prev_depre_immovable = 0
		prev_depre_vehicle = 0
		prev_add_immovable = 0
		prev_add_vehicle = 0
	prev_gross_immovable = 0
	prev_gross_vehicle = 0
	prev_acc_depre_immovable = 0
	prev_acc_depre_vehicle = 0
	res = frappe.get_value(
		"Previous Lease Note Details",
		{"company": company_name, "financial_start_year": int(fin_start_year) - 1},
		[
			"gross_amount_immovable",
			"accumulated_amortization_immovable",
			"gross_amount_vehicle",
			"accumulated_amortization_vehicle",
			"gross_additions_immovable",
			"gross_additions_vehicle",
			"gross_disposals_immovable",
			"gross_disposals_vehicle",
			"accumulated_amortization_at_year_ended_immovable",
			"accumulated_amortization_at_year_ended_vehicle",
			"accumulated_amortization_disposals_immovable",
			"accumulated_amortization_disposals_vehicle",
		],
		as_dict=True,
	)
	if res:
		prev_gross_immovable = float(res.gross_amount_immovable)
		prev_gross_vehicle = float(res.gross_amount_vehicle)
		prev_add_immovable = float(res.gross_additions_immovable)
		prev_add_vehicle = float(res.gross_additions_vehicle)
		prev_ter_gross_wdv_immovable = float(res.gross_disposals_immovable)
		prev_ter_gross_wdv_vehicle = float(res.gross_disposals_vehicle)
		prev_acc_depre_immovable = float(res.accumulated_amortization_immovable)
		prev_acc_depre_vehicle = float(res.accumulated_amortization_vehicle)
		prev_depre_immovable = float(res.accumulated_amortization_at_year_ended_immovable)
		prev_depre_vehicle = float(res.accumulated_amortization_at_year_ended_vehicle)
		prev_ter_acc_deprec_immovable = float(res.accumulated_amortization_disposals_immovable)
		prev_ter_acc_deprec_vehicle = float(res.accumulated_amortization_disposals_vehicle)
	# if filters.get("prev_gross_immovable"):
	# 	prev_gross_immovable = round(float(filters.get("prev_gross_immovable")), 3)
	# if filters.get("prev_gross_vehicle"):
	# 	prev_gross_vehicle = round(float(filters.get("prev_gross_vehicle")), 3)
	# if filters.get("prev_acc_depre_immovable"):
	# 	prev_acc_depre_immovable = round(float(filters.get("prev_acc_depre_immovable")), 3)
	# if filters.get("prev_acc_depre_vehicle"):
	# 	prev_acc_depre_vehicle = round(float(filters.get("prev_acc_depre_vehicle")), 3)
	prev_gross_at_immovable = prev_gross_immovable + prev_add_immovable - prev_ter_gross_wdv_immovable
	prev_gross_at_vehicle = prev_gross_vehicle + prev_add_vehicle - prev_ter_gross_wdv_vehicle
	prev_gross_at_total = prev_gross_at_immovable + prev_gross_at_vehicle
	prev_acc_depre_upto_immovable = (
		prev_acc_depre_immovable + prev_depre_immovable - prev_ter_acc_deprec_immovable
	)
	prev_acc_depre_upto_vehicle = prev_acc_depre_vehicle + prev_depre_vehicle - prev_ter_acc_deprec_vehicle
	prev_net_immovable = prev_gross_at_immovable - prev_acc_depre_upto_immovable
	prev_net_vehicle = prev_gross_at_vehicle - prev_acc_depre_upto_vehicle
	# prev_ter_immovable = round(prev_df.iloc[2]["credit"],3)
	# prev_ter_vehicle = round(prev_df.iloc[3]["credit"],3)

	prev_fin_year = int(fin_start_year) - 1
	prev_fin_start_dt = date(prev_fin_year, 4, 1)
	prev_fin_end_dt = date(fin_start_year, 3, 31)
	prev_fin_start = "As at " + get_formatted_date(prev_fin_start_dt)
	prev_fin_end = "As at " + get_formatted_date(prev_fin_end_dt)
	cur_fin_end_dt = date(fin_end_year, 3, 31)
	cur_fin_end = "As at " + get_formatted_date(cur_fin_end_dt)
	cur_gross_at_immovable = prev_gross_at_immovable + cur_add_immovable - cur_ter_gross_wdv_immovable
	cur_gross_at_vehicle = prev_gross_at_vehicle + cur_add_vehicle - cur_ter_gross_wdv_vehicle
	cur_gross_at_total = cur_gross_at_immovable + cur_gross_at_vehicle
	cur_acc_depre_upto_immovable = (
		prev_acc_depre_upto_immovable + cur_depre_immovable - cur_ter_acc_deprec_immovable
	)
	cur_acc_depre_upto_vehicle = prev_acc_depre_upto_vehicle + cur_depre_vehicle - cur_ter_acc_deprec_vehicle
	cur_net_immovable = cur_gross_at_immovable - cur_acc_depre_upto_immovable
	cur_net_vehicle = cur_gross_at_vehicle - cur_acc_depre_upto_vehicle

	# sd_amount_prev_immovable, sd_amount_prev_vehicle = get_sd_amount(
	# 	prev_sd_leases, int(fin_start_year) - 1, fin_start_year
	# )
	# sd_amount_cur_immovable, sd_amount_cur_vehicle = get_sd_amount(
	# 	cur_sd_leases, fin_start_year, fin_end_year
	# )

	# cur_add_immovable += sd_amount_cur_immovable
	# cur_add_vehicle += sd_amount_cur_vehicle
	# prev_add_immovable += sd_amount_prev_immovable
	# prev_add_vehicle += sd_amount_prev_vehicle

	# frappe.msgprint("cur_sd_leases="+str(cur_sd_leases)+" prev_sd_leases="+str(prev_sd_leases))
	# frappe.msgprint("cur_sd_leases="+ str(cur_sd_leases)+ " sd_amount_cur="+ str(sd_amount_cur_immovable)+ " "+ str(sd_amount_cur_vehicle)+ " prev_sd_leases="+ str(prev_sd_leases)+ " sd_amount_prev="+ str(sd_amount_prev_immovable)+ " "+ str(sd_amount_prev_vehicle))

	records = [
		{
			"particulars": "I. Gross Carrying Amount",
			"rou_immovable": "",
			"rou_vehicle": "",
			"total": "",
		},
		{
			"particulars": prev_fin_start,
			"rou_immovable": prev_gross_immovable,
			"rou_vehicle": prev_gross_vehicle,
			"total": +prev_gross_immovable + prev_gross_vehicle,
		},
		{
			"particulars": "Additions",
			"rou_immovable": prev_add_immovable,
			"rou_vehicle": prev_add_vehicle,
			"total": prev_add_immovable + prev_add_vehicle,
		},
		{
			"particulars": "Disposals, Transfers and Adjustments",
			"rou_immovable": prev_ter_gross_wdv_immovable,
			"rou_vehicle": prev_ter_gross_wdv_vehicle,
			"total": prev_ter_gross_wdv_immovable + prev_ter_gross_wdv_vehicle,
		},
		{
			"particulars": prev_fin_end,
			"rou_immovable": prev_gross_at_immovable,
			"rou_vehicle": prev_gross_at_vehicle,
			"total": prev_gross_at_total,
		},
		{
			"particulars": "Additions",
			"rou_immovable": cur_add_immovable,
			"rou_vehicle": cur_add_vehicle,
			"total": cur_add_immovable + cur_add_vehicle,
		},
		{
			"particulars": "Disposals, Transfers and Adjustments",
			"rou_immovable": cur_ter_gross_wdv_immovable,
			"rou_vehicle": cur_ter_gross_wdv_vehicle,
			"total": cur_ter_gross_wdv_immovable + cur_ter_gross_wdv_vehicle,
		},
		{
			"particulars": cur_fin_end,
			"rou_immovable": cur_gross_at_immovable,
			"rou_vehicle": cur_gross_at_vehicle,
			"total": cur_gross_at_total,
		},
		{
			"particulars": "II.  Accumulated Amortisation",
			"rou_immovable": "",
			"rou_vehicle": "",
			"total": "",
		},
		{
			"particulars": prev_fin_start,
			"rou_immovable": prev_acc_depre_immovable,
			"rou_vehicle": prev_acc_depre_vehicle,
			"total": prev_acc_depre_immovable + prev_acc_depre_vehicle,
		},
		{
			"particulars": "For the Year Ended " + get_formatted_date(prev_fin_end_dt),
			"rou_immovable": prev_depre_immovable,
			"rou_vehicle": prev_depre_vehicle,
			"total": prev_depre_immovable + prev_depre_vehicle,
		},
		{
			"particulars": "Disposals and Adjustments",
			"rou_immovable": prev_ter_acc_deprec_immovable,
			"rou_vehicle": prev_ter_acc_deprec_vehicle,
			"total": prev_ter_acc_deprec_immovable + prev_ter_acc_deprec_vehicle,
		},
		{
			"particulars": "Upto " + get_formatted_date(prev_fin_end_dt),
			"rou_immovable": prev_acc_depre_upto_immovable,
			"rou_vehicle": prev_acc_depre_upto_vehicle,
			"total": prev_acc_depre_upto_immovable + prev_acc_depre_upto_vehicle,
		},
		{
			"particulars": "For the Year Ended " + get_formatted_date(cur_fin_end_dt),
			"rou_immovable": cur_depre_immovable,
			"rou_vehicle": cur_depre_vehicle,
			"total": cur_depre_immovable + cur_depre_vehicle,
		},
		{
			"particulars": "Disposals and Adjustments",
			"rou_immovable": cur_ter_acc_deprec_immovable,
			"rou_vehicle": cur_ter_acc_deprec_vehicle,
			"total": cur_ter_acc_deprec_immovable + cur_ter_acc_deprec_vehicle,
		},
		{
			"particulars": "Upto " + get_formatted_date(cur_fin_end_dt),
			"rou_immovable": cur_acc_depre_upto_immovable,
			"rou_vehicle": cur_acc_depre_upto_vehicle,
			"total": cur_acc_depre_upto_immovable + cur_acc_depre_upto_vehicle,
		},
		{
			"particulars": "III.  Net Carrying Amount",
			"rou_immovable": "",
			"rou_vehicle": "",
			"total": "",
		},
		{
			"particulars": prev_fin_end,
			"rou_immovable": prev_net_immovable,
			"rou_vehicle": prev_net_vehicle,
			"total": prev_net_immovable + prev_net_vehicle,
		},
		{
			"particulars": cur_fin_end,
			"rou_immovable": cur_net_immovable,
			"rou_vehicle": cur_net_vehicle,
			"total": cur_net_immovable + cur_net_vehicle,
		},
	]
	data.extend(records)

	return columns, data

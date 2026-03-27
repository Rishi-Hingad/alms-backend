# Copyright (c) 2026, Shradha_Siddhi and contributors
# For license information, please see license.txt

from datetime import date, datetime, timedelta

import frappe
import pandas as pd
from frappe import _ as translate
from frappe.desk.query_report import run

from leasemanagement.api.utils import get_formatted_date, get_terminated_lease_data


def execute(filters=None):
	if not filters:
		return [], []

	company_name = filters.get("company_name")

	if not company_name:
		frappe.throw(translate("Please select a Company."))

	fin_start_year = filters.get("fin_start_year")
	fin_end_year = filters.get("fin_end_year")

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
	cur_ter_gross_wdv_immovable = 0
	cur_ter_gross_wdv_vehicle = 0
	cur_ter_acc_deprec_immovable = 0
	cur_ter_acc_deprec_vehicle = 0
	prev_ter_acc_deprec_vehicle = 0
	prev_ter_acc_deprec_immovable = 0
	prev_ter_gross_wdv_vehicle = 0
	prev_ter_gross_wdv_immovable = 0
	for _, row in sum_df.iterrows():
		if row["termination_rou"] != 0 and (
			isinstance(row["termination_rou"], int) or isinstance(row["termination_rou"], float)
		):
			cur_terminated_leases.append(row["lease_id"])
	if len(cur_terminated_leases) > 0:
		(
			cur_ter_acc_deprec_vehicle,
			cur_ter_acc_deprec_immovable,
			cur_ter_gross_wdv_vehicle,
			cur_ter_gross_wdv_immovable,
		) = get_terminated_lease_data(cur_terminated_leases)
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
		if row["termination_rou"] != 0 and (
			isinstance(row["termination_rou"], int) or isinstance(row["termination_rou"], float)
		):
			prev_terminated_leases.append(row["lease_id"])
	if len(prev_terminated_leases) > 0:
		(
			prev_ter_acc_deprec_vehicle,
			prev_ter_acc_deprec_immovable,
			prev_ter_gross_wdv_vehicle,
			prev_ter_gross_wdv_immovable,
		) = get_terminated_lease_data(prev_terminated_leases)
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

	cur_depre_immovable = round(df.iloc[15]["debit"], 3)
	cur_depre_vehicle = round(df.iloc[16]["debit"], 3)
	cur_add_immovable = round(df.iloc[5]["debit"], 3)
	cur_add_vehicle = round(df.iloc[6]["debit"], 3)
	# cur_ter_immovable = round(df.iloc[2]["credit"],3)
	# cur_ter_vehicle = round(df.iloc[3]["credit"],3)
	# frappe.msgprint(str(cur_depre))
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
	prev_depre_immovable = round(prev_df.iloc[15]["debit"], 3)
	prev_depre_vehicle = round(prev_df.iloc[16]["debit"], 3)
	prev_add_immovable = round(prev_df.iloc[5]["debit"], 3)
	prev_add_vehicle = round(prev_df.iloc[6]["debit"], 3)
	prev_gross_immovable = 0
	prev_gross_vehicle = 0
	prev_gross_at_immovable = prev_gross_immovable + prev_add_immovable - prev_ter_gross_wdv_immovable
	prev_gross_at_vehicle = prev_gross_vehicle + prev_add_vehicle - prev_ter_gross_wdv_vehicle
	prev_gross_at_total = prev_gross_at_immovable + prev_gross_at_vehicle
	prev_acc_depre_immovable = 0
	prev_acc_depre_vehicle = 0
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

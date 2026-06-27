# Copyright (c) 2026, Shradha_Siddhi and contributors
# For license information, please see license.txt

import math
from datetime import date, datetime

import frappe
import pandas as pd
from frappe import _ as translate
from frappe.desk.query_report import run


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
	if not frappe.db.exists("GL Code Master", {"company": company_name}):
		frappe.throw(f"GL Code doesn't exist for the selected company: {company_name}")

	gl_code_doc = frappe.get_doc("GL Code Master", company_name)

	result = run(
		"Lease Summary Report",
		filters={
			"company_name": company_name,
			"fin_start_year": fin_start_year,
			"fin_end_year": fin_end_year,
		},
	)
	rows = result.get("result")
	df = pd.DataFrame(rows)

	interest = df["interest"].tolist()
	rent_paid = df["rent_paid"].tolist()
	ter_lease_lia = df["termination_lease_liability"].tolist()

	total_interest = 0
	total_rent = 0
	total_ter_lease_lia = 0
	immovable_depreciation = 0
	car_depreciation = 0
	immovable_additions = 0
	car_additions = 0
	immovable_ter_rou = 0
	car_ter_rou = 0

	for i in range(len(interest)):
		val = interest[i]
		if isinstance(val, int) or isinstance(val, float):
			total_interest += val
		if isinstance(rent_paid[i], int) or isinstance(rent_paid[i], float):
			total_rent += rent_paid[i]
		if isinstance(ter_lease_lia[i], int) or isinstance(ter_lease_lia[i], float):
			total_ter_lease_lia += ter_lease_lia[i]
	total_ter_lease_lia = -(total_ter_lease_lia)

	for _, row in df.iterrows():
		lease_id = row.get("lease_id")
		depreciation = row.get("depreciation") or 0
		additions_rou = row.get("additions_rou_asset") or 0
		ter_rou = row.get("termination_rou") or 0

		if not lease_id or not isinstance(depreciation, int | float):
			continue
		if not lease_id or not isinstance(additions_rou, int | float):
			continue
		if not lease_id or not isinstance(ter_rou, int | float):
			continue
		type_of_asset = frappe.get_value("Lease Management", lease_id, "type_of_asset")
		if type_of_asset == "Immovable":
			immovable_depreciation += depreciation
			immovable_additions += additions_rou
			immovable_ter_rou += ter_rou
		if type_of_asset == "Car":
			car_depreciation += depreciation
			car_additions += additions_rou
			car_ter_rou += ter_rou
	car_ter_rou = -(car_ter_rou)
	immovable_ter_rou = -(immovable_ter_rou)
	gain_loss_derecognition = total_ter_lease_lia - car_ter_rou - immovable_ter_rou
	# frappe.msgprint("car_ter_rou="+str(car_ter_rou)+" immovable_ter_rou"+str((immovable_ter_rou))+"||=gain_loss_derecognition"+str(gain_loss_derecognition))
	# frappe.msgprint(str(total_ter_lease_lia)+"--"+str(gain_loss_derecognition+car_ter_rou+immovable_ter_rou))
	data = []
	columns = [
		{"label": translate("GL No."), "fieldname": "gl_no", "fieldtype": "Int", "width": 120},
		{"label": translate("Particulars"), "fieldname": "particulars", "fieldtype": "Data", "width": 300},
		{
			"label": translate("Debit"),
			"fieldname": "debit",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": translate("Credit"),
			"fieldname": "credit",
			"fieldtype": "Currency",
			"width": 200,
			"precision": 2,
		},
		{
			"label": translate("Remarks"),
			"fieldname": "remark",
			"fieldtype": "Data",
			"width": 300,
		},
	]
	records = [
		{
			"gl_no": gl_code_doc.lease_liability,
			"particulars": "Lease Liability",
			"debit": total_ter_lease_lia,
			"credit": "",
			"remark": "De-recognition of Terminated Lease's",
		},
		{
			"gl_no": "",
			"particulars": "Gain/Loss on De-recognition of Leased Asset",
			"debit": "",
			"credit": gain_loss_derecognition,
		},
		{
			"gl_no": gl_code_doc.rou_asset_immovable,
			"particulars": "ROU Asset (Immovable Property)",
			"debit": "",
			"credit": immovable_ter_rou,
		},
		{
			"gl_no": gl_code_doc.rou_asset_vehicle,
			"particulars": "ROU Asset (Vehicle)",
			"debit": "",
			"credit": car_ter_rou,
		},
		{
			"gl_no": "",
			"particulars": "",
			"debit": "",
			"credit": "",
		},
		{
			"gl_no": gl_code_doc.rou_asset_immovable,
			"particulars": "ROU Asset (Immovable Property)",
			"debit": immovable_additions,
			"credit": "",
			"remark": "Recognition of New Lease's",
		},
		{
			"gl_no": gl_code_doc.rou_asset_vehicle,
			"particulars": "ROU Asset (Vehicle)",
			"debit": car_additions,
			"credit": "",
		},
		{
			"gl_no": gl_code_doc.lease_liability,
			"particulars": "Lease Liability",
			"debit": "",
			"credit": immovable_additions + car_additions,
		},
		{
			"gl_no": "",
			"particulars": "",
			"debit": "",
			"credit": "",
		},
		{
			"gl_no": gl_code_doc.lease_liability,
			"particulars": "Lease Liability",
			"debit": total_rent,
			"credit": "",
			"remark": "Actual Rent Paid",
		},
		{
			"gl_no": gl_code_doc.rent_expenses,
			"particulars": "Rent Expenses IND AS",
			"debit": "",
			"credit": total_rent,
		},
		{
			"gl_no": "",
			"particulars": "",
			"debit": "",
			"credit": "",
		},
		{
			"gl_no": gl_code_doc.interest_lease_liability,
			"particulars": "Interest on Lease Liability",
			"debit": total_interest,
			"credit": "",
			"remark": "Interest on Lease Liability",
		},
		{
			"gl_no": gl_code_doc.lease_liability,
			"particulars": "Lease Liability",
			"debit": "",
			"credit": total_interest,
		},
		{
			"gl_no": "",
			"particulars": "",
			"debit": "",
			"credit": "",
		},
		{
			"gl_no": gl_code_doc.depreciation_immovable,
			"particulars": "Depreciation - Immovable Property",
			"debit": immovable_depreciation,
			"credit": "",
			"remark": "Depreciation on ROU Asset",
		},
		{
			"gl_no": gl_code_doc.depreciation_vehicle,
			"particulars": "Depreciation - Vehicle",
			"debit": car_depreciation,
			"credit": "",
		},
		{
			"gl_no": gl_code_doc.rou_asset_immovable,
			"particulars": "ROU Asset (Immovable Property)",
			"debit": "",
			"credit": immovable_depreciation,
		},
		{
			"gl_no": gl_code_doc.rou_asset_vehicle,
			"particulars": "ROU Asset (Vehicle)",
			"debit": "",
			"credit": car_depreciation,
		},
	]
	data.extend(records)

	return columns, data

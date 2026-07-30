# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import math
from calendar import monthrange
from datetime import date, datetime

import frappe
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
		{"label": _("Status"), "fieldname": "lease_status", "fieldtype": "Data", "width": 150},
		{"label": _("Lease"), "fieldname": "lease_id", "fieldtype": "Data", "width": 240},
		{"label": _("Vendor"), "fieldname": "vendor", "fieldtype": "Data", "width": 120},
		{
			"label": _("Asset Description"),
			"fieldname": "asset_description",
			"fieldtype": "Data",
			"width": 200,
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
			car_desc = frappe.get_doc("Vehicle Details", lease_doc.car_description)
		modified_start = None
		terminated_on = None
		terminated = False
		modified = False
		# frappe.msgprint(str(lease_status)+"__"+str(lease_doc.is_modified)+lease.name)
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

			# if lease_status=="Terminated" and lease_doc.is_modified==1:
		msdate = date(int(fin_start_year), 4, 1)
		# medate = date(int(fin_end_year), 3, 1)
		medate = date(int(fin_end_year), 3, 31)

		if modified_start is not None:
			if modified_start > msdate and modified_start <= medate:
				modified = True
			else:
				modified_start = None

		if terminated_on is not None:
			if lease_doc.termination_date > msdate and lease_doc.termination_date <= medate:
				terminated = True
			else:
				terminated_on = None
			# frappe.msgprint(str(modified_start)+"__"+str(lease_doc.is_modified)+lease.name+" modified="+str(modified_start)+" "+str(modified)+" terminated="+str(terminated)+" "+str(lease_doc.termination_date>msdate)+" "+str(lease_doc.termination_date <= medate) +" "+str(medate))
		lease_end = None
		if lease_doc.agreement_end_date:
			lease_end = getdate(lease_doc.agreement_end_date)

		if lease_end and lease_end < msdate:
			continue

		if lease_doc.calculation_rate_type == "Daily Rate":
			lreport = "Lease Report"
		else:
			lreport = "Lease Report Monthly (With Escalation)"

		prev_res = run(lreport, filters={"docname": lease.name, "sum_modified": None})
		prev_rows = prev_res.get("result", [])
		
		def to_date(d):
			if isinstance(d, str):
				return getdate(d)
			elif isinstance(d, datetime):
				return d.date()
			elif isinstance(d, date):
				return d
			return None

		for r in prev_rows:
			r["month_start_date"] = to_date(r.get("month_start_date"))
			r["month_end_date"] = to_date(r.get("month_end_date"))

		if lease_doc.status == "Terminated":
			result = run(lreport, filters={"docname": lease.name, "sum_modified": terminated_on})
		else:
			result = run(lreport, filters={"docname": lease.name, "sum_modified": modified_start})
		rows = result.get("result", [])
		
		for r in rows:
			r["month_start_date"] = to_date(r.get("month_start_date"))
			r["month_end_date"] = to_date(r.get("month_end_date"))

		sdate = date(int(fin_start_year), 3, 31)
		edate = date(int(fin_end_year), 3, 31)
		mod_rou = 0
		mod_lia = 0
		ter_rou = 0
		ter_lia = 0

		if lease_end < edate:
			medate = date(lease_end.year, lease_end.month, lease_end.day)

		row_opening = [r for r in rows if r.get("month_end_date") == sdate]
		prev_row_opening = [r for r in prev_rows if r.get("month_end_date") == sdate]
		diff_calc_ter_mod = False
		diff_calc_ter_add = False

		if len(row_opening) == 1:
			opening_rou = row_opening[0].get("wdv", 0)
			opening_liability = row_opening[0].get("closing_liability", 0)
			if len(prev_row_opening) == 1 and row_opening[0].get("wdv") != prev_row_opening[0].get("wdv"):
				diff_calc_ter_mod = True
				opening_rou = prev_row_opening[0].get("wdv", 0)
				opening_liability = prev_row_opening[0].get("closing_liability", 0)
		else:
			opening_rou = 0
			opening_liability = 0
            
		if lease_doc.termination_date:
			if lease_doc.termination_date == edate:
				edate = date(edate.year, 4, 30)

		row_closing = [r for r in rows if r.get("month_end_date") == edate]
		if len(row_closing) == 1:
			closing_rou = row_closing[0].get("wdv", 0)
			closing_liability = row_closing[0].get("closing_liability", 0)
			if lease_end < edate:
				closing_rou = 0
				closing_liability = 0
		else:
			closing_rou = 0
			closing_liability = 0

		mlp_list, interest_list, depreciation_list = [], [], []
		for r in rows:
			d = r.get("month_start_date")
			if d and d >= msdate and d <= medate:
				mlp_list.append(r.get("mlp", 0))
				interest_list.append(r.get("interest_cost", 0))
				depreciation_list.append(r.get("depreciation", 0))

		if opening_rou == 0:
			if not lease_doc.is_modified:
				additions_rou_asset = rows[0].get("wdv", 0) if rows else 0
				if prev_rows and rows and prev_rows[0].get("wdv") != rows[0].get("wdv"):
					additions_rou_asset = prev_rows[0].get("wdv", 0)
					diff_calc_ter_add = True
				additions_lease_lia = additions_rou_asset
			else:
				additions_rou_asset = additions_lease_lia = 0
		else:
			additions_rou_asset = additions_lease_lia = 0
            
		total_rent_paid = 0
		total_interest_cost = 0
		total_depreciation = 0

		for i in range(len(mlp_list)):
			if isinstance(mlp_list[i], (int, float)) and not math.isnan(float(mlp_list[i])):
				total_rent_paid += mlp_list[i]
			if isinstance(interest_list[i], (int, float)) and not math.isnan(float(interest_list[i])):
				total_interest_cost += interest_list[i]
			if isinstance(depreciation_list[i], (int, float)) and not math.isnan(float(depreciation_list[i])):
				total_depreciation += depreciation_list[i]

		if modified:
			mod_rou = -(rows[0].get("wdv", 0) if rows else 0)
			mod_lia = -(rows[0].get("closing_liability", 0) if rows else 0)
			if diff_calc_ter_mod:
				mod_rou = -(opening_rou - total_depreciation)
				mod_lia = -(opening_liability + total_interest_cost - total_rent_paid)
		if (
			lease_status == "Modified"
			or (lease_status == "Terminated" and lease_doc.is_modified == 1)
			or ("Discarded" and lease_doc.is_modified == 1)
		):
			if opening_rou == 0 and opening_liability == 0:
				mod_rou = rows[0].get("wdv", 0) if rows else 0
				mod_lia = rows[0].get("closing_liability", 0) if rows else 0
				if diff_calc_ter_mod:
					mod_rou = opening_rou - total_depreciation
					mod_lia = opening_liability + total_interest_cost - total_rent_paid
		if terminated:
			ter_rou = -(rows[0].get("wdv", 0) if rows else 0)
			ter_lia = -(rows[0].get("closing_liability", 0) if rows else 0)
			if diff_calc_ter_mod:
				ter_rou = -(opening_rou - total_depreciation)
				ter_lia = -(opening_liability + total_interest_cost - total_rent_paid)
			if diff_calc_ter_add:
				ter_rou = -(additions_rou_asset - total_depreciation)
				ter_lia = -(additions_lease_lia + total_interest_cost - total_rent_paid)
			# frappe.msgprint(lease.name+" "+str(additions_rou_asset)+" "+str(opening_rou)+" "+str(round(total_depreciation,2))+" "+str(closing_rou)+" "+str(additions_rou_asset)+" "+str(mod_rou)+ " "+str(ter_rou))
		rou_check = opening_rou - total_depreciation - closing_rou + additions_rou_asset + mod_rou + ter_rou
		# frappe.msgprint("roucheck="+str(round(opening_rou,2) - round(total_depreciation,2) - round(closing_rou,2) + round(additions_rou_asset,2) + round(mod_rou,2) + round(ter_rou,2)))
		liability_check = (
			opening_liability
			+ total_interest_cost
			- total_rent_paid
			- closing_liability
			+ additions_lease_lia
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
					"lease_status": lease_doc.status,
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
					"check_rou": round(rou_check),
					"check_liability": round(liability_check),
					"modification_rou": mod_rou,
					"modification_lease_liability": mod_lia,
					"termination_rou": ter_rou,
					"termination_lease_liability": ter_lia,
				}
			)
		else:
			data.append(
				{
					"lease_status": lease_doc.status,
					"lease_id": lease.name,
					"vendor": car_desc.vendor_company,
					"asset_description": car_desc.employee_code_and_name,
					"rou_opening": opening_rou,
					"rou_closing": closing_rou,
					"liability_opening": opening_liability,
					"liability_closing": closing_liability,
					"rent_paid": total_rent_paid,
					"interest": total_interest_cost,
					"depreciation": total_depreciation,
					"additions_rou_asset": additions_rou_asset,
					"additions_lease_liability": additions_lease_lia,
					"check_rou": round(rou_check),
					"check_liability": round(liability_check),
					"modification_rou": mod_rou,
					"modification_lease_liability": mod_lia,
					"termination_rou": ter_rou,
					"termination_lease_liability": ter_lia,
				}
			)
	data.append(
		{
			"lease_status": "",
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

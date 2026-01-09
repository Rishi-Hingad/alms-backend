# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import calendar
import io
from calendar import monthrange
from collections import Counter
from datetime import date, datetime, time, timedelta

import frappe
import pandas as pd
from dateutil.relativedelta import relativedelta
from frappe import _, db
from frappe.model.document import Document
from frappe.utils import now_datetime, nowdate
from frappe.utils.file_manager import save_file
from openpyxl.utils import get_column_letter

from lms.api.utils import get_mlp


def get_diff_years(start_date, end_date):
	arg_sd = start_date
	arg_ed = end_date + timedelta(days=1)
	diff_years = relativedelta(arg_ed, arg_sd)
	diff_years = int(str(diff_years.years))
	return diff_years


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


def get_n(current_date, diff_annually):
	n_prior = 0
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
	return n_prior


def date_increment(current_date, diff_annually, mid_diff_annually, esc_bd_end_date):
	if current_date.month == 12:
		if diff_annually and not mid_diff_annually:
			current_date = datetime(current_date.year + 1, 1, current_date.day) - relativedelta(days=1)
		elif diff_annually and mid_diff_annually:
			current_date = datetime(current_date.year + 1, 1, esc_bd_end_date.day) - relativedelta(days=1)
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
		else:
			current_date = datetime(current_date.year, current_date.month + 1, 1)
	return current_date


# ====================================================================================


@frappe.whitelist()
def get_all_active_lease_rent_data():
	today = frappe.utils.nowdate()
	if isinstance(today, str):
		today = datetime.strptime(today, "%Y-%m-%d")
	current_month = today.strftime("%Y-%m")
	previous_month = (today - relativedelta(months=1)).strftime("%Y-%m")
	next_month = (today + relativedelta(months=1)).strftime("%Y-%m")
	leases = frappe.get_all(
		"Lease Management",
		filters={"agreement_start_date": ("<=", today), "agreement_end_date": (">=", today)},
		fields=["name"],
	)
	monthly_totals = {"Previous Month": 0.0, "Current Month": 0.0, "Next Month": 0.0}

	for lease in leases:
		lease_doc = frappe.get_doc("Lease Management", lease.name)
		timeline_l = lease_doc.get_lease_rent_timeline()

		monthly_totals["Previous Month"] += timeline_l.get(previous_month, 0)
		monthly_totals["Current Month"] += timeline_l.get(current_month, 0)
		monthly_totals["Next Month"] += timeline_l.get(next_month, 0)

	return monthly_totals


@frappe.whitelist()
def bulk_update_agreement_status():
	today = nowdate()

	# updated_count = frappe.db.sql(
	# 	"""
	# 	UPDATE `tabLease Management`
	# 	SET status = 'Agreement Expired'
	# 	WHERE agreement_end_date < %s
	# 	AND status != 'Agreement Expired'
	# """,
	# 	(today,),
	# )
	expired_docs = frappe.get_all(
		"Lease Management",
		filters={"agreement_end_date": ["<", today], "status": ["!=", "Agreement Expired"]},
		fields=["name"],
	)
	for name in expired_docs:
		frappe.db.set_value("Lease Management", name, "status", "Agreement Expired")

	frappe.db.commit()
	# return {"updated": True, "count": updated_count}
	return len(expired_docs)


# @frappe.whitelist()
# def has_expired_agreements():
# 	today = nowdate()
# 	count = frappe.db.count(
# 		"Lease Management", {"status": ["!=", "Agreement Expired"], "agreement_end_date": ["<", today]}
# 	)

# 	# return {"needs_update": count > 0, "count": count}
# 	return count


@frappe.whitelist()
def delete_invoice_attachment(parent_doctype, parent_name, attachment_name, delete_file=False):
	"""
	Deletes a child row Invoice Attachment (attachment_name) under parent_name.
	If delete_file=True and we can map file_docname, also delete the File doc.
	"""
	# simple guards
	if not frappe.has_permission(parent_doctype, ptype="write", doc=parent_name):
		frappe.throw(_("Not permitted"))

	# delete the child row doc (Invoice Attachment)
	try:
		# grab file_docname before deleting
		file_docname = frappe.db.get_value("Invoice Attachments", attachment_name, "file_docname")
		frappe.delete_doc("Invoice Attachments", attachment_name, force=True)
		if delete_file and file_docname:
			# ensure File exists and is safe to delete
			try:
				frappe.delete_doc("File", file_docname, force=True)
			except Exception:
				# swallow or log
				frappe.log_error(f"Could not delete File {file_docname}")
		return "ok"
	except Exception as e:
		frappe.log_error(frappe.get_traceback())
		frappe.throw(_("Could not delete attachment: {0}").format(e))


@frappe.whitelist()
def get_invoice_attachments(filters=None):
	if not filters:
		return []

	# always parse, since frappe.call sends args as strings
	filters = frappe.parse_json(filters)

	return frappe.get_all(
		"Invoice Attachments", filters=filters, fields=["name", "file", "uploaded_by", "uploaded_on"]
	)


# ===================================================================================
class LeaseManagement(Document):
	# pass
	def autoname(self):
		# start_date = datetime.strptime(self.agreement_start_date, "%Y-%m-%d").date()
		# end_date = datetime.strptime(self.agreement_end_date, "%Y-%m-%d").date()

		start_date = self.agreement_start_date
		if isinstance(start_date, str):
			start_date = datetime.strptime(start_date, "%Y-%m-%d")
		if isinstance(start_date, date) and not isinstance(start_date, datetime):
			start_date = datetime.combine(start_date, datetime.min.time())
		start_date = start_date.date()

		end_date = self.agreement_end_date
		if isinstance(end_date, str):
			end_date = datetime.strptime(end_date, "%Y-%m-%d")
		if isinstance(end_date, date) and not isinstance(end_date, datetime):
			end_date = datetime.combine(end_date, datetime.min.time())
		end_date = end_date.date()

		start_month = calendar.month_abbr[start_date.month].upper()
		start_year = str(start_date.year)[-2:]

		end_month = calendar.month_abbr[end_date.month].upper()
		end_year = str(end_date.year)[-2:]

		full_seq = frappe.model.naming.getseries("LMS-", 4)

		seq_num_str = full_seq.replace("LMS-", "")
		seq_num = int(seq_num_str)

		self.name = f"LMS-{start_month}{start_year}_{end_month}{end_year}-{seq_num}"

	def validate(self):
		# validate property decription field
		self.validate_property_details()
		self.validate_car_description_details()

		if self.invoice_details and len(self.invoice_details) > 0:
			self.validate_invoice_details()
		for row in self.escalation:
			# if row.escalation_type=='Per Annum' and not row.rate:
			# 	frappe.throw("Rate Field Required in Escalation")
			if row.escalation_type == "Based On Dates" and not row.start_date:
				frappe.throw("Start Date Field Required in Escalation")
			if row.escalation_type == "Based On Dates" and not row.end_date:
				frappe.throw("End Date Field Required in Escalation")
			# if row.escalation_type=='Based On Dates' and not row.monthly_rent:
			# 	frappe.throw("Monthly Rent Field Required in Escalation")
			# if row.escalation_type=='Per Annum and Fixed Amount' and not row.rate:
			# 	frappe.throw("Rate Field Required in Escalation")
			# if row.escalation_type=='Per Annum and Fixed Amount' and not row.fixed_amount:
			# 	frappe.throw("Fixed Amount Field Required in Escalation")
		invoice_row_names = [r.custom_row_id for r in self.invoice_details]
		for a in list(self.invoice_attachments):
			if a.invoice_row not in invoice_row_names:
				# remove it
				frappe.db.delete("Invoice Attachments", a.name)

		for idx, row in enumerate(self.invoice_details, start=1):
			if row.from_date and row.to_date:
				from_str = frappe.utils.formatdate(row.from_date, "dd-MM-yyyy")
				to_str = frappe.utils.formatdate(row.to_date, "dd-MM-yyyy")
				row.custom_row_id = f"{self.name}-row-{idx}-{from_str}-to-{to_str}"

	def before_insert(self):
		# On new record creation, populate invoice_details
		if self.agreement_start_date and self.agreement_end_date:
			# self.populate_invoice_details()
			if not self.escalation and len(self.escalation) == 0:
				self.populate_escalation_record()

	def validate_car_description_details(self):
		if not self.car_description:
			return

		car_doc = frappe.get_doc("Car Description Master", self.car_description)

		if car_doc.vendor != self.vendor:
			frappe.throw(
				f"Vendor Mismatch:<br>"
				f"Selected Car Description belongs to Vendor <b>{car_doc.vendor}</b> "
				f"but you have selected <b>{self.vendor}</b>."
			)

	def validate_property_details(self):
		if not self.property_description:
			return

		property_doc = frappe.get_doc("Property Master", self.property_description)

		if property_doc.vendor != self.vendor:
			frappe.throw(
				f"Vendor Mismatch:<br>"
				f"Selected Property belongs to Vendor <b>{property_doc.vendor}</b> "
				f"but you have selected <b>{self.vendor}</b>."
			)

		# if property_doc.type_of_asset != self.type_of_asset:
		# 	frappe.throw(
		# 		f"Type of Asset mismatch:<br>"
		# 		f"Selected Property has Type of Asset <b>{property_doc.type_of_asset}</b> "
		# 		f"but you selected <b>{self.type_of_asset}</b>."
		# 	)

	def populate_escalation_record(self):
		# start_date = datetime.strptime(self.agreement_start_date, "%Y-%m-%d").date()
		if isinstance(self.agreement_start_date, str):
			start_date = datetime.strptime(self.agreement_start_date, "%Y-%m-%d").date()
		else:
			start_date = self.agreement_start_date
		# end_date = datetime.strptime(self.agreement_end_date, "%Y-%m-%d").date()
		if isinstance(self.agreement_start_date, str):
			end_date = datetime.strptime(self.agreement_end_date, "%Y-%m-%d").date()
		else:
			end_date = self.agreement_end_date
		# self.escalation=[]
		# if self.escalation and len(self.escalation)==0:
		self.append(
			"escalation",
			{
				"escalation_type": "Per Annum",
				"start_date": start_date,
				"end_date": end_date,
				"monthly_rent": 0,
				"rate": 0,
				"fixed_amount": 0,
			},
		)

	def get_lease_rent_timeline(self):
		doc = frappe.get_doc("Lease Management", self.name)
		mlp = float(doc.monthly_rent)
		start_date = doc.agreement_start_date
		end_date = doc.agreement_end_date
		if isinstance(doc.agreement_start_date, datetime):
			start_date = doc.agreement_start_date
		else:
			start_date = datetime.combine(doc.agreement_start_date, datetime.min.time())

		if isinstance(doc.agreement_end_date, datetime):
			end_date = doc.agreement_end_date
		else:
			end_date = datetime.combine(doc.agreement_end_date, datetime.min.time())

		diff_years = get_diff_years(start_date, end_date)

		timeline = {}
		current_date = start_date
		cnt = 0
		famt_prev_mlp1 = 0
		prev_mlp_escl = None

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

		if len(edates_pannum) > 0:
			if edates_pannum[0] != edates_pannum[0].replace(day=1) and current_date != current_date.replace(
				day=1
			):
				diff_annually = True
		if len(edates_pafa) > 0:
			if edates_pafa[0] != edates_pafa[0].replace(day=1) and current_date != current_date.replace(
				day=1
			):
				diff_annually = True
		cnt_keys = len(dict_ed_bdates)
		dict_new = {}
		common_month = []
		common_dict = {}
		prev_mlp_next = {}
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
								mlp_escl = mlp_escl * n / total_days_of_month
								total_mlp_escl += mlp_escl
						common_dict[cmonth] = total_mlp_escl
		if esc_bd_end_date is not None and esc_bd_end_date != esc_bd_end_date.replace(day=1):
			mid_diff_annually = True
		else:
			mid_diff_annually = False
		# Calculate Previous Closing Liability from Present Value and Total Days
		while current_date <= end_date:
			cnt += 1
			if diff_annually:
				if cnt > 1:
					if current_date != end_date:
						current_date = current_date + timedelta(days=1)
			month_start, month_end, month_start2, month_end2, total_days_of_month = get_month_details(
				current_date
			)
			n_prior = get_n(current_date, diff_annually)

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

			if n_prior < total_days_of_month or n < total_days_of_month:
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
				timeline[current_date.date().strftime("%Y-%m")] = round(mlp, 3)
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
				timeline[current_date.date().strftime("%Y-%m")] = round(mlp, 3)
				if mrent == 0 and rate == 0 and famt == 0 and escalation:
					mlp = prev_mlp
			if month_end > end_date:
				month_end = end_date

			if esc_bd_end_date is not None and esc_bd_end_date != esc_bd_end_date.replace(day=1):
				if current_date.month == 12:
					next_current_date = datetime(current_date.year + 1, 1, 1)
				else:
					next_current_date = datetime(current_date.year, current_date.month + 1, 1)
				if next_current_date.strftime("%Y-%m") == esc_bd_end_date.strftime("%Y-%m"):
					diff_annually = True
			current_date = date_increment(current_date, diff_annually, mid_diff_annually, esc_bd_end_date)
			if current_date.strftime("%Y-%m") == end_date.strftime("%Y-%m"):
				current_date = current_date.replace(day=1)
		return timeline

	def get_lease_monthly_data(self):
		doc = frappe.get_doc("Lease Management", self.name)
		mlp = float(doc.monthly_rent)
		start_date = doc.agreement_start_date
		end_date = doc.agreement_end_date
		if isinstance(doc.agreement_start_date, datetime):
			start_date = doc.agreement_start_date
		else:
			start_date = datetime.combine(doc.agreement_start_date, datetime.min.time())

		if isinstance(doc.agreement_end_date, datetime):
			end_date = doc.agreement_end_date
		else:
			end_date = datetime.combine(doc.agreement_end_date, datetime.min.time())
		diff_years = get_diff_years(start_date, end_date)
		monthly_data = {}
		current_date = start_date
		cnt = 0
		prev_mlp_escl = None
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

		# Calculate Previous Closing Liability from Present Value and Total Days
		while current_date <= end_date:
			cnt += 1
			if diff_annually:
				if cnt > 1:
					if current_date != end_date:
						current_date = current_date + timedelta(days=1)
			month_start, month_end, month_start2, month_end2, total_days_of_month = get_month_details(
				current_date
			)
			n_prior = get_n(current_date, diff_annually)

			if end_date < month_end:
				month_end = end_date

			if diff_annually:
				if month_end < month_end2 and month_end == end_date:
					month_end = current_date
					month_start = current_date.replace(day=1)
				date_difference = month_end - month_start
				# n_next = date_difference.days +1
				n = total_days_of_month
			else:
				date_difference = month_end - month_start
				n = date_difference.days + 1

			if current_date == start_date or month_end == end_date:
				date_difference = month_end - month_start
				n = date_difference.days + 1
				n_prior = n

			if n_prior < total_days_of_month or n < total_days_of_month:
				prev_mlp = mlp
				if not diff_annually:
					mlp = mlp * n / total_days_of_month
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
									mlp = mlp * n / total_days_of_month
								if mrent == 0 and rate == 0 and famt == 0:
									mlp = 0
								mlp = mlp + (rate * mlp / 100) + famt
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
								mlp = mlp + (rate * mlp / 100) + famt
								prev_mlp_escl = mlp
								break

					if current_date == start_date:
						month_start = current_date
						if month_end > end_date:
							month_end = end_date
					else:
						month_start = current_date.replace(day=1)
					val = [month_start.date(), month_end.date()]
					monthly_data[current_date.date().strftime("%Y-%m")] = val
					if prev_mlp_escl is None:
						mlp = prev_mlp
					else:
						mlp = prev_mlp_escl
					if mrent == 0 and rate == 0 and famt == 0 and escalation:
						mlp = prev_mlp
				else:
					mlp_1 = mlp * n_prior / total_days_of_month
					# mlp_2=0
					if current_date == start_date or month_end == end_date:
						mlp = mlp_1
					# mlp_new=mlp
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
								# mlp_2=mlp*n_next/total_days_of_month
								# mlp_new=mlp_1+mlp_2
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
								mlp = mlp + (rate * mlp / 100) + famt
								# mlp_2=mlp*n_next/total_days_of_month
								# mlp_new=mlp_1+mlp_2
								prev_mlp_escl = mlp
								break
					if current_date == start_date:
						month_start = current_date
						if month_end > end_date:
							month_end = end_date
					else:
						month_start = current_date.replace(day=1)
					val = [month_start.date(), month_end.date()]
					monthly_data[current_date.date().strftime("%Y-%m")] = val
					if prev_mlp_escl is None:
						mlp = prev_mlp
					else:
						mlp = prev_mlp_escl
					if mrent == 0 and rate == 0 and famt == 0 and escalation:
						mlp = prev_mlp

			else:
				prev_mlp = mlp
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
							mlp = mlp + (rate * mlp / 100) + famt
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
							if mrent == 0 and rate == 0 and famt == 0:
								mlp = 0
							mlp = mlp + (rate * mlp / 100) + famt

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
							mlp = mlp + (rate * mlp / 100) + famt
							break

				if current_date == start_date:
					month_start = current_date
					if month_end > end_date:
						month_end = end_date
				else:
					month_start = current_date.replace(day=1)
				val = [month_start.date(), month_end.date()]
				monthly_data[current_date.date().strftime("%Y-%m")] = val
				if mrent == 0 and rate == 0 and famt == 0 and escalation:
					mlp = prev_mlp
			if month_end > end_date:
				month_end = end_date
			mid_diff_annually = False
			current_date = date_increment(current_date, diff_annually, mid_diff_annually, esc_bd_end_date)
		return monthly_data

	def validate_invoice_details(self):
		rent_timeline = self.get_lease_rent_timeline()
		for row in self.invoice_details:
			from_date = datetime.strptime(row.from_date, "%Y-%m-%d")
			to_date = datetime.strptime(row.to_date, "%Y-%m-%d")
			date_ranges = []
			exp_rent = []
			current = from_date
			while current <= to_date:
				start_date = current
				_, last_day = monthrange(current.year, current.month)
				end_date = datetime(current.year, current.month, last_day)

				if end_date > to_date:
					end_date = to_date

				date_ranges.append([start_date, end_date])

				if current.month == 12:
					current = current.replace(year=current.year + 1, month=1, day=1)
				else:
					current = current.replace(month=current.month + 1, day=1)

			for i in range(len(date_ranges)):
				dates = date_ranges[i]
				start_date = dates[0]
				end_date = dates[1]
				inv_month = start_date.strftime("%Y-%m")
				exp_rent.append(rent_timeline.get(inv_month))

			expected_rent = 0.0
			for i in range(len(exp_rent)):
				expected_rent += exp_rent[i]
			if expected_rent is None:
				row.is_mismatch = 1
				continue
			actual_amount = float(row.amount)
			tax = float(row.tax)
			if int(row.with_tax) == 1:
				calc_amount = expected_rent + ((tax * expected_rent) / 100)
				if round(calc_amount, 3) != round(actual_amount, 3):
					row.is_mismatch = 1
				else:
					row.is_mismatch = 0
			else:
				if round(actual_amount, 3) != round(expected_rent, 3):
					row.is_mismatch = 1
				else:
					row.is_mismatch = 0


def get_permission_query_conditions(user):
	if not user:
		return ""

	roles = frappe.get_roles(user)
	if "System Manager" in roles or "Accounts" in roles:
		return ""

	if "Vendor" in roles:
		vendor = frappe.db.get_value("Vendor Master", {"email_address": user}, "name")

		if not vendor:
			return "1=0"

		return f"`tabLease Management`.`vendor`='{vendor}'"

	return ""


def has_permission(doc, user):
	roles = frappe.get_roles(user)
	if "System Manager" in roles or "Accounts" in roles:
		return True

	if "Vendor" in roles:
		vendor = frappe.db.get_value("Vendor Master", {"email_address": user}, "name")
		return doc.vendor == vendor

	return False

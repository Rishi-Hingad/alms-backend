import json

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today

REQUIRED_DOCS = {"PE", "TRC", "10F"}


class RemittanceForm15CB(Document):
	def autoname(self):
		company_short = frappe.db.get_value("Remittance Company", self.company, "company_short_form")

		if not company_short:
			frappe.throw("Company short form not set")

		# Company-wise counter
		series_key = f"{company_short}"

		next_number = int(frappe.model.naming.getseries(series_key, 4))

		self.name = f"{next_number:06d} - {company_short}"

	def validate(self):
		self.calculate_invoice_totals()
		self.calculate_taxes()
		# self.set_tds_deduction_date()
		self.add_vat_details()

		if not self.trc_obtained:
			return

		if not self.vendor:
			frappe.throw("Vendor is required.")

		# Step 1: Find DTAA Tax Document record for this vendor
		dtaa_tax_name = frappe.db.get_value("Remittance DTAA Tax Documents", {"vendor": self.vendor}, "name")

		if not dtaa_tax_name:
			frappe.throw("No DTAA Tax Documents found for this Vendor.")

		# Step 2: Get full document
		dtaa_tax_doc = frappe.get_doc("Remittance DTAA Tax Documents", dtaa_tax_name)

		if not dtaa_tax_doc.tax_documents:
			frappe.throw("No tax documents found for this Vendor.")

		today_date = getdate(today())
		valid_docs = set()

		# Step 3: Validate child rows
		for row in dtaa_tax_doc.tax_documents:
			if not row.enabled:
				continue

			if not row.received:
				continue

			if (
				not row.effective_from
				or not row.effective_to
				or getdate(row.effective_from) > today_date
				or getdate(row.effective_to) < today_date
			):
				continue

			if row.tax_document_type:
				valid_docs.add(row.tax_document_type)

		missing = REQUIRED_DOCS - valid_docs

		if missing:
			frappe.throw("Cannot obtain TRC. Missing or invalid documents: " + ", ".join(missing))

		if self.status == "Approved" and not self.is_new():
			# After approval, only POST-APPROVAL fields (attachments + remark)
			# may be edited. Critical financial / regulatory fields must stay
			# locked because they were what the approver actually approved.
			old_doc = self.get_doc_before_save()
			if old_doc:
				CRITICAL_FIELDS = [
					"vendor", "company", "currency",
					"amount_payable_foreign", "amount_payable_inr",
					"tax_category", "purpose_code", "section_of_act",
					"dtaa_name", "dtaa_article", "applicable_dtaa_article",
					"taxable_income", "tax_liability",
					"dtaa_taxable_income", "dtaa_tax_liability",
					"tds_amount_foreign", "tds_amount_inr",
					"tds_rate_income_tax_act", "tds_rate_as_per_dtaa",
					"applicable_tds_rate", "applied_rate",
					"bank_branch", "bank_name", "ifsc_code", "bsr_code",
					"proposed_date_of_remittance",
					"country_to_remit", "actual_remittance_country",
					"gross_up", "taxability_under_it_act", "trc_obtained",
					"basis_for_taxable_income_and_tax_liability_calculation",
				]
				for fname in CRITICAL_FIELDS:
					if self._critical_field_changed(old_doc, fname):
						frappe.throw(
							f"Cannot modify '{fname}' after approval. "
							"Only Attachments and Post-Approval Remark can be edited."
						)

		if self.status == "Pending Approval" and self.approval_entry:
			current_user = frappe.session.user

			# 1. Load the linked Approval Entry Document
			approval_doc = frappe.get_doc("Approval Entry", self.approval_entry)

			# 2. Get the child table (replace 'approval_stages' with your actual fieldname)
			child_table = approval_doc.get("approval_entry")

			if child_table:
				# 3. Get the recent row (last row in the table)
				recent_row = child_table[-1]
				expected_approver = recent_row.next_approver       # user-stage
				expected_role = recent_row.next_approver_role        # role-stage

				# 4. Enforce the rule — allow named user OR users holding the role
				is_named_user = expected_approver and current_user == expected_approver
				has_required_role = expected_role and (expected_role in frappe.get_roles(current_user))
				is_admin = current_user == "Administrator"

				if not (is_named_user or has_required_role or is_admin):
					if expected_approver:
						who = expected_approver
					elif expected_role:
						who = f"role '{expected_role}'"
					else:
						who = "the next approver"
					frappe.throw(
						f"You cannot edit this document. It is currently waiting for action from {who}"
					)

	def _critical_field_changed(self, old_doc, fname):
		"""Type-aware change detection for post-approval lock.

		Currency / Float / Int / Percent fields are compared NUMERICALLY with a
		0.01 tolerance — string compare on these breaks because the DB-stored
		"100.5" and a re-loaded "100.50000000001" look different.
		"""
		new_val = self.get(fname)
		old_val = old_doc.get(fname)

		# Both blank → no change
		if not new_val and not old_val:
			return False

		df = self.meta.get_field(fname)
		if df and df.fieldtype in ("Currency", "Float", "Percent", "Int"):
			try:
				return abs(float(new_val or 0) - float(old_val or 0)) > 0.01
			except (TypeError, ValueError):
				return True

		return str(new_val or "").strip() != str(old_val or "").strip()

	def on_trash(self):
		"""Clear the used-flag on linked SAP FBL1N entries when this Form 15 CB is deleted."""
		for row in self.invoices:
			if row.fbl1n_entry and frappe.db.exists("RE KR Entry", row.fbl1n_entry):
				frappe.db.set_value(
					"RE KR Entry",
					row.fbl1n_entry,
					{"form_15cb": None, "is_used": 0},
					update_modified=False,
				)

	# def before_insert(self):
	# 	self.set_serial_no()

	def before_save(self):
		if self.vendor and not self.vendor_address:
			v = frappe.get_doc("Remittance Vendor", self.vendor)

			address_parts = [
				v.address_line_1,
				v.address_line_2,
				v.road_street,
				v.area_locality,
				v.city_district,
				v.state,
				v.country,
				v.zip_code,
			]

			# Remove empty values
			address_parts = [part for part in address_parts if part]

			# Join with comma
			self.vendor_address = ", ".join(address_parts)


		if self.invoices and not self.document_no:
			self.set("document_no", [])
			for row in self.invoices:
				if row.fbl1n_entry and row.fbl1n_entry:
					self.append("document_no", {"fbl1n_entry": row.fbl1n_entry})

		if self.invoices and not self.exchange_rate:
			# Set exchange rate from first invoice if not already set
			first_invoice = self.invoices[0]
			if first_invoice.waers and first_invoice.kurse:
				self.exchange_rate = first_invoice.kurse
				self.currency = first_invoice.waers
		
	def set_tds_deduction_date(self):
		dates = []

		if self.total_tax_amount!=0:
			for row in self.invoices:
				if row.fbl1n_entry:

					posting_date = frappe.db.get_value(
						"RE KR Entry",
						row.fbl1n_entry,
						"budat"
					)

					if posting_date:
						dates.append(posting_date)

			# set latest/greatest date
			if dates:
				self.date_of_deduction_of_tax_at_source = max(dates)
			else:
				self.date_of_deduction_of_tax_at_source = None

	def add_vat_details(self):
		if self.actual_amt_after_tds_foreign and not self.before_vat_amount:
			self.before_vat_amount = self.actual_amt_after_tds_foreign
		if self.vat:
			self.total_amount= self.before_vat_amount + self.vat
		else:
			self.total_amount= self.before_vat_amount

	def calculate_taxes(self):
		# -------------------------
		# 1. ITA Calculation
		# -------------------------
		ita_rate = self.tds_rate_income_tax_act

		ita_taxable, ita_tax = compute_tax(self.net_amount_inr, ita_rate, self.gross_up)
		ita_taxable_frgn, ita_tax_frgn = compute_tax(self.net_amount_foreign, ita_rate, self.gross_up)

		self.taxable_income = round(ita_taxable)
		self.tax_liability = round(ita_tax)

		self.ita_gross_amount_inr = round(ita_taxable)
		self.ita_tds_amount_inr = round(ita_tax)

		self.ita_gross_amount_foreign = ita_taxable_frgn
		self.ita_tds_amount_foreign = ita_tax_frgn

		# -------------------------
		# 2. DTAA Calculation
		# -------------------------
		dtaa_rate = self.tds_rate_as_per_dtaa

		if self.trc_obtained:
			dtaa_taxable, dtaa_tax = compute_tax(self.net_amount_inr, dtaa_rate, self.gross_up)
			dtaa_taxable_frgn, dtaa_tax_frgn = compute_tax(self.net_amount_foreign, dtaa_rate, self.gross_up)
		else:
			dtaa_taxable = dtaa_tax = 0
			dtaa_taxable_frgn = dtaa_tax_frgn = 0

		self.dtaa_taxable_income = round(dtaa_taxable)
		self.dtaa_tax_liability = round(dtaa_tax)

		self.gross_amount_inr = round(dtaa_taxable)
		self.tds_amount_inr = round(dtaa_tax)

		self.gross_amount_foreign = dtaa_taxable_frgn
		self.tds_amount_foreign = dtaa_tax_frgn

		# -------------------------
		# 3. Zero DTAA Edge Case
		# -------------------------
		if self.trc_obtained and dtaa_rate == 0 and self.net_amount_inr:
			self.gross_amount_inr = 0
			self.tds_amount_inr = 0
			self.gross_amount_foreign = 0
			self.tds_amount_foreign = 0

		# -------------------------
		# 4. Decide Applied Rate
		# -------------------------
		use_dtaa = (
			self.trc_obtained and dtaa_rate is not None and ita_rate is not None and dtaa_rate < ita_rate
		)

		self.applied_rate = dtaa_rate if use_dtaa else ita_rate

		# -------------------------
		# 5. Net After TDS
		# -------------------------
		if use_dtaa:
			gross = self.gross_amount_inr
			tds = self.tds_amount_inr
			gross_frgn = self.gross_amount_foreign
			tds_frgn = self.tds_amount_foreign
		else:
			gross = self.ita_gross_amount_inr
			tds = self.ita_tds_amount_inr
			gross_frgn = self.ita_gross_amount_foreign
			tds_frgn = self.ita_tds_amount_foreign

		if gross is not None and tds is not None:
			self.actual_amt_after_tds_inr = round(gross - tds)
			self.actual_amt_after_tds_foreign = gross_frgn - tds_frgn
			if not self.before_vat_amount:
				self.before_vat_amount = self.actual_amt_after_tds_foreign

		if (
			self.trc_obtained
			and self.dtaa_article
			and self.tds_rate_as_per_dtaa == 0
			and self.net_amount_inr
			and self.net_amount_foreign
		):
			self.actual_amt_after_tds_inr = round(self.net_amount_inr)
			self.actual_amt_after_tds_foreign = self.net_amount_foreign
			if not self.before_vat_amount:
				self.before_vat_amount = self.actual_amt_after_tds_foreign

	# def set_serial_no(self):
	# 	if self.serial_no:
	# 		return

	# 	company_short = frappe.db.get_value("Remittance Company", self.company, "company_short_form")

	# 	if not company_short:
	# 		frappe.throw("Company short form not set")

	# 	# Company-wise counter
	# 	series_key = f"{company_short}"

	# 	next_number = int(frappe.model.naming.getseries(series_key, 4))

	# 	self.serial_no = f"{next_number:04d} - {company_short}"

	def calculate_invoice_totals(self):
		"""Sum up child table (Remittance Invoice) values into parent total fields.

		Mapping:
		  amount_payable_foreign = SUM of qsshb    (Withhldg tax base amount)
		  amount_payable_inr     = SUM of zzqsshb  (Withhldg tax base amount INR)
		  base_amount_foreign    = SUM of wrshb    (Amount in doc. curr.)
		  base_amount_inr        = SUM of dmshb    (Amount in local currency)
		"""
		amount_payable_foreign = 0
		amount_payable_inr = 0
		net_amount_foreign = 0
		net_amount_inr = 0
		total_tax_amount = 0

		for row in self.invoices:
			amount_payable_foreign += row.qsshb or 0
			amount_payable_inr += row.zzqsshb or 0
			net_amount_foreign += row.wrshb or 0
			net_amount_inr += row.dmshb or 0
			total_tax_amount += row.qbshb or 0

		self.amount_payable_foreign = amount_payable_foreign
		self.amount_payable_inr = round(amount_payable_inr)
		self.net_amount_foreign = net_amount_foreign
		self.net_amount_inr = round(net_amount_inr)

		# Keep legacy totals in sync if they exist on the form
		if hasattr(self, "total_invoice_amount"):
			self.total_invoice_amount = net_amount_foreign
		if hasattr(self, "total_tax_amount"):
			self.total_tax_amount = total_tax_amount
		if hasattr(self, "total_amount_payable"):
			self.total_amount_payable = amount_payable_foreign


# -------------------------
# Helpers
# -------------------------
def compute_tax(base_amount, rate, gross_up=False):
	base_amount = float(base_amount or 0)
	rate = float(rate or 0)
	if not base_amount or rate is None:
		return 0, 0

	if gross_up and rate != 0:
		taxable = base_amount / ((100 - rate) / 100)
	else:
		taxable = base_amount
	if rate == 0:
		taxable = 0
	tax = taxable * rate / 100
	return taxable, tax


# -------------------------
# Main
# -------------------------
@frappe.whitelist()
def calculate_taxes_api(doc):
	if isinstance(doc, str):
		doc = frappe._dict(json.loads(doc))
	else:
		doc = frappe._dict(doc)

	net_inr = doc.get("net_amount_inr")
	net_frgn = doc.get("net_amount_foreign")

	# -------------------------
	# 1. ITA Calculation
	# -------------------------
	ita_rate = doc.get("tds_rate_income_tax_act")

	ita_taxable, ita_tax = compute_tax(net_inr, ita_rate, doc.get("gross_up"))
	ita_taxable_frgn, ita_tax_frgn = compute_tax(net_frgn, ita_rate, doc.get("gross_up"))

	doc.taxable_income = round(ita_taxable)
	doc.tax_liability = round(ita_tax)

	doc.ita_gross_amount_inr = round(ita_taxable)
	doc.ita_tds_amount_inr = round(ita_tax)

	doc.ita_gross_amount_foreign = ita_taxable_frgn
	doc.ita_tds_amount_foreign = ita_tax_frgn

	# -------------------------
	# 2. DTAA Calculation
	# -------------------------
	dtaa_rate = doc.get("tds_rate_as_per_dtaa")

	if doc.get("trc_obtained"):
		dtaa_taxable, dtaa_tax = compute_tax(net_inr, dtaa_rate, doc.get("gross_up"))
		dtaa_taxable_frgn, dtaa_tax_frgn = compute_tax(net_frgn, dtaa_rate, doc.get("gross_up"))
	else:
		dtaa_taxable, dtaa_tax = 0, 0
		dtaa_taxable_frgn, dtaa_tax_frgn = 0, 0

	doc.dtaa_taxable_income = round(dtaa_taxable)
	doc.dtaa_tax_liability = round(dtaa_tax)

	doc.gross_amount_inr = round(dtaa_taxable)
	doc.tds_amount_inr = round(dtaa_tax)

	doc.gross_amount_foreign = dtaa_taxable_frgn
	doc.tds_amount_foreign = dtaa_tax_frgn

	# -------------------------
	# 3. Zero DTAA Edge Case
	# -------------------------
	if doc.get("trc_obtained") and dtaa_rate == 0 and net_inr:
		doc.gross_amount_inr = 0
		doc.tds_amount_inr = 0
		doc.gross_amount_foreign = 0
		doc.tds_amount_foreign = 0

	# -------------------------
	# 4. Decide Applied Rate
	# -------------------------
	use_dtaa = (
		doc.get("trc_obtained") and dtaa_rate is not None and ita_rate is not None and dtaa_rate < ita_rate
	)

	doc.applied_rate = dtaa_rate if use_dtaa else ita_rate

	# -------------------------
	# 5. Net After TDS (based on applied rate)
	# -------------------------
	if use_dtaa:
		gross = doc.gross_amount_inr
		tds = doc.tds_amount_inr
		gross_frgn = doc.gross_amount_foreign
		tds_frgn = doc.tds_amount_foreign
	else:
		gross = doc.ita_gross_amount_inr
		tds = doc.ita_tds_amount_inr
		gross_frgn = doc.ita_gross_amount_foreign
		tds_frgn = doc.ita_tds_amount_foreign

	if gross is not None and tds is not None:
		doc.actual_amt_after_tds_inr = round((gross - tds))
		doc.actual_amt_after_tds_foreign = gross_frgn - tds_frgn
		doc.before_vat_amount = doc.actual_amt_after_tds_foreign

	if (
		doc.get("trc_obtained")
		and doc.get("dtaa_article")
		and doc.get("tds_rate_as_per_dtaa") == 0
		and doc.get("net_amount_inr")
		and doc.get("net_amount_foreign")
	):
		doc["actual_amt_after_tds_inr"] = round((doc["net_amount_inr"]))
		doc["actual_amt_after_tds_foreign"] = doc["net_amount_foreign"]
		doc["before_vat_amount"] = doc["actual_amt_after_tds_foreign"]

	return doc

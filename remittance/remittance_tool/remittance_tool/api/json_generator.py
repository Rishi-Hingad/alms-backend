"""IT Portal Form 15CB JSON generator.

Maps a Remittance Form 15 CB doc + linked masters into the JSON shape the
income-tax e-filing portal expects. Sources pulled:

  - Form 15CB doc itself        (numbers, dates, flags, DTAA info)
  - Remittance Company          (remitter PAN, address, contact, director)
  - Remittance Vendor           (remittee identity + foreign address)
  - Remittance Country          (numeric code + ISO code lookup)
  - Remittance Bank Branch      (branch label)
  - Remittance Purpose Code     (broad code + subcode + nature code)
  - CA Master (linked via doc.ca) — CA name, firm, address, IP

Fields with no source remain empty strings so gaps are visible to the team.
Uses ``doc.get(fieldname)`` so missing fields return None instead of raising
AttributeError if the schema evolves.
"""
import json

import frappe


@frappe.whitelist()
def generate_remittance_json(docname):
	doc = frappe.get_doc("Remittance Form 15 CB", docname)
	vendor = _get_linked(doc.get("vendor"), "Remittance Vendor")
	company = _get_linked(doc.get("company"), "Remittance Company")
	bank_branch = _get_linked(doc.get("bank_branch"), "Remittance Bank Branch")
	purpose = _get_linked(doc.get("purpose_code"), "Remittance Purpose Code")
	ca = _get_linked(doc.get("ca"), "CA Master")

	tax_category = doc.get("tax_category") or ""
	director = _split_director_name(company)
	ca_name_parts = _split_ca_name(ca)
	ca_addr = _ca_address_str(ca)
	company_addr = _company_address_str(company)
	company_country_code = _country_code(_g(company, "country"))
	company_iso = _country_iso(_g(company, "country"))
	vendor_country_code = _country_code(_g(vendor, "country") or doc.get("country_to_remit"))

	payload = {
		# ─── Entity (Indian company + authorized director) ─────────────
		"entityNumber": _g(company, "pan") or "",
		"entityFirstName": director["first"],
		"entityMidName": director["middle"],
		"entityLastName": director["last"],
		"entityAddrLine1Txt": _g(ca, "address_line_1") or "",
		"entityAddrLine2Txt": _g(ca, "address_line_2") or "",
		"entityPinCd": _g(ca, "pin_code") or "",
		"entityLocalityDesc": _g(ca, "locality") or "",
		"entityStateCd": "",
		"entityStateDesc": _g(ca, "state") or "",
		"entityCountryCd": _country_code(_g(ca, "country")),
		"entityCountryName": _g(ca, "country") or "",
		"entityDistrictDesc": _g(ca, "district") or "",
		"entityPostofficeDesc": _g(ca, "post_office") or "",
		"entityTaxPayerCatgCd": _status_code(_g(company, "status_of_remitter")),
		"entityTaxPayerCatgDesc": _g(company, "status_of_remitter") or "",
		"entityPrimaryEmail": _g(company, "email_id") or "",
		"entitySecondaryEmail": _g(company, "secondary_email_id") or "",
		"entityPrimaryMobile": _g(company, "phone_number") or "",
		"entityDesig": _g(company, "status_of_remitter") or "",
		"citId": 1,
		"pcPan": _g(ca, "pan") or "",

		# ─── Form metadata ─────────────────────────────────────────────
		"formVersion": 1,
		"schemaVersion": 1,

		# ─── CA user info ──────────────────────────────────────────────
		"userId": _g(ca, "user_id") or "",
		"userFirstName": ca_name_parts["first"],
		"userMidName": ca_name_parts["middle"],
		"userLastName": ca_name_parts["last"],
		"userRoleCd": "CA",
		"userPan": _g(ca, "pan") or "",
		"userEmail": _g(ca, "email_id") or "",
		"userMobile": _g(ca, "mobile") or "",
		"form19bf8DtlsPK": "",

		# ─── Remitter (Indian company) ─────────────────────────────────
		"form19bf8RemitterName": _g(company, "company_name") or doc.get("company") or "",
		"form19bf8Address": company_addr,
		"form19bf8PAN": _g(company, "pan") or "",
		"form19bf8TaxYear": _assessment_year(),
		"form19bf8Status": _g(company, "status_of_remitter") or "",
		"form19bf8ResStatus": _residential_code(_g(company, "residential_status")),
		"form19bf8Email": _g(company, "email_id") or "",
		"form19bf8MobileNumber": _g(company, "phone_number") or "",
		"form19bf8CountryCode1": str(company_country_code or "91"),

		# ─── Remittee (foreign vendor) ─────────────────────────────────
		"form19bf8RemiteeName": _g(vendor, "vendor_name") or doc.get("vendor") or "",
		"form19bf8RemiteeTIN": _g(vendor, "tax_id_no") or "",
		"form19bf8RemiteeCountry": vendor_country_code,
		"form19bf8RemiteeFullAddr": doc.get("vendor_address") or "",
		"form19bf8BusinPlace": _g(vendor, "country_of_residence") or doc.get("country_to_remit") or "",
		"form19bf8CountryCodeISO": company_iso or "in",
		"form19bf8CountryCode": f"+{company_country_code}" if company_country_code else "+91",
		"form19bf8RemittaceCntry": _country_code(
			doc.get("country_to_remit")
			or doc.get("actual_remittance_country")
			or doc.get("country_to_which_actual_remittance_is_made")
		),

		# ─── Amount & bank ─────────────────────────────────────────────
		"form19bf8Currency": doc.get("currency") or "",
		"form19bf8AmtPayableFore": _str_num(doc.get("amount_payable_foreign")),
		"form19bf8AmtPayableInd": _str_num(doc.get("amount_payable_inr")),
		"form19bf8IFSCcode": doc.get("ifsc_code") or "",
		"form19bf8NameBank": doc.get("bank_name") or "",
		"form19bf8Branch": _g(bank_branch, "branch_name") or doc.get("bank_branch") or "",
		"form19bf8BSRcode": str(doc.get("bsr_code") or ""),
		"form19bf8Dealer": "Y",
		"form19bf8ProposedDate": _str_date(doc.get("proposed_date_of_remittance")),

		# ─── Purpose / nature ──────────────────────────────────────────
		"form19bf8RemittanceName": _g(purpose, "nature_code") or "",
		"form19bf8Purposecode": _g(purpose, "category_code") or "",
		"form19bf8Subcode": doc.get("purpose_code") or "",
		"form19bf8GrossedTax": _yn(doc.get("gross_up")),
		"form19bf8Subcode1": doc.get("bank_name") or "",

		# ─── Taxability under IT Act ───────────────────────────────────
		"form19bf8RemittanceTax": _yn(doc.get("taxability_under_it_act")),
		"form19bf8Taxable": doc.get("section_of_act") or "",
		"form19bf8TaxableInc": _str_num(doc.get("taxable_income")),
		"form19bf8TaxLiability": _str_num(doc.get("tax_liability")),
		"form19bf8Taxdetermine": doc.get("basis_for_taxable_income_and_tax_liability_calculation") or "",

		# ─── DTAA relief ───────────────────────────────────────────────
		"form19bf8ReliefClaimed": _yn(doc.get("dtaa_name") or doc.get("trc_obtained")),
		"form19bf8TaxResidency": _yn(doc.get("trc_obtained")),
		"form19bf8Relevant": doc.get("dtaa_name") or "",
		"form19bf8Article": doc.get("dtaa_article") or "",
		"form19bf8NaturePayment": doc.get("specify_nature_of_remittance") or doc.get("nature_of_remittance") or "",
		"form19bf8TaxbleIncome": _str_num(doc.get("dtaa_taxable_income")),
		"form19bf8TaxbleLiablity": _str_num(doc.get("dtaa_tax_liability")),
		"form19bf8Ratededctax": _str_num(doc.get("tds_rate_as_per_dtaa") or doc.get("tds_rate_dtaa")),
		"form19bf8TaxResidNum": doc.get("tax_residency_number") or "",

		# ─── Section A / B of Point 10 ─────────────────────────────────
		"form19bf8RemitanceAcc": _yn(tax_category == "Business Income"),
		"form19bf8ArticleDTAA": doc.get("applicable_dtaa_article") or "",
		"form19bf8RateDTAA": _str_num(doc.get("applicable_tds_rate")),
		"form19bf8RemittanceDrp": _yn(tax_category == "Royalty / FTS / Interest / Dividend"),
		"form19bf8ArticleReasons": "NA",
		"form19bf8CaptialGains": _yn(tax_category == "Capital Gains"),
		"form19bf8Basis": doc.get("basis_for_tax_deduction_rate") or "NA",
		"form19bf8SubItems": _capital_gains_count(doc),
		"form19bf8NatureRemittance": doc.get("specify_nature_of_remittance") or "NA",
		"form19bf8TaxableIncDTAA": _yn(doc.get("taxable_in_india_as_per_dtaa")),
		"form19bf8AmtTaxInd": _str_num(doc.get("income_taxable_in_india")),
		"form19bf8CertAdd": ca_addr or "NA",
		"form19bf8AmtPay": _str_num(doc.get("actual_amt_after_tds_inr")),
		"form19bf8Taxdetermine1": doc.get("basis_for_taxable_income_calculation") or "NA",

		# ─── TDS deduction ─────────────────────────────────────────────
		"form19bf8TDSforeign": _str_num(doc.get("tds_amount_foreign")),
		"form19bf8TDSIndian": _str_num(doc.get("tds_amount_inr")),
		"form19bf8RateTDS": _str_num(doc.get("tds_rate_income_tax_act") or doc.get("applied_rate")),
		"form19bf8OthersTDS": "",
		"form19bf8DateAmtTDS": _str_date(doc.get("date_of_deduction_of_tax_at_source")),
		"form19bf8AmtPayableFore1": _str_num(doc.get("actual_amt_after_tds_foreign")),

		# ─── CA certification ──────────────────────────────────────────
		"form19bf8CertSalutation": _g(ca, "salutation") or "M/s.",
		"form19bf8CerfVerSalutation": _g(ca, "salutation") or "M/s.",
		"form19bf8NameAcc": _g(ca, "ca_name") or "",
		"form19bf8CAMemberNo": _g(ca, "membership_no") or "",
		"form19f8Namefirm": _g(ca, "firm_name") or "",
		"form19bf8FirmRegNo": _g(ca, "firm_registration_no") or "",
		"form19bf8CertPlace": _g(ca, "place") or "",
		"form19bf8CertDate": _str_date(frappe.utils.today()),
		"form19bf8CertIPAddress": _client_ip(),

		# ─── Duplicate / mislabeled portal fields ──────────────────────
		"form19bf8Subcode2": _g(vendor, "vendor_name") or doc.get("vendor") or "",
		"form19bf8RemiteeName1": _g(company, "company_name") or doc.get("company") or "",
		"form19bf8RemittanceAddr": ca_addr,

		# ─── Portal session state (defaults — UI will overwrite) ───────
		"startTime": _start_time_string(),
		"panel1flag": True, "panel1Fl": True, "panel1Save": False,
		"panel2flag": True, "panel2Fl": True, "panel2Save": False,
		"panel3flag": True, "panel3Fl": True, "panel3Save": False,
		"panel4flag": True, "panel4Fl": True, "panel4Save": False,
		"panel5flag": True, "panel5Fl": True, "panel5Save": False,
		"panel6flag": True, "panel6Fl": True, "panel6Save": False,
		"panel7flag": True, "panel7Fl": True, "panel7Save": False,

		# ─── Foreign address (vendor) ──────────────────────────────────
		"tyForm19BF8AddressP2": {
			"country": vendor_country_code,
			"addrLine1": _g(vendor, "address_line_1") or "",
			"zipcode": _g(vendor, "zip_code") or "",
			"foreignPostOffice": "",
			"foreignLocality": _g(vendor, "city_district") or "",
			"foreignDistrict": _g(vendor, "area_locality") or "",
			"foreignState": _g(vendor, "state") or "Foreign",
		},

		# ─── Indian address (company) ──────────────────────────────────
		"tyForm19BF8AddressP3": {
			"country": company_country_code or 91,
			"addrLine1": _g(company, "address_line_1") or "",
			"addrLine2": _g(company, "address_line_2") or "",
			"pincode": _g(company, "pin_code") or "",
			"postOffice": "",
			"locality": _g(company, "area_locality") or "",
			"district": _g(company, "city_district") or "",
			"state": _g(company, "state") or "",
		},
	}

	return json.dumps(payload, indent=2, ensure_ascii=False)


# ─── helpers ────────────────────────────────────────────────────────────

def _get_linked(name, doctype):
	if not name:
		return None
	try:
		return frappe.get_doc(doctype, name)
	except (frappe.DoesNotExistError, Exception):
		return None


def _g(obj, fieldname):
	"""Safe attribute lookup — handles None, dicts, and Frappe docs uniformly."""
	if obj is None:
		return None
	if hasattr(obj, "get"):
		return obj.get(fieldname)
	return getattr(obj, fieldname, None)


def _yn(value):
	return "Y" if value else "N"


def _str_num(value):
	if value in (None, ""):
		return "0"
	return str(value)


def _str_date(value):
	if not value:
		return ""
	return str(value)


def _country_code(country_name):
	if not country_name:
		return ""
	try:
		code = frappe.db.get_value("Remittance Country", country_name, "country_code")
		return code or country_name
	except Exception:
		return country_name


def _country_iso(country_name):
	if not country_name:
		return ""
	try:
		return (frappe.db.get_value("Remittance Country", country_name, "iso_code") or "").lower()
	except Exception:
		return ""


def _capital_gains_count(doc):
	count = 0
	if doc.get("long_term_capital_gains_amount"):
		count += 1
	if doc.get("short_term_capital_gains_amount"):
		count += 1
	return str(count)


def _split_director_name(company):
	"""Split company.director_* fields into first/middle/last for entity* keys."""
	if not company:
		return {"first": "", "middle": "", "last": ""}
	return {
		"first": _g(company, "director_first_name") or "",
		"middle": _g(company, "director_middle_name") or "",
		"last": _g(company, "director_last_name") or "",
	}


def _split_ca_name(ca):
	"""Split CA full name into first/middle/last (best-effort by whitespace)."""
	if not ca:
		return {"first": "", "middle": "", "last": ""}
	full = (_g(ca, "ca_name") or "").strip()
	if not full:
		return {"first": "", "middle": "", "last": ""}
	parts = full.split()
	if len(parts) == 1:
		return {"first": parts[0], "middle": "", "last": ""}
	if len(parts) == 2:
		return {"first": parts[0], "middle": "", "last": parts[1]}
	return {
		"first": parts[0],
		"middle": " ".join(parts[1:-1]),
		"last": parts[-1],
	}


def _ca_address_str(ca):
	"""Build a single-line CA address string for entity* / RemittanceAddr / CertAdd."""
	if not ca:
		return ""
	parts = [
		_g(ca, "address_line_1"),
		_g(ca, "address_line_2"),
		_g(ca, "locality"),
		_g(ca, "post_office"),
		_g(ca, "district"),
		_g(ca, "state"),
		_g(ca, "country"),
	]
	clean = [p for p in parts if p]
	addr = ", ".join(clean)
	pin = _g(ca, "pin_code")
	if pin:
		addr = f"{addr} - {pin}" if addr else pin
	return addr


def _company_address_str(company):
	"""Build a single-line company address string for form19bf8Address."""
	if not company:
		return ""
	parts = [
		_g(company, "address_line_1"),
		_g(company, "address_line_2"),
		_g(company, "road_street"),
		_g(company, "area_locality"),
		_g(company, "city_district"),
		_g(company, "state"),
		_g(company, "country"),
	]
	clean = [p for p in parts if p]
	addr = ", ".join(clean)
	pin = _g(company, "pin_code")
	if pin:
		addr = f"{addr} - {pin}" if addr else pin
	return addr


def _status_code(status_desc):
	"""Map status description → IT portal short code (COM/IND/HUF/etc.)."""
	if not status_desc:
		return ""
	mapping = {
		"Company": "COM",
		"Individual": "IND",
		"HUF": "HUF",
		"Partnership": "FRM",
		"Firm": "FRM",
		"AOP": "AOP",
		"BOI": "BOI",
		"Trust": "TRS",
	}
	return mapping.get(status_desc.strip(), status_desc[:3].upper())


def _residential_code(status):
	"""Map 'Resident' / 'Non-Resident' → 'RES' / 'NRES' codes."""
	if not status:
		return "RES"
	s = status.strip().lower()
	if "non" in s:
		return "NRES"
	return "RES"


def _assessment_year():
	"""Return current assessment year string like '2026-27'.

	Indian AY runs Apr 1 – Mar 31. If we're past April we're in AY (current+1).
	Uses today's date from Frappe so it's deterministic per site.
	"""
	today = frappe.utils.getdate(frappe.utils.today())
	if today.month >= 4:
		ay_start = today.year
	else:
		ay_start = today.year - 1
	return f"{ay_start}-{str(ay_start + 1)[-2:]}"


def _client_ip():
	"""Best-effort IP of the user generating the JSON."""
	try:
		req = getattr(frappe.local, "request", None)
		if not req:
			return ""
		xff = req.headers.get("X-Forwarded-For") or ""
		if xff:
			return xff.split(",")[0].strip()
		return req.remote_addr or ""
	except Exception:
		return ""


def _start_time_string():
	"""IT portal startTime format: 'Mon Jun 15 2026 16:31:45 GMT+0530 (India Standard Time)'."""
	try:
		now = frappe.utils.now_datetime()
		return now.strftime("%a %b %d %Y %H:%M:%S") + " GMT+0530 (India Standard Time)"
	except Exception:
		return ""

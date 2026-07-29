"""IT Portal Form 15CB XML generator — v2 (multi-source).

Same data sources as json_generator.py — pulls from Form 15CB + Remittance
Company + Remittance Vendor + Remittance Country + Remittance Bank Branch +
Remittance Purpose Code + CA Master.

The existing xml_generator.generate_remittance_xml() is preserved untouched.
This file adds generate_remittance_xml_v2() which produces the same root
schema but populates every tag from the proper master records.
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom

import frappe


NS_FORM = "http://incometaxindiaefiling.gov.in/common"
NS_15CB = "http://incometaxindiaefiling.gov.in/FORM15CAB"


@frappe.whitelist()
def generate_remittance_xml_v2(docname):
	doc = frappe.get_doc("Remittance Form 15 CB", docname)
	vendor = _get_linked(doc.get("vendor"), "Remittance Vendor")
	company = _get_linked(doc.get("company"), "Remittance Company")
	bank_branch = _get_linked(doc.get("bank_branch"), "Remittance Bank Branch")
	purpose = _get_linked(doc.get("purpose_code"), "Remittance Purpose Code")
	ca = _get_linked(doc.get("ca"), "CA Master")

	tax_category = doc.get("tax_category") or ""

	ET.register_namespace("Form", NS_FORM)
	ET.register_namespace("FORM15CB", NS_15CB)

	root = ET.Element(f"{{{NS_15CB}}}FORM15CB")

	_build_creation_info(root, ca)
	_build_form_details(root)
	_build_remitter(root, company, doc)
	_build_remittee(root, vendor, doc)
	_build_remittance(root, doc, bank_branch, purpose)
	_build_it_act(root, doc)
	_build_dtaa(root, doc, tax_category)
	_build_tds(root, doc)
	_build_accountant(root, ca)

	xml_bytes = ET.tostring(root, encoding="utf-8")
	pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ")
	return pretty


# ─── XML section builders ────────────────────────────────────────────────

def _build_creation_info(root, ca):
	sec = ET.SubElement(root, f"{{{NS_FORM}}}CreationInfo")
	ET.SubElement(sec, f"{{{NS_FORM}}}SWVersionNo").text = "1.0"
	ET.SubElement(sec, f"{{{NS_FORM}}}SWCreatedBy").text = "Remittance Tool"
	ET.SubElement(sec, f"{{{NS_FORM}}}XMLCreatedBy").text = "Remittance Tool"
	ET.SubElement(sec, f"{{{NS_FORM}}}XMLCreationDate").text = str(frappe.utils.today())
	ET.SubElement(sec, f"{{{NS_FORM}}}IntermediaryCity").text = _g(ca, "place") or ""


def _build_form_details(root):
	sec = ET.SubElement(root, f"{{{NS_FORM}}}Form_Details")
	ET.SubElement(sec, f"{{{NS_FORM}}}FormName").text = "FORM15CB"
	ET.SubElement(sec, f"{{{NS_FORM}}}Description").text = "FORM15CB"
	ET.SubElement(sec, f"{{{NS_FORM}}}AssessmentYear").text = _assessment_year()
	ET.SubElement(sec, f"{{{NS_FORM}}}SchemaVer").text = "Ver1.1"
	ET.SubElement(sec, f"{{{NS_FORM}}}FormVer").text = "1"


def _build_remitter(root, company, doc):
	"""Indian remitter — Company master se sab fields."""
	sec = ET.SubElement(root, f"{{{NS_15CB}}}RemitterDetails")
	ET.SubElement(sec, f"{{{NS_15CB}}}IorWe").text = "02"
	ET.SubElement(sec, f"{{{NS_15CB}}}RemitterHonorific").text = _honorific_code(_g(company, "status_of_remitter"))
	ET.SubElement(sec, f"{{{NS_15CB}}}PAN").text = _g(company, "pan") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}NameRemitter").text = _g(company, "company_name") or doc.get("company") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}BeneficiaryHonorific").text = "03"

	addr = ET.SubElement(sec, f"{{{NS_15CB}}}RemitterAddrs")
	ET.SubElement(addr, f"{{{NS_15CB}}}FlatDoorBuilding").text = _g(company, "address_line_1") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}PremisesBuildingVillage").text = _g(company, "address_line_2") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}RoadStreet").text = _g(company, "road_street") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}AreaLocality").text = _g(company, "area_locality") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}TownCityDistrict").text = _g(company, "city_district") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}State").text = _g(company, "state") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}Country").text = _g(company, "country") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}Pincode").text = _g(company, "pin_code") or ""

	ET.SubElement(sec, f"{{{NS_15CB}}}StatusRemitter").text = _g(company, "status_of_remitter") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}ResidentialStatus").text = _residential_code(_g(company, "residential_status"))
	ET.SubElement(sec, f"{{{NS_15CB}}}EmailId").text = _g(company, "email_id") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}SecondaryEmailId").text = _g(company, "secondary_email_id") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}MobileNumber").text = str(_g(company, "phone_number") or "")
	ET.SubElement(sec, f"{{{NS_15CB}}}TAN").text = _g(company, "tan") or ""

	# Director / authorized signatory
	dir_sec = ET.SubElement(sec, f"{{{NS_15CB}}}AuthorizedSignatory")
	ET.SubElement(dir_sec, f"{{{NS_15CB}}}FirstName").text = _g(company, "director_first_name") or ""
	ET.SubElement(dir_sec, f"{{{NS_15CB}}}MiddleName").text = _g(company, "director_middle_name") or ""
	ET.SubElement(dir_sec, f"{{{NS_15CB}}}LastName").text = _g(company, "director_last_name") or ""
	ET.SubElement(dir_sec, f"{{{NS_15CB}}}PAN").text = _g(company, "director_pan") or ""


def _build_remittee(root, vendor, doc):
	"""Foreign remittee — Vendor master se."""
	sec = ET.SubElement(root, f"{{{NS_15CB}}}RemitteeDtls")
	ET.SubElement(sec, f"{{{NS_15CB}}}NameRemittee").text = _g(vendor, "vendor_name") or doc.get("vendor") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}TaxIdentificationNo").text = _g(vendor, "tax_id_no") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}PrincipalPlaceOfBusiness").text = (
		_g(vendor, "country_of_residence") or doc.get("country_to_remit") or ""
	)

	addr = ET.SubElement(sec, f"{{{NS_15CB}}}RemitteeAddrs")
	ET.SubElement(addr, f"{{{NS_15CB}}}FlatDoorBuilding").text = _g(vendor, "address_line_1") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}PremisesBuildingVillage").text = _g(vendor, "address_line_2") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}RoadStreet").text = _g(vendor, "road_street") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}AreaLocality").text = _g(vendor, "area_locality") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}TownCityDistrict").text = _g(vendor, "city_district") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}State").text = _g(vendor, "state") or "Foreign"
	ET.SubElement(addr, f"{{{NS_15CB}}}Country").text = _g(vendor, "country") or doc.get("country_to_remit") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}ZipCode").text = _g(vendor, "zip_code") or ""


def _build_remittance(root, doc, bank_branch, purpose):
	"""Remittance amount / bank / purpose."""
	sec = ET.SubElement(root, f"{{{NS_15CB}}}RemittanceDetails")
	ET.SubElement(sec, f"{{{NS_15CB}}}CountryRemMadeSecb").text = (
		doc.get("actual_remittance_country")
		or doc.get("country_to_which_actual_remittance_is_made")
		or doc.get("country_to_remit")
		or ""
	)
	ET.SubElement(sec, f"{{{NS_15CB}}}CurrencySecbCode").text = doc.get("currency") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}AmtPayForgnRem").text = _str_num(doc.get("amount_payable_foreign"))
	ET.SubElement(sec, f"{{{NS_15CB}}}AmtPayIndRem").text = _str_num(doc.get("amount_payable_inr"))

	ET.SubElement(sec, f"{{{NS_15CB}}}NameBank").text = doc.get("bank_name") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}BranchName").text = _g(bank_branch, "branch_name") or doc.get("bank_branch") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}IfscCode").text = doc.get("ifsc_code") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}BsrCode").text = str(doc.get("bsr_code") or "")

	ET.SubElement(sec, f"{{{NS_15CB}}}PropDateRem").text = _str_date(doc.get("proposed_date_of_remittance"))

	# Purpose code triple from Remittance Purpose Code master
	ET.SubElement(sec, f"{{{NS_15CB}}}NatureRemCategory").text = _g(purpose, "nature_code") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}RevPurCategory").text = _g(purpose, "category_code") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}RevPurCode").text = doc.get("purpose_code") or ""

	ET.SubElement(sec, f"{{{NS_15CB}}}TaxPayGrossSecb").text = _yn_full(doc.get("gross_up"))
	ET.SubElement(sec, f"{{{NS_15CB}}}AuthorizedDealer").text = "Yes"


def _build_it_act(root, doc):
	"""Income Tax Act details."""
	sec = ET.SubElement(root, f"{{{NS_15CB}}}ItActDetails")
	ET.SubElement(sec, f"{{{NS_15CB}}}RemittanceCharIndia").text = _yn_full(doc.get("taxability_under_it_act"))
	ET.SubElement(sec, f"{{{NS_15CB}}}SecRemCovered").text = doc.get("section_of_act") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}AmtIncChrgIt").text = _str_num(doc.get("taxable_income"))
	ET.SubElement(sec, f"{{{NS_15CB}}}TaxLiablIt").text = _str_num(doc.get("tax_liability"))
	ET.SubElement(sec, f"{{{NS_15CB}}}BasisDeterTax").text = (
		doc.get("basis_for_taxable_income_and_tax_liability_calculation") or ""
	)


def _build_dtaa(root, doc, tax_category):
	"""DTAA + relief details."""
	sec = ET.SubElement(root, f"{{{NS_15CB}}}DTAADetails")
	ET.SubElement(sec, f"{{{NS_15CB}}}ReliefClaimed").text = _yn_full(
		doc.get("dtaa_name") or doc.get("trc_obtained")
	)
	ET.SubElement(sec, f"{{{NS_15CB}}}TaxResidCert").text = _yn_full(doc.get("trc_obtained"))
	ET.SubElement(sec, f"{{{NS_15CB}}}RelevantDtaa").text = doc.get("dtaa_name") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}RelevantArtDtaa").text = doc.get("dtaa_article") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}NaturePayment").text = (
		doc.get("specify_nature_of_remittance") or doc.get("nature_of_remittance") or ""
	)
	ET.SubElement(sec, f"{{{NS_15CB}}}TaxIncDtaa").text = _str_num(doc.get("dtaa_taxable_income"))
	ET.SubElement(sec, f"{{{NS_15CB}}}TaxLiablDtaa").text = _str_num(doc.get("dtaa_tax_liability"))
	ET.SubElement(sec, f"{{{NS_15CB}}}RateTdsADtaa").text = _str_num(
		doc.get("tds_rate_as_per_dtaa") or doc.get("tds_rate_dtaa")
	)

	# Section A — Royalty / FTS / Interest / Dividend
	ET.SubElement(sec, f"{{{NS_15CB}}}RemForRoyFlg").text = _yn_full(
		tax_category == "Royalty / FTS / Interest / Dividend"
	)
	if tax_category == "Royalty / FTS / Interest / Dividend":
		ET.SubElement(sec, f"{{{NS_15CB}}}ArtDtaa").text = doc.get("applicable_dtaa_article") or ""
		ET.SubElement(sec, f"{{{NS_15CB}}}RateTdsBDtaa").text = _str_num(doc.get("applicable_tds_rate"))

	# Section B — Business income
	ET.SubElement(sec, f"{{{NS_15CB}}}RemAcctBusIncFlg").text = _yn_full(tax_category == "Business Income")
	if tax_category == "Business Income":
		ET.SubElement(sec, f"{{{NS_15CB}}}IncLiabIndiaFlg").text = _yn_full(doc.get("income_taxable_in_india"))
		ET.SubElement(sec, f"{{{NS_15CB}}}ReasonofReleventArtDtaa").text = (
			doc.get("basis_for_taxable_income_calculation") or "NA"
		)
		ET.SubElement(sec, f"{{{NS_15CB}}}AmtTaxIndia").text = _str_num(doc.get("income_taxable_in_india"))

	# Section C — Capital gains
	ET.SubElement(sec, f"{{{NS_15CB}}}RemOnCapGainFlg").text = _yn_full(tax_category == "Capital Gains")
	if tax_category == "Capital Gains":
		ET.SubElement(sec, f"{{{NS_15CB}}}LongTermCapGain").text = _str_num(
			doc.get("long_term_capital_gains_amount")
		)
		ET.SubElement(sec, f"{{{NS_15CB}}}ShortTermCapGain").text = _str_num(
			doc.get("short_term_capital_gains_amount")
		)

	# Section D — Other
	ET.SubElement(sec, f"{{{NS_15CB}}}OtherRemDtaa").text = _yn_full(tax_category == "Other")
	if tax_category == "Other":
		ET.SubElement(sec, f"{{{NS_15CB}}}TaxIndDtaaFlg").text = _yn_full(doc.get("taxable_in_india_as_per_dtaa"))
		ET.SubElement(sec, f"{{{NS_15CB}}}NatureRemOther").text = doc.get("specify_nature_of_remittance") or ""
		ET.SubElement(sec, f"{{{NS_15CB}}}BasisDeterTaxOther").text = doc.get("basis_for_tax_deduction_rate") or "NA"
		ET.SubElement(sec, f"{{{NS_15CB}}}AmtIncTaxOther").text = _str_num(doc.get("income_taxable_in_india"))
		ET.SubElement(sec, f"{{{NS_15CB}}}ReasonForNonTaxability").text = doc.get("reason_for_non_taxability") or ""


def _build_tds(root, doc):
	"""TDS deduction details."""
	sec = ET.SubElement(root, f"{{{NS_15CB}}}TDSDetails")
	ET.SubElement(sec, f"{{{NS_15CB}}}AmtPayForgnTds").text = _str_num(doc.get("tds_amount_foreign"))
	ET.SubElement(sec, f"{{{NS_15CB}}}AmtPayIndianTds").text = _str_num(doc.get("tds_amount_inr"))
	ET.SubElement(sec, f"{{{NS_15CB}}}RateTdsSecA").text = _str_num(
		doc.get("tds_rate_income_tax_act") or doc.get("applied_rate")
	)
	ET.SubElement(sec, f"{{{NS_15CB}}}RateTdsSecB").text = _str_num(doc.get("tds_rate_dtaa"))
	ET.SubElement(sec, f"{{{NS_15CB}}}ActlAmtTdsForgn").text = _str_num(doc.get("actual_amt_after_tds_foreign"))
	ET.SubElement(sec, f"{{{NS_15CB}}}ActlAmtTdsInr").text = _str_num(doc.get("actual_amt_after_tds_inr"))
	ET.SubElement(sec, f"{{{NS_15CB}}}DednDateTds").text = _str_date(doc.get("date_of_deduction_of_tax_at_source"))


def _build_accountant(root, ca):
	"""CA certification block — CA Master se sab fields."""
	sec = ET.SubElement(root, f"{{{NS_15CB}}}AcctntDetls")
	ET.SubElement(sec, f"{{{NS_15CB}}}Salutation").text = _g(ca, "salutation") or "M/s."
	ET.SubElement(sec, f"{{{NS_15CB}}}NameAcctnt").text = _g(ca, "ca_name") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}PANAcctnt").text = _g(ca, "pan") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}NameFirmAcctnt").text = _g(ca, "firm_name") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}MembershipNumber").text = _g(ca, "membership_no") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}UDIN").text = _g(ca, "udin") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}RegNoAcctnt").text = _g(ca, "firm_registration_no") or ""

	addr = ET.SubElement(sec, f"{{{NS_15CB}}}AcctntAddrs")
	ET.SubElement(addr, f"{{{NS_15CB}}}FlatDoorBuilding").text = _g(ca, "address_line_1") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}PremisesBuildingVillage").text = _g(ca, "address_line_2") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}AreaLocality").text = _g(ca, "locality") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}TownCityDistrict").text = _g(ca, "city") or _g(ca, "district") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}State").text = _g(ca, "state") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}Country").text = _g(ca, "country") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}Pincode").text = _g(ca, "pin_code") or ""
	ET.SubElement(addr, f"{{{NS_15CB}}}PostOffice").text = _g(ca, "post_office") or ""

	ET.SubElement(sec, f"{{{NS_15CB}}}Place").text = _g(ca, "place") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}DateCert").text = str(frappe.utils.today())
	ET.SubElement(sec, f"{{{NS_15CB}}}IPAddress").text = _client_ip()
	ET.SubElement(sec, f"{{{NS_15CB}}}Email").text = _g(ca, "email_id") or ""
	ET.SubElement(sec, f"{{{NS_15CB}}}Mobile").text = _g(ca, "mobile") or ""


# ─── helpers (same semantics as json_generator) ──────────────────────────

def _get_linked(name, doctype):
	if not name:
		return None
	try:
		return frappe.get_doc(doctype, name)
	except Exception:
		return None


def _g(obj, fieldname):
	if obj is None:
		return None
	if hasattr(obj, "get"):
		return obj.get(fieldname)
	return getattr(obj, fieldname, None)


def _yn_full(value):
	"""IT portal XML schema uses 'Yes' / 'No' (not Y / N like JSON)."""
	return "Yes" if value else "No"


def _str_num(value):
	if value in (None, ""):
		return "0"
	return str(value)


def _str_date(value):
	if not value:
		return ""
	return str(value)


def _residential_code(status):
	if not status:
		return "RES"
	return "NRES" if "non" in status.strip().lower() else "RES"


def _honorific_code(status):
	"""IT portal expects a 2-digit honorific code in RemitterHonorific."""
	if not status:
		return "03"
	mapping = {
		"Company": "03",
		"Individual": "01",
		"HUF": "02",
		"Partnership": "04",
		"Firm": "04",
		"AOP": "05",
		"BOI": "06",
		"Trust": "07",
	}
	return mapping.get(status.strip(), "03")


def _assessment_year():
	today = frappe.utils.getdate(frappe.utils.today())
	ay_start = today.year if today.month >= 4 else today.year - 1
	return f"{ay_start}-{str(ay_start + 1)[-2:]}"


def _client_ip():
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

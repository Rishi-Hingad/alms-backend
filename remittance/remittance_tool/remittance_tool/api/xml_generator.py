import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom

import frappe


@frappe.whitelist()
def generate_remittance_xml(docname):
	doc = frappe.get_doc("Remittance Form 15 CB", docname)

	# ---------------- NAMESPACES ----------------
	NS_FORM = "http://incometaxindiaefiling.gov.in/common"
	NS_15CB = "http://incometaxindiaefiling.gov.in/FORM15CAB"

	ET.register_namespace("Form", NS_FORM)
	ET.register_namespace("FORM15CB", NS_15CB)

	# ---------------- ROOT ----------------
	root = ET.Element(f"{{{NS_15CB}}}FORM15CB")

	# ---------------- CREATION INFO ----------------
	creation_info = ET.SubElement(root, f"{{{NS_FORM}}}CreationInfo")
	ET.SubElement(creation_info, f"{{{NS_FORM}}}SWVersionNo").text = "1.0"
	ET.SubElement(creation_info, f"{{{NS_FORM}}}SWCreatedBy").text = "Test"
	ET.SubElement(creation_info, f"{{{NS_FORM}}}XMLCreatedBy").text = "Test"
	ET.SubElement(creation_info, f"{{{NS_FORM}}}XMLCreationDate").text = str(frappe.utils.today())
	ET.SubElement(creation_info, f"{{{NS_FORM}}}IntermediaryCity").text = "Vapi"

	# ---------------- FORM DETAILS ----------------
	form_details = ET.SubElement(root, f"{{{NS_FORM}}}Form_Details")
	ET.SubElement(form_details, f"{{{NS_FORM}}}FormName").text = "FORM15CB"
	ET.SubElement(form_details, f"{{{NS_FORM}}}Description").text = "FORM15CB"
	ET.SubElement(form_details, f"{{{NS_FORM}}}AssessmentYear").text = str(datetime.now().year)
	ET.SubElement(form_details, f"{{{NS_FORM}}}SchemaVer").text = "Ver1.1"
	ET.SubElement(form_details, f"{{{NS_FORM}}}FormVer").text = "1"

	# ---------------- REMITTER DETAILS ----------------
	remitter = ET.SubElement(root, f"{{{NS_15CB}}}RemitterDetails")
	ET.SubElement(remitter, f"{{{NS_15CB}}}IorWe").text = "02"
	ET.SubElement(remitter, f"{{{NS_15CB}}}RemitterHonorific").text = "03"
	company = frappe.get_doc("Remittance Company", doc.company)
	ET.SubElement(remitter, f"{{{NS_15CB}}}PAN").text = "***"
	ET.SubElement(remitter, f"{{{NS_15CB}}}NameRemitter").text = company.company_name or ""
	ET.SubElement(remitter, f"{{{NS_15CB}}}BeneficiaryHonorific").text = "03"

	# ---------------- REMITTEE DETAILS ----------------
	remittee = ET.SubElement(root, f"{{{NS_15CB}}}RemitteeDtls")
	vendor = frappe.get_doc("Remittance Vendor", doc.vendor)
	ET.SubElement(remittee, f"{{{NS_15CB}}}NameRemittee").text = vendor.vendor_name or ""

	remittee_address = ET.SubElement(remittee, f"{{{NS_15CB}}}RemitteeAddrs")
	ET.SubElement(remittee_address, f"{{{NS_15CB}}}PremisesBuildingVillage").text = (
		vendor.address_line_2 or ""
	)
	ET.SubElement(remittee_address, f"{{{NS_15CB}}}TownCityDistrict").text = vendor.city_district or ""
	ET.SubElement(remittee_address, f"{{{NS_15CB}}}FlatDoorBuilding").text = vendor.address_line_1 or ""
	ET.SubElement(remittee_address, f"{{{NS_15CB}}}AreaLocality").text = vendor.area_locality or ""
	ET.SubElement(remittee_address, f"{{{NS_15CB}}}ZipCode").text = vendor.zip_code or ""
	ET.SubElement(remittee_address, f"{{{NS_15CB}}}State").text = vendor.state or ""
	ET.SubElement(remittee_address, f"{{{NS_15CB}}}RoadStreet").text = vendor.road_street or ""
	ET.SubElement(remittee_address, f"{{{NS_15CB}}}Country").text = doc.country_to_remit or ""

	# ---------------- REMITTANCE DETAILS ----------------
	remittance = ET.SubElement(root, f"{{{NS_15CB}}}RemittanceDetails")
	bank_branch = frappe.get_doc("Remittance Bank Branch", doc.bank_branch)
	ET.SubElement(remittance, f"{{{NS_15CB}}}CountryRemMadeSecb").text = doc.country_to_remit or ""
	ET.SubElement(remittance, f"{{{NS_15CB}}}CurrencySecbCode").text = doc.currency or ""
	ET.SubElement(remittance, f"{{{NS_15CB}}}AmtPayForgnRem").text = str(doc.amount_payable_foreign or 0)
	ET.SubElement(remittance, f"{{{NS_15CB}}}AmtPayIndRem").text = str(doc.amount_payable_inr or 0)
	ET.SubElement(remittance, f"{{{NS_15CB}}}NameBankCode").text = ""
	ET.SubElement(remittance, f"{{{NS_15CB}}}BranchName").text = bank_branch.branch_name or ""
	ET.SubElement(remittance, f"{{{NS_15CB}}}BsrCode").text = str(bank_branch.bsr_code or 0)
	ET.SubElement(remittance, f"{{{NS_15CB}}}PropDateRem").text = str(doc.proposed_date_of_remittance or "")
	ET.SubElement(remittance, f"{{{NS_15CB}}}NatureRemCategory").text = doc.nature_of_remittance or ""
	ET.SubElement(remittance, f"{{{NS_15CB}}}RevPurCategory").text = ""
	ET.SubElement(remittance, f"{{{NS_15CB}}}RevPurCode").text = doc.purpose_code or ""
	ET.SubElement(remittance, f"{{{NS_15CB}}}TaxPayGrossSecb").text = "Yes" if doc.gross_up else "No"

	# ---------------- IT ACT DETAILS ----------------
	it_act = ET.SubElement(root, f"{{{NS_15CB}}}ItActDetails")
	ET.SubElement(it_act, f"{{{NS_15CB}}}RemittanceCharIndia").text = ""
	ET.SubElement(it_act, f"{{{NS_15CB}}}SecRemCovered").text = doc.section_of_act or ""
	ET.SubElement(it_act, f"{{{NS_15CB}}}AmtIncChrgIt").text = str(doc.taxable_income or 0)
	ET.SubElement(it_act, f"{{{NS_15CB}}}TaxLiablIt").text = str(doc.tax_liability or 0)
	ET.SubElement(it_act, f"{{{NS_15CB}}}BasisDeterTax").text = (
		doc.basis_for_taxable_income_and_tax_liability_calculation or ""
	)

	# ---------------- DTAA DETAILS ----------------
	dtaa_act = ET.SubElement(root, f"{{{NS_15CB}}}DTAADetails")
	ET.SubElement(dtaa_act, f"{{{NS_15CB}}}TaxResidCert").text = "Yes" if doc.trc_obtained else "No"
	ET.SubElement(dtaa_act, f"{{{NS_15CB}}}RelevantDtaa").text = doc.dtaa_name or ""
	# art = frappe.get_doc("DTAA Article", doc.dtaa_article)
	# ET.SubElement(dtaa_act, f"{{{NS_15CB}}}RelevantArtDtaa").text = (
	# 	art.article_no + " " + art.article_description or ""
	# )
	ET.SubElement(dtaa_act, f"{{{NS_15CB}}}RelevantArtDtaa").text = doc.dtaa_article or ""
	ET.SubElement(dtaa_act, f"{{{NS_15CB}}}TaxIncDtaa").text = str(doc.dtaa_taxable_income or 0)
	ET.SubElement(dtaa_act, f"{{{NS_15CB}}}TaxLiablDtaa").text = str(doc.dtaa_tax_liability or 0)
	ET.SubElement(dtaa_act, f"{{{NS_15CB}}}RemForRoyFlg").text = (
		"Yes" if doc.tax_category == "Royalty / FTS / Interest / Dividend" else "No"
	)
	if doc.tax_category == "Royalty / FTS / Interest / Dividend":
		ET.SubElement(dtaa_act, f"{{{NS_15CB}}}ArtDtaa").text = doc.applicable_dtaa_article or ""
		ET.SubElement(dtaa_act, f"{{{NS_15CB}}}RateTdsADtaa").text = str(doc.tds_rate_as_per_dtaa or 0)
	ET.SubElement(dtaa_act, f"{{{NS_15CB}}}RemAcctBusIncFlg").text = (
		"Yes" if doc.tax_category == "Business Income" else "No"
	)
	if doc.tax_category == "Business Income":
		ET.SubElement(dtaa_act, f"{{{NS_15CB}}}IncLiabIndiaFlg").text = (
			"Yes" if doc.income_taxable_in_india else "No"
		)
		ET.SubElement(dtaa_act, f"{{{NS_15CB}}}ReasonofReleventArtDtaa").text = ""
	ET.SubElement(dtaa_act, f"{{{NS_15CB}}}RemOnCapGainFlg").text = (
		"Yes" if doc.tax_category == "Capital Gains" else "No"
	)
	ET.SubElement(dtaa_act, f"{{{NS_15CB}}}OtherRemDtaa").text = (
		"Yes" if doc.tax_category == "Other" else "No"
	)
	if doc.tax_category == "Other":
		ET.SubElement(dtaa_act, f"{{{NS_15CB}}}TaxIndDtaaFlg").text = (
			"Yes" if doc.taxable_in_india_as_per_dtaa else "No"
		)
	ET.SubElement(dtaa_act, f"{{{NS_15CB}}}TaxIndDtaaFlg").text = ""

	# ---------------- TDS DETAILS ----------------
	tds_det = ET.SubElement(root, f"{{{NS_15CB}}}TDSDetails")
	ET.SubElement(tds_det, f"{{{NS_15CB}}}AmtPayForgnTds").text = str(doc.tds_amount_foreign or 0)
	ET.SubElement(tds_det, f"{{{NS_15CB}}}AmtPayIndianTds").text = str(doc.tds_amount_inr or 0)
	ET.SubElement(tds_det, f"{{{NS_15CB}}}RateTdsSecbFlg").text = ""
	ET.SubElement(tds_det, f"{{{NS_15CB}}}RateTdsSecB").text = str(doc.tds_rate_dtaa or 0)
	ET.SubElement(tds_det, f"{{{NS_15CB}}}ActlAmtTdsForgn").text = str(doc.actual_amt_after_tds_foreign or 0)
	ET.SubElement(tds_det, f"{{{NS_15CB}}}DednDateTds").text = str(
		getattr(doc, "date_of_deduction", None) or ""
	)

	# ---------------- TDS DETAILS ----------------
	acctnt_det = ET.SubElement(root, f"{{{NS_15CB}}}AcctntDetls")
	ET.SubElement(acctnt_det, f"{{{NS_15CB}}}NameAcctnt").text = ""
	ET.SubElement(acctnt_det, f"{{{NS_15CB}}}NameFirmAcctnt").text = ""

	acctnt_address = ET.SubElement(acctnt_det, f"{{{NS_15CB}}}AcctntAddrs")
	ET.SubElement(acctnt_address, f"{{{NS_15CB}}}PremisesBuildingVillage").text = ""
	ET.SubElement(acctnt_address, f"{{{NS_15CB}}}TownCityDistrict").text = ""
	ET.SubElement(acctnt_address, f"{{{NS_15CB}}}FlatDoorBuilding").text = ""
	ET.SubElement(acctnt_address, f"{{{NS_15CB}}}AreaLocality").text = ""
	ET.SubElement(acctnt_address, f"{{{NS_15CB}}}Pincode").text = ""
	ET.SubElement(acctnt_address, f"{{{NS_15CB}}}State").text = ""
	ET.SubElement(acctnt_address, f"{{{NS_15CB}}}RoadStreet").text = ""
	ET.SubElement(acctnt_address, f"{{{NS_15CB}}}Country").text = ""
	ET.SubElement(acctnt_det, f"{{{NS_15CB}}}MembershipNumber").text = ""
	ET.SubElement(acctnt_det, f"{{{NS_15CB}}}RegNoAcctnt").text = ""

	# ---------------- PRETTY PRINT ----------------
	xml_string = ET.tostring(root, encoding="utf-8")
	parsed = minidom.parseString(xml_string)
	pretty_xml = parsed.toprettyxml(indent="  ")

	return pretty_xml

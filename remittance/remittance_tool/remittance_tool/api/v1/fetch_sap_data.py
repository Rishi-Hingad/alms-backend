import xml.etree.ElementTree as ET
from datetime import datetime

import frappe
import requests
from frappe import _

# from remittance_tool.remittance_tool.api.v1.sap_safety import (
# 	assert_circuit_closed,
# 	engage_circuit,
# )

NS = {
	"atom": "http://www.w3.org/2005/Atom",
	"m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
	"d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
}

# SAP XML field name → RE KR Entry doctype field name
SAP_TO_FBL1N_MAP = {
	"Bukrs": "bukrs",
	"Lifnr": "lifnr",
	"Name1": "name1",
	"Xblnr": "xblnr",
	"Belnr": "belnr",
	"Blart": "blart",
	"Bldat": "bldat",  # date field → parsed
	"Budat": "budat",  # date field → parsed
	"Zlspr": "zlspr",
	"Qsshb": "qsshb",
	"Zzqsshb": "zzqsshb",
	"Qbshb": "qbshb",
	"Zzqbshb": "zzqbshb",
	"Wrshb": "wrshb",
	"Dmshb": "dmshb",
	"Waers": "waers",
	"Kurse": "kurse",
	"Hwaer": "hwaer",
}

DATE_FIELDS = {"Bldat", "Budat"}


def format_date_yyyymmdd(date_str):
	"""Convert YYYY-MM-DD to YYYYMMDD, or return as-is if already YYYYMMDD."""
	if not date_str:
		return ""
	return str(date_str).strip().replace("-", "")


def parse_amount(val):
	"""Handle SAP trailing-minus amounts: '4513.37-' → -4513.37"""
	if not val:
		return 0.0
	s = str(val).strip()
	if not s or s == "0.00":
		return 0.0
	if s.endswith("-"):
		return -float(s[:-1])
	try:
		return float(s)
	except ValueError:
		return 0.0


def parse_sap_date(val):
	"""SAP date YYYYMMDD or timestamp → YYYY-MM-DD string."""
	if not val:
		return None
	s = str(val).strip()
	if "T" in s:
		s = s.split("T")[0]
	if len(s) == 8 and s.isdigit():
		return f"{s[:4]}-{s[4:6]}-{s[6:]}"
	return s


def parse_xml_entries(xml_content):
	"""Parse SAP OData XML response and return list of dicts (SAP field names as keys)."""
	root = ET.fromstring(xml_content)
	entries = root.findall("atom:entry", NS)
	results = []
	for entry in entries:
		properties = entry.find("atom:content/m:properties", NS)
		if properties is None:
			continue
		data = {}
		for prop in properties:
			tag_name = prop.tag.split("}")[-1]
			data[tag_name] = prop.text
		results.append(data)
	return results


def format_xml(xml_str):
	"""Pretty-print XML string for better readability in the Desk."""
	if not xml_str or not isinstance(xml_str, str) or not xml_str.strip().startswith("<"):
		return xml_str
	try:
		from xml.dom import minidom
		reparsed = minidom.parseString(xml_str)
		return reparsed.toprettyxml(indent="  ")
	except Exception:
		return xml_str


# Fields compared to detect value changes (excludes punch_time, is_used, form_15cb)
COMPARE_FIELDS = [
	"lifnr",
	"name1",
	"xblnr",
	"blart",
	"bldat",
	"budat",
	"zlspr",
	"qsshb",
	"zzqsshb",
	"qbshb",
	"zzqbshb",
	"wrshb",
	"dmshb",
	"waers",
	"kurse",
	"hwaer",
]


def _build_fbl1n_values(sap_data):
	"""Extract and parse all RE KR Entry field values from raw SAP dict."""
	values = {}
	values["bukrs"] = sap_data.get("Bukrs", "")
	values["lifnr"] = sap_data.get("Lifnr", "")
	values["name1"] = sap_data.get("Name1", "")
	values["xblnr"] = sap_data.get("Xblnr", "")
	values["belnr"] = sap_data.get("Belnr", "")
	values["blart"] = sap_data.get("Blart", "")
	values["zlspr"] = sap_data.get("Zlspr", "")
	values["waers"] = sap_data.get("Waers") or sap_data.get("WAERS") or ""
	values["hwaer"] = sap_data.get("Hwaer") or sap_data.get("HWAER") or ""
	values["bldat"] = parse_sap_date(sap_data.get("Bldat"))
	values["budat"] = parse_sap_date(sap_data.get("Budat"))
	values["qsshb"] = parse_amount(sap_data.get("Qsshb"))
	values["zzqsshb"] = parse_amount(sap_data.get("Zzqsshb") or sap_data.get("ZZQSSHB"))
	values["qbshb"] = parse_amount(sap_data.get("Qbshb") or sap_data.get("QBSHB"))
	values["zzqbshb"] = parse_amount(sap_data.get("Zzqbshb") or sap_data.get("ZZQBSHB"))
	values["wrshb"] = parse_amount(sap_data.get("Wrshb") or sap_data.get("WRSHB"))
	values["dmshb"] = parse_amount(sap_data.get("Dmshb") or sap_data.get("DMSHB"))
	try:
		values["kurse"] = float(sap_data.get("Kurse") or sap_data.get("KURSE") or 0)
	except (ValueError, TypeError):
		values["kurse"] = 0.0
	return values


def _has_changed(existing_doc, new_values):
	"""Return True if any tracked field value differs between existing doc and new SAP data."""
	for field in COMPARE_FIELDS:
		old_val = existing_doc.get(field)
		new_val = new_values.get(field)
		# Normalize for comparison
		if isinstance(old_val, float) or isinstance(new_val, float):
			if round(float(old_val or 0), 4) != round(float(new_val or 0), 4):
				return True
		else:
			if str(old_val or "") != str(new_val or ""):
				return True
	return False


def upsert_fbl1n_entry(sap_data):
	"""
	Smart insert/skip/update for RE KR Entry.
	
	Logic:
	  1. No existing record → INSERT new with name {bukrs}-{belnr}
	  2. Existing record, same values → SKIP (exact duplicate)
	  3. Existing record, values changed →
	       - Rename old to {bukrs}-{belnr}-HIST-{timestamp}
	       - Mark old as is_outdated=1 (hidden from non-Admins)
	       - INSERT new with name {bukrs}-{belnr}

	Returns (doc_name, action) where action is 'inserted', 'skipped', or 'updated'
	"""
	bukrs = sap_data.get("Bukrs") or ""
	belnr = sap_data.get("Belnr") or ""

	if not bukrs or not belnr:
		# print(f">>> [SKIP] Missing Bukrs or Belnr in SAP data: {sap_data}")
		return None, "skipped"

	canonical_name = f"{bukrs}-{belnr}"
	new_values = _build_fbl1n_values(sap_data)

	# --- Check if active (non-outdated) record exists ---
	existing_name = frappe.db.get_value(
		"RE KR Entry", {"bukrs": bukrs, "belnr": belnr, "is_outdated": 0}, "name"
	)

	if existing_name:
		existing_doc = frappe.get_doc("RE KR Entry", existing_name)

		if not _has_changed(existing_doc, new_values):
			# Case 2: Exact duplicate — skip
			# print(f">>> [SKIP] No changes detected for: {existing_name}")
			return existing_name, "skipped"

		# Case 3: Values changed — archive old, insert new
		timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
		hist_name = f"{canonical_name}-HIST-{timestamp}"

		# Rename old record to history name and mark outdated.
		# Frappe v15 public wrapper accepts only: force, merge, ignore_if_exists,
		# show_alert, rebuild_search. force=True bypasses allow_rename / perm checks.
		frappe.flags.in_patch = True
		try:
			frappe.rename_doc(
				"RE KR Entry",
				existing_name,
				hist_name,
				force=True,
				show_alert=False,
				rebuild_search=False,
			)
		finally:
			frappe.flags.in_patch = False
		frappe.db.set_value(
			"RE KR Entry",
			hist_name,
			{
				"is_outdated": 1,
			},
			update_modified=False,
		)
		# print(f">>> [ARCHIVE] Old record archived as: {hist_name}")

	# Case 1 or 3: Insert fresh record with canonical name
	doc = frappe.get_doc({"doctype": "RE KR Entry", **new_values})
	doc.punch_time = datetime.now()
	doc.insert(ignore_permissions=True, ignore_mandatory=True)

	action = "updated" if existing_name else "inserted"
	# print(f">>> [{action.upper()}] RE KR Entry: {doc.name}")
	return doc.name, action


@frappe.whitelist()
def fetch_sap_data(lifnr=None, bukrs=None, augdt=None, sap_client=None):
	# Circuit-breaker: refuse to call SAP if a previous attempt 401'd
	# assert_circuit_closed()

	# --- SAP Setting: ONLY url + auth credentials ---
	settings = frappe.get_doc("SAP Setting")
	if not settings.url:
		frappe.throw(_("SAP Setting URL is missing. Please configure it in SAP Setting."))
	if not settings.auth_user_name or not settings.auth_user_pass:
		frappe.throw(_("SAP Setting Auth credentials (username/password) are missing."))

	# --- All other values MUST come from parameters (passed by JS from masters) ---
	if not lifnr:
		frappe.throw(_("Vendor Code (lifnr) is required"))
	if not bukrs:
		frappe.throw(_("Company Code (bukrs) is required"))
	if not augdt:
		frappe.throw(_("Clearing Date (augdt) is required"))

	augdt = format_date_yyyymmdd(augdt)
	request_url = settings.url.rstrip("/")

	# Query params: sap_client from Remittance Company.sap_client_code
	params = {}
	if sap_client:
		params["sap-client"] = sap_client

	# Headers: SAP filter values as headers
	headers = {
		"Accept": "application/xml",
		"lifnr": str(lifnr),
		"bukrs": str(bukrs),
		"augdt": str(augdt),
	}

	# Auth: Basic Auth from SAP Setting only
	auth = (settings.auth_user_name, settings.get_password("auth_user_pass"))

	# --- Prepare initial log entry data ---
	log_entry = {
		"doctype": "SAP Log",
		"vendor_code": lifnr,
		"company_code": bukrs,
		"url": request_url,
		"call_datetime": datetime.now(),
		"request_data": frappe.as_json({"headers": headers, "params": params}, indent=2),
	}

	response = None
	try:
		response = requests.get(
			request_url,
			headers=headers,
			params=params,
			auth=auth,
			verify=False,
			timeout=60,
		)

		# Update log with response details
		log_entry.update({
			"status": "Success" if response.status_code < 400 else "Failed",
			"url": response.url,
			"response": format_xml(response.text),
		})

		if response.status_code == 401:
			# engage_circuit(f"401 Unauthorized at {request_url}")
			frappe.log_error("SAP FBL1N Fetch Error", f"401 —  URL={request_url}")
			# Save log before throwing
			frappe.get_doc(log_entry).insert(ignore_permissions=True)
			frappe.db.commit()
			frappe.throw(
				_(
					"SAP returned 401 Unauthorized. "
					"Verify the WF-BATCH password with the SAP admin, update SAP Setting, then reset the circuit."
				)
			)

		response.raise_for_status()

		# Save successful log
		frappe.get_doc(log_entry).insert(ignore_permissions=True)

	except frappe.ValidationError:
		raise
	except Exception as e:
		# Update log with error info if not already updated by a successful response
		if response is not None:
			log_entry.update({
				"status": "Failed",
				"url": response.url,
				"response": format_xml(response.text),
			})
		else:
			log_entry.update({
				"status": "Failed",
				"response": f"Exception: {str(e)}"
			})

		frappe.get_doc(log_entry).insert(ignore_permissions=True)
		frappe.db.commit()

		frappe.log_error("SAP FBL1N Fetch Error", str(e)[:140])
		frappe.throw(_("Failed to fetch data from SAP. Check Error Log."))

	# --- Parse XML and save to RE KR Entry ---
	sap_entries = parse_xml_entries(response.content)
	# print(f">>> [PARSED] {len(sap_entries)} entries received from SAP")

	inserted = 0
	updated = 0
	skipped = 0

	for sap_data in sap_entries:
		_doc_name, action = upsert_fbl1n_entry(sap_data)
		if action == "inserted":
			inserted += 1
		elif action == "updated":
			updated += 1
		else:
			skipped += 1

	frappe.db.commit()

	# print(f">>> [DONE] Inserted: {inserted}, Updated: {updated}, Skipped (no change): {skipped}")

	return {
		"message": (
			f"Processed {len(sap_entries)} entries from SAP — "
			f"New: {inserted}, Updated: {updated}, No change: {skipped}"
		),
		"total": len(sap_entries),
		"inserted": inserted,
		"updated": updated,
		"skipped": skipped,
	}

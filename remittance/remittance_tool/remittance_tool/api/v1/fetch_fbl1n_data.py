import xml.etree.ElementTree as ET
from datetime import datetime

import frappe
import requests
from frappe import _

from remittance_tool.remittance_tool.api.v1.sap_safety import (
	assert_circuit_closed,
	engage_circuit,
)

NS = {
	"atom": "http://www.w3.org/2005/Atom",
	"m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
	"d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
}


def parse_amount(val):
	"""SAP trailing-minus amounts like '4513.37-' -> -4513.37"""
	if not val:
		return 0.0
	s = str(val).strip()
	if not s or s == "0.00":
		return 0.0
	if s.endswith("-"):
		return -float(s[:-1])
	return float(s)


def parse_sap_date(val):
	"""YYYYMMDD -> YYYY-MM-DD, or timestamp with T -> date portion only"""
	if not val:
		return None
	s = str(val).strip()
	if "T" in s:
		s = s.split("T")[0]
	if len(s) == 8 and s.isdigit():
		return f"{s[:4]}-{s[4:6]}-{s[6:]}"
	return s


def build_request(settings, augdt, lifnr=None, bukrs=None):
	"""Build (url, headers, params, auth) tuple for SAP FBL1N request.

	SAP expects:
	  - lifnr, bukrs, augdt  -> HTTP request headers
	  - sap-client           -> URL query parameter
	  - Auth                 -> HTTP Basic Auth
	"""
	url = settings.url.rstrip("/")

	lifnr = lifnr or settings.lifnr or ""
	bukrs = bukrs or settings.bukrs or ""

	headers = {
		"Accept": "application/xml",
		"lifnr": str(lifnr),
		"bukrs": str(bukrs),
		"augdt": str(augdt or ""),
	}

	params = {}
	sap_client = getattr(settings, "sap_client", None)
	if sap_client:
		params["sap-client"] = sap_client

	auth = None
	if settings.auth_user_name and settings.auth_user_pass:
		auth = (settings.auth_user_name, settings.get_password("auth_user_pass"))
	elif settings.authorization_key:
		headers["Authorization"] = f"{settings.authorization_type} {settings.authorization_key}"

	return url, headers, params, auth


def parse_entries(xml_content):
	"""Parse SAP OData XML and return list of dicts."""
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


def insert_or_update_fbl1n(data):
	"""Insert a RE KR Entry record. Skips if entry with same bukrs+belnr already exists."""
	bukrs = data.get("Bukrs", "")
	belnr = data.get("Belnr", "")
	doc_name = f"{bukrs}-{belnr}"

	if frappe.db.exists("RE KR Entry", doc_name):
		return doc_name, "skipped"

	values = {
		"bukrs": bukrs,
		"lifnr": data.get("Lifnr", ""),
		"name1": data.get("Name1", ""),
		"xblnr": data.get("Xblnr", ""),
		"belnr": belnr,
		"blart": data.get("Blart", ""),
		"bldat": parse_sap_date(data.get("Bldat")),
		"budat": parse_sap_date(data.get("Budat")),
		"zlspr": data.get("Zlspr", ""),
		"qsshb": parse_amount(data.get("Qsshb")),
		"zzqsshb": parse_amount(data.get("Zzqsshb") or data.get("ZZQSSHB")),
		"qbshb": parse_amount(data.get("Qbshb") or data.get("QBSHB")),
		"zzqbshb": parse_amount(data.get("Zzqbshb") or data.get("ZZQBSHB")),
		"wrshb": parse_amount(data.get("Wrshb") or data.get("WRSHB")),
		"dmshb": parse_amount(data.get("Dmshb") or data.get("DMSHB")),
		"waers": data.get("Waers") or data.get("WAERS") or "",
		"kurse": float(data.get("Kurse") or data.get("KURSE") or 0),
		"hwaer": data.get("Hwaer") or data.get("HWAER") or "",
	}

	doc = frappe.new_doc("RE KR Entry")
	doc.update(values)
	doc.insert(ignore_permissions=True)
	return doc.name, "inserted"


@frappe.whitelist()
def fetch_fbl1n_data(augdt=None):
	"""
	Fetch vendor line items from SAP ZFBL1N OData service and punch into
	RE KR Entry doctype.

	Args:
		augdt: Clearing date in YYYYMMDD format. Defaults to today.
	"""
	# Circuit-breaker: refuse to call SAP if a previous attempt 401'd
	assert_circuit_closed()

	settings = frappe.get_doc("SAP Setting")

	if not settings.url:
		frappe.throw(_("SAP Setting URL is missing"))

	if not augdt:
		augdt = datetime.today().strftime("%Y%m%d")

	url, headers, params, auth = build_request(settings, augdt)

	try:
		response = requests.get(url, headers=headers, params=params, auth=auth, verify=False, timeout=60)
		if response.status_code == 401:
			engage_circuit(f"401 Unauthorized at {url}")
			frappe.log_error("SAP FBL1N Fetch Error", f"401 — circuit breaker engaged for {augdt}")
			frappe.throw(
				_(
					"SAP returned 401 Unauthorized. Local circuit breaker engaged to prevent further attempts. "
					"Verify the WF-BATCH password, update SAP Setting, then reset the circuit."
				)
			)
		response.raise_for_status()
	except frappe.ValidationError:
		raise
	except Exception as e:
		frappe.log_error(
			"SAP FBL1N Fetch Error", f"SAP FBL1N Request Failed for date {augdt}: {str(e)}"[:140]
		)
		frappe.throw(_("Failed to fetch FBL1N data from SAP. Check Error Log."))

	entries = parse_entries(response.content)

	inserted = 0
	skipped = 0

	for data in entries:
		_doc_name, action = insert_or_update_fbl1n(data)
		if action == "inserted":
			inserted += 1
		else:
			skipped += 1

	frappe.db.commit()

	return {
		"message": f"Processed {len(entries)} entries (inserted: {inserted}, skipped duplicates: {skipped})",
		"total": len(entries),
		"inserted": inserted,
		"skipped": skipped,
	}


def sync_fbl1n_daily():
	"""
	Scheduler method - runs daily.
	Fetches today's SAP FBL1N data and inserts into the doctype.
	"""
	today = datetime.today().strftime("%Y%m%d")
	frappe.logger().info(f"SAP FBL1N daily sync started for date: {today}")

	try:
		result = fetch_fbl1n_data(augdt=today)
		frappe.logger().info(f"SAP FBL1N daily sync result: {result}")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "SAP FBL1N Daily Sync Error")

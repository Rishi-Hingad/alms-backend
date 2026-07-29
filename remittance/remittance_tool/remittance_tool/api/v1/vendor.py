"""SAP-side vendor sync API for Remittance Vendor.

Endpoints (all under remittance_tool.remittance_tool.api.v1.vendor):
  - upsert_vendor   : create or update one or many vendors
  - block_vendor    : mark one or many vendors as disabled (soft block)
  - unblock_vendor  : clear the disabled flag
  - delete_vendor   : hard delete if not referenced; otherwise soft-block

Authentication for all endpoints: HTTP Basic Auth using base64(api_key:api_secret).
The bench-execute path (no HTTP request) is allowed for admin scripts.

See VENDOR_API.md (next to this file) for the full request/response contract.
"""
from datetime import datetime

import frappe
from frappe import _


VENDOR_FIELD_ALIASES = {
	# Vendor identity
	"vendor": "vendor_code",
	"vendor code": "vendor_code",
	"vendor_code": "vendor_code",
	"lifnr": "vendor_code",
	"name": "vendor_name",
	"vendor name": "vendor_name",
	"vendor_name": "vendor_name",
	"name1": "vendor_name",
	# State / region
	"state": "state",
	"bezei": "state",
	"state code": "state_code",
	"state_code": "state_code",
	"regio": "state_code",
	# Tax identifiers
	"gstn no": "gstn_no",
	"gstn_no": "gstn_no",
	"gst no": "gstn_no",
	"gst_no": "gstn_no",
	"stcd3": "gstn_no",
	"pan no": "pan",
	"pan": "pan",
	"j 1ipanno": "pan",
	"j_1ipanno": "pan",
	# GST classification
	"vendor gst classification": "vendor_gst_classification",
	"vendor_gst_classification": "vendor_gst_classification",
	"vgclass": "vendor_gst_classification",
	# Address lines
	"address01": "address01",
	"address1": "address01",
	"str suppl1": "address01",
	"str_suppl1": "address01",
	"address02": "address02",
	"address2": "address02",
	"str suppl2": "address02",
	"str_suppl2": "address02",
	"address03": "address03",
	"address3": "address03",
	"street": "address03",
	"address04": "address04",
	"address4": "address04",
	"str suppl3": "address04",
	"str_suppl3": "address04",
	"address05": "address05",
	"address5": "address05",
	"location": "address05",
	# City / pincode / country
	"city": "city_district",
	"city1": "city_district",
	"city_district": "city_district",
	"town city district": "city_district",
	"pincode": "pincode",
	"pin code": "pincode",
	"post code1": "pincode",
	"post_code1": "pincode",
	"country": "country",
	# Contact
	"contact no": "contact_no",
	"contact_no": "contact_no",
	"telf1": "contact_no",
	"alternate no": "alternate_no",
	"alterenate no": "alternate_no",
	"alternate_no": "alternate_no",
	"telf2": "alternate_no",
	"email-id": "email_id",
	"email id": "email_id",
	"email_id": "email_id",
	"smtp addr": "email_id",
	"smtp_addr": "email_id",
	# Misc
	"remark": "remark",
	"created on": "created_on",
	"created_on": "created_on",
	"erdat": "created_on",
	"c.code": "c_code",
	"c code": "c_code",
	"c_code": "c_code",
	"bukrs": "c_code",
	"count": "count",
	"zcount": "count",
	"currency": "currency",
	"waers": "currency",
	"account group": "account_group",
	"account_group": "account_group",
	"ktokk": "account_group",
	"type of industr": "type_of_industry",
	"type of industry": "type_of_industry",
	"type_of_industry": "type_of_industry",
	"j 1kftind": "type_of_industry",
	"j_1kftind": "type_of_industry",
	"payment term": "terms_of_payment",
	"terms of payment": "terms_of_payment",
	"terms_of_payment": "terms_of_payment",
	"zterm": "terms_of_payment",
	"payment term desc": "payment_term_description",
	"payment term description": "payment_term_description",
	"payment_term_description": "payment_term_description",
	"text1": "payment_term_description",
	"reconciliation acco": "reconciliation_account",
	"reconciliation account": "reconciliation_account",
	"reconciliation_account": "reconciliation_account",
	"akont": "reconciliation_account",
}

# Doctype name used for SAP Mapper lookup (admin-configurable overlay).
_SAP_MAPPER_TARGET_DOCTYPE = "Remittance Vendor"
_SAP_MAPPER_CACHE_KEY = "sap_mapper_aliases:"

VENDOR_FIELDS = {
	"vendor_code",
	"vendor_name",
	"state",
	"state_code",
	"gstn_no",
	"pan",
	"vendor_gst_classification",
	"address01",
	"address02",
	"address03",
	"address04",
	"address05",
	"city_district",
	"pincode",
	"country",
	"contact_no",
	"alternate_no",
	"email_id",
	"remark",
	"created_on",
	"c_code",
	"count",
	"currency",
	"account_group",
	"type_of_industry",
	"terms_of_payment",
	"payment_term_description",
	"reconciliation_account",
}


# ─────────────────────────────────────────────────────────────────────────────
# Auth + payload helpers
# ─────────────────────────────────────────────────────────────────────────────

def _assert_authenticated_request():
	"""Require Frappe authentication for HTTP calls.

	Frappe validates Basic Auth as base64(api_key:api_secret) before whitelisted
	methods run. This guard keeps the contract explicit and still allows
	bench-execute calls for admin/test scripts (no request object).
	"""
	if not getattr(frappe.local, "request", None):
		return

	if frappe.session.user in ("", "Guest"):
		frappe.throw(_("Authentication required"), frappe.AuthenticationError)


def _normalize_key(key):
	return " ".join(str(key).strip().replace("_", " ").replace(".", " ").split()).lower()


def _load_sap_field_aliases(target_doctype):
	"""Load admin-configured SAP field → ERP field mapping from the SAP Mapper doctype.

	Allows the SAP team to add/change SAP field mappings via the UI without
	a code deploy. The result overlays VENDOR_FIELD_ALIASES — same key wins
	from this map. Cached for 5 minutes; cache is invalidated when an admin
	saves the SAP Mapper (see hooks.py).
	"""
	cache = frappe.cache()
	cache_key = _SAP_MAPPER_CACHE_KEY + target_doctype
	cached = cache.get_value(cache_key)
	if cached is not None:
		return cached

	mapping = {}
	try:
		mapper_name = frappe.db.get_value(
			"SAP Mapper", {"doctype_name": target_doctype}, "name"
		)
		if mapper_name:
			rows = frappe.get_all(
				"SAP Mapper Table",
				filters={"parent": mapper_name, "parenttype": "SAP Mapper"},
				fields=["sap_field", "erp_field"],
			)
			for row in rows:
				if row.sap_field and row.erp_field:
					mapping[_normalize_key(row.sap_field)] = row.erp_field
	except Exception:
		# Doctype might not exist in some envs — fall back silently to hardcoded aliases.
		frappe.log_error(
			frappe.get_traceback(),
			f"SAP Mapper alias load failed for {target_doctype}",
		)

	cache.set_value(cache_key, mapping, expires_in_sec=300)
	return mapping


def _resolve_field_alias(key, sap_mapper_overlay):
	"""SAP Mapper overlay wins over hardcoded aliases for the same normalized key."""
	normalized = _normalize_key(key)
	return (
		sap_mapper_overlay.get(normalized)
		or VENDOR_FIELD_ALIASES.get(normalized)
		or VENDOR_FIELD_ALIASES.get(str(key).strip())
	)


def invalidate_sap_mapper_cache(doc, method=None):
	"""hooks.py callback: drop the cached aliases when SAP Mapper changes."""
	target = getattr(doc, "doctype_name", None) if doc else None
	if target:
		frappe.cache().delete_value(_SAP_MAPPER_CACHE_KEY + target)


def _get_payload(*, data=None, vendors=None, payload_kwarg=None):
	payload = data if data is not None else (vendors if vendors is not None else payload_kwarg)

	request = getattr(frappe.local, "request", None)
	if payload is None and request:
		payload = request.get_json(silent=True)

	if payload is None:
		payload = getattr(frappe.local, "form_dict", None)

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)

	if isinstance(payload, dict) and "data" in payload and len(payload) == 1:
		payload = payload.get("data")

	if isinstance(payload, dict) and "vendors" in payload:
		payload = payload.get("vendors")

	return payload


def _parse_date(value):
	if not value:
		return None

	value = str(value).strip()
	if len(value) == 8 and value.isdigit():
		value = f"{value[:4]}-{value[4:6]}-{value[6:]}"

	for date_format in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
		try:
			return datetime.strptime(value, date_format).date()
		except ValueError:
			pass

	frappe.throw(_("Invalid Created On date: {0}").format(value))


def _resolve_country(value):
	if not value:
		return None

	value = str(value).strip()
	if frappe.db.exists("Remittance Country", value):
		return value

	for fieldname in ("country_name", "country_code", "iso_code"):
		country = frappe.db.get_value("Remittance Country", {fieldname: value}, "name")
		if country:
			return country

	frappe.throw(_("Country '{0}' does not exist in Remittance Country").format(value))


def _normalize_vendor_payload(row):
	if not isinstance(row, dict):
		frappe.throw(_("Each vendor entry must be a JSON object"))

	values = {}
	ignored_fields = []
	sap_mapper_overlay = _load_sap_field_aliases(_SAP_MAPPER_TARGET_DOCTYPE)

	for key, value in row.items():
		if value is None:
			continue

		fieldname = _resolve_field_alias(key, sap_mapper_overlay)

		if not fieldname or fieldname not in VENDOR_FIELDS:
			ignored_fields.append(key)
			continue

		if isinstance(value, str):
			value = value.strip()

		if fieldname == "count":
			value = int(value or 0)
		elif fieldname == "created_on":
			value = _parse_date(value)
		elif fieldname == "country":
			value = _resolve_country(value)

		values[fieldname] = value

	return values, ignored_fields


def _extract_vendor_keys(payload):
	"""Accept several payload shapes and return a list of {vendor_code, c_code} dicts.

	Uses the same alias resolution as upsert (including the SAP Mapper overlay)
	so the SAP team can send raw field names like LIFNR/BUKRS to block, unblock
	and delete endpoints too — not only the ERP fieldnames.

	Vendor identity is composite — the same vendor_code can exist under different
	company codes (c_code) and they are distinct records.
	"""
	sap_mapper_overlay = _load_sap_field_aliases(_SAP_MAPPER_TARGET_DOCTYPE)

	def _resolve_one(item):
		if not isinstance(item, dict):
			return None
		vendor_code = None
		c_code = None
		for key, value in item.items():
			if value in (None, ""):
				continue
			fieldname = _resolve_field_alias(key, sap_mapper_overlay)
			if fieldname == "vendor_code" and not vendor_code:
				vendor_code = value
			elif fieldname == "c_code" and not c_code:
				c_code = value
		if not vendor_code:
			return None
		return {"vendor_code": vendor_code, "c_code": c_code}

	if isinstance(payload, dict):
		if "vendors" in payload:
			return _extract_vendor_keys(payload["vendors"])
		resolved = _resolve_one(payload)
		return [resolved] if resolved else []
	if isinstance(payload, list):
		out = []
		for item in payload:
			resolved = _resolve_one(item)
			if resolved:
				out.append(resolved)
		return out
	return []


def _vendor_name_from_keys(vendor_code, c_code):
	"""Resolve the Remittance Vendor primary-key name from the composite (vendor_code, c_code)."""
	if not vendor_code or not c_code:
		return None
	return frappe.db.get_value(
		"Remittance Vendor",
		{"vendor_code": vendor_code, "c_code": c_code},
		"name",
	)


def _is_vendor_referenced(vendor_name):
	"""Return True if the vendor is referenced by any active business document.

	Uses Frappe's standard link-tracker so newly added link references work
	without changes here.
	"""
	links = frappe.get_all(
		"DocField",
		filters={"fieldtype": "Link", "options": "Remittance Vendor"},
		fields=["parent", "fieldname"],
	)
	for link in links:
		if link.parent == "Remittance Vendor":
			continue
		try:
			if frappe.db.count(link.parent, {link.fieldname: vendor_name}) > 0:
				return True
		except Exception:
			# parent doctype may not have a queryable table (virtual doctype etc.)
			continue
	return False


# ─────────────────────────────────────────────────────────────────────────────
# Per-row workers (raise on error; caller catches)
# ─────────────────────────────────────────────────────────────────────────────

def _upsert_vendor_row(row):
	values, ignored_fields = _normalize_vendor_payload(row)

	vendor_code = values.get("vendor_code")
	c_code = values.get("c_code")
	if not vendor_code:
		frappe.throw(_("Vendor code is required"))
	if not c_code:
		frappe.throw(_("Company Code (C.Code) is required — vendor identity is composite (vendor_code + c_code)"))

	existing_name = _vendor_name_from_keys(vendor_code, c_code)

	if existing_name:
		doc = frappe.get_doc("Remittance Vendor", existing_name)
		action = "updated"
	else:
		if not values.get("vendor_name"):
			frappe.throw(_("Vendor name is required for new vendor {0}/{1}").format(vendor_code, c_code))
		doc = frappe.new_doc("Remittance Vendor")
		action = "created"

	doc.update(values)

	if existing_name:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)

	return {
		"vendor_code": doc.vendor_code,
		"c_code": doc.c_code,
		"name": doc.name,
		"action": action,
		"ignored_fields": ignored_fields,
	}


def _block_vendor_row(key, reason=None):
	vendor_code = key.get("vendor_code")
	c_code = key.get("c_code")
	if not vendor_code:
		frappe.throw(_("Vendor code is required"))
	if not c_code:
		frappe.throw(_("Company Code (C.Code) is required"))

	name = _vendor_name_from_keys(vendor_code, c_code)
	if not name:
		frappe.throw(_("Vendor {0} (C.Code {1}) not found").format(vendor_code, c_code))

	stamp = frappe.utils.now()
	reason_text = reason or f"BLOCKED via SAP API at {stamp}"

	frappe.db.set_value(
		"Remittance Vendor",
		name,
		{"disabled": 1, "block_reason": reason_text},
		update_modified=True,
	)
	return {"vendor_code": vendor_code, "c_code": c_code, "name": name, "action": "blocked"}


def _unblock_vendor_row(key):
	vendor_code = key.get("vendor_code")
	c_code = key.get("c_code")
	if not vendor_code:
		frappe.throw(_("Vendor code is required"))
	if not c_code:
		frappe.throw(_("Company Code (C.Code) is required"))

	name = _vendor_name_from_keys(vendor_code, c_code)
	if not name:
		frappe.throw(_("Vendor {0} (C.Code {1}) not found").format(vendor_code, c_code))

	frappe.db.set_value(
		"Remittance Vendor",
		name,
		{"disabled": 0, "block_reason": ""},
		update_modified=True,
	)
	return {"vendor_code": vendor_code, "c_code": c_code, "name": name, "action": "unblocked"}


def _delete_vendor_row(key, reason=None, force=False):
	"""Hard-delete if no references; otherwise soft-block.

	`force=True` will hard delete even if referenced (use only for SAP cleanup).
	"""
	vendor_code = key.get("vendor_code")
	c_code = key.get("c_code")
	if not vendor_code:
		frappe.throw(_("Vendor code is required"))
	if not c_code:
		frappe.throw(_("Company Code (C.Code) is required"))

	name = _vendor_name_from_keys(vendor_code, c_code)
	if not name:
		# Idempotent — already gone
		return {"vendor_code": vendor_code, "c_code": c_code, "name": None, "action": "already_absent"}

	if not force and _is_vendor_referenced(name):
		stamp = frappe.utils.now()
		reason_text = reason or f"DELETED from SAP at {stamp} (kept as disabled — referenced by other documents)"
		frappe.db.set_value(
			"Remittance Vendor",
			name,
			{"disabled": 1, "block_reason": reason_text},
			update_modified=True,
		)
		return {"vendor_code": vendor_code, "c_code": c_code, "name": name, "action": "soft_deleted"}

	frappe.delete_doc("Remittance Vendor", name, ignore_permissions=True, force=1)
	return {"vendor_code": vendor_code, "c_code": c_code, "name": name, "action": "deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# Bulk runner with per-row error capture
# ─────────────────────────────────────────────────────────────────────────────

def _run_bulk(rows, worker):
	"""Run worker over rows. Each row is committed independently so a single
	failure doesn't roll back successful rows in the same batch.
	"""
	results = []
	succeeded = 0
	failed = 0

	for row in rows:
		savepoint = f"sp_{frappe.generate_hash(length=8)}"
		try:
			frappe.db.savepoint(savepoint)
			result = worker(row)
			frappe.db.commit()
			result["status"] = "success"
			succeeded += 1
		except Exception as exc:
			frappe.db.rollback(save_point=savepoint)
			frappe.log_error(frappe.get_traceback(), f"Vendor API error ({getattr(worker, '__name__', 'worker')})")
			ref_code = None
			ref_ccode = None
			if isinstance(row, dict):
				ref_code = row.get("vendor_code")
				ref_ccode = row.get("c_code")
			result = {
				"status": "error",
				"error": str(exc),
				"vendor_code": ref_code,
				"c_code": ref_ccode,
			}
			failed += 1
		results.append(result)

	return {
		"status": "success" if failed == 0 else ("partial" if succeeded else "failed"),
		"count": len(results),
		"succeeded": succeeded,
		"failed": failed,
		"results": results,
	}


# ─────────────────────────────────────────────────────────────────────────────
# Public endpoints
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist(methods=["GET", "POST"])
def upsert_vendor(data=None, vendors=None):
	"""Create or update Remittance Vendor records from SAP payload.

	Payload shapes accepted:
	  - {"data": {...single vendor...}}
	  - {"vendors": [{...vendor 1...}, {...vendor 2...}]}
	  - [{...vendor 1...}, {...vendor 2...}]
	  - {...single vendor...}
	"""
	request = getattr(frappe.local, "request", None)
	if request and request.method == "GET":
		return {
			"status": "ok",
			"message": "Vendor API is reachable. POST with Basic Auth to create or update vendors.",
		}

	_assert_authenticated_request()

	payload = _get_payload(data=data, vendors=vendors)
	if not payload:
		frappe.throw(_("Vendor payload is required"))

	rows = payload if isinstance(payload, list) else [payload]
	return _run_bulk(rows, _upsert_vendor_row)


def _read_request_body():
	"""Return the parsed JSON body of the current HTTP request (or {})."""
	request = getattr(frappe.local, "request", None)
	if not request:
		return {}
	body = request.get_json(silent=True)
	return body if isinstance(body, dict) else {}


@frappe.whitelist(methods=["POST"])
def block_vendor(vendor_code=None, c_code=None, vendors=None, reason=None):
	"""Mark one or many vendors as disabled (soft block).

	Payload shapes accepted:
	  - {"vendor_code": "V001", "c_code": "1000", "reason": "..."}
	  - {"vendors": [{"vendor_code": "V001", "c_code": "1000"}, ...], "reason": "..."}
	  - [{"vendor_code": "V001", "c_code": "1000"}, ...]

	Vendor identity is composite — both vendor_code and c_code are required for every entry.
	"""
	_assert_authenticated_request()

	body = _read_request_body()
	payload = (
		body
		or vendors
		or ({"vendor_code": vendor_code, "c_code": c_code} if vendor_code else None)
	)

	keys = _extract_vendor_keys(payload)
	if not keys:
		frappe.throw(_("vendor_code + c_code (or a 'vendors' list of objects) is required"))

	if not reason:
		reason = body.get("reason") if isinstance(body, dict) else None

	return _run_bulk(keys, lambda k: _block_vendor_row(k, reason=reason))


@frappe.whitelist(methods=["POST"])
def unblock_vendor(vendor_code=None, c_code=None, vendors=None):
	"""Clear the disabled flag on one or many vendors. Same payload shapes as block_vendor (no reason)."""
	_assert_authenticated_request()

	body = _read_request_body()
	payload = (
		body
		or vendors
		or ({"vendor_code": vendor_code, "c_code": c_code} if vendor_code else None)
	)

	keys = _extract_vendor_keys(payload)
	if not keys:
		frappe.throw(_("vendor_code + c_code (or a 'vendors' list of objects) is required"))

	return _run_bulk(keys, _unblock_vendor_row)


@frappe.whitelist(methods=["POST"])
def delete_vendor(vendor_code=None, c_code=None, vendors=None, reason=None, force=False):
	"""Delete one or many vendors.

	Behavior per vendor:
	  - If not referenced by any other document -> hard delete
	  - If referenced and force=False -> soft-block (disabled=1) with reason
	  - If force=True -> hard delete regardless (use with caution)

	Same payload shapes as block_vendor, with optional `reason` and `force`.
	"""
	_assert_authenticated_request()

	body = _read_request_body()
	payload = (
		body
		or vendors
		or ({"vendor_code": vendor_code, "c_code": c_code} if vendor_code else None)
	)

	keys = _extract_vendor_keys(payload)
	if not keys:
		frappe.throw(_("vendor_code + c_code (or a 'vendors' list of objects) is required"))

	if isinstance(body, dict):
		reason = reason or body.get("reason")
		if not force:
			force = body.get("force")

	force = bool(force) if isinstance(force, (bool, int)) else str(force).lower() in ("1", "true", "yes")

	return _run_bulk(keys, lambda k: _delete_vendor_row(k, reason=reason, force=force))

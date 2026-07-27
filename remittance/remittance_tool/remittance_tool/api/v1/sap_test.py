"""SAP fetch test helpers — used to verify the request without risking auth lockout."""

from datetime import datetime

import frappe

from remittance_tool.remittance_tool.api.v1.fetch_fbl1n_data import (
	build_request,
	fetch_fbl1n_data,
)


def _mask(s, keep=2):
	if not s:
		return ""
	s = str(s)
	if len(s) <= keep * 2:
		return "*" * len(s)
	return s[:keep] + "*" * (len(s) - keep * 2) + s[-keep:]


def dry_run(augdt=None, lifnr=None, bukrs=None):
	"""Print the exact request that would be sent — no call made."""
	settings = frappe.get_doc("SAP Setting")

	if not augdt:
		augdt = datetime.today().strftime("%Y%m%d")

	url, headers, params, auth = build_request(settings, augdt, lifnr=lifnr, bukrs=bukrs)

	pwd = settings.get_password("auth_user_pass", raise_exception=False)
	pwd_set = bool(settings.auth_user_name and pwd)

	out = {
		"would_call": "GET " + url,
		"query_params": params,
		"request_headers": {k: v for k, v in headers.items() if k.lower() != "authorization"},
		"basic_auth_user": settings.auth_user_name or None,
		"basic_auth_password_set": pwd_set,
		"basic_auth_password_masked": _mask(pwd) if pwd_set else None,
		"settings_summary": {
			"url": settings.url,
			"sap_client": getattr(settings, "sap_client", None),
			"default_lifnr": settings.lifnr,
			"default_bukrs": settings.bukrs,
			"default_augdt": settings.augdt,
		},
		"warnings": [],
	}

	if not settings.url:
		out["warnings"].append("SAP Setting URL is empty — fetch would fail with 'URL is missing'.")
	if not pwd_set and not settings.authorization_key:
		out["warnings"].append("Neither Basic Auth (user+pass) nor Authorization key is set.")
	if not (settings.lifnr or lifnr):
		out["warnings"].append("LIFNR is empty — SAP may reject or return 0 rows.")
	if not (settings.bukrs or bukrs):
		out["warnings"].append("BUKRS is empty — SAP may reject or return 0 rows.")

	print("=" * 70)
	print("SAP FBL1N — DRY RUN (no request sent)")
	print("=" * 70)
	for k, v in out.items():
		if k == "warnings":
			continue
		print(f"  {k}: {v}")
	if out["warnings"]:
		print("-" * 70)
		print("WARNINGS:")
		for w in out["warnings"]:
			print(f"  ⚠ {w}")
	print("=" * 70)
	return out


def connectivity_check():
	"""
	Hit the SAP URL with NO credentials. Expect 401 Unauthorized.
	A failed login attempt is only counted when wrong credentials are sent;
	sending none does NOT count toward lockout, so this is safe.
	"""
	import requests

	settings = frappe.get_doc("SAP Setting")
	if not settings.url:
		print("⚠ SAP Setting URL is empty.")
		return {"status": "fail", "reason": "url_missing"}

	url = settings.url
	print("=" * 70)
	print("SAP CONNECTIVITY CHECK (no credentials sent — safe)")
	print("=" * 70)
	print(f"  URL: GET {url}")

	try:
		r = requests.get(url, timeout=15, verify=False, allow_redirects=False)
	except requests.exceptions.ConnectTimeout:
		print("  ✖ Connection timeout — server unreachable from this host.")
		return {"status": "timeout"}
	except requests.exceptions.ConnectionError as e:
		print(f"  ✖ Connection error — {str(e)[:120]}")
		return {"status": "connect_error", "error": str(e)[:200]}
	except Exception as e:
		print(f"  ✖ Other error — {str(e)[:120]}")
		return {"status": "error", "error": str(e)[:200]}

	print(f"  HTTP: {r.status_code} {r.reason}")
	server = r.headers.get("Server", "")
	www_auth = r.headers.get("WWW-Authenticate", "")
	if server:
		print(f"  Server header: {server}")
	if www_auth:
		print(f"  WWW-Authenticate: {www_auth}")

	if r.status_code == 401:
		print("  ✓ Server reachable and requires auth — exactly what we want.")
		print("    Safe to proceed to real_call_one() if password is current.")
		return {"status": "ok_401", "server": server, "www_auth": www_auth}

	if r.status_code in (200, 302, 303):
		print("  ⚠ Server replied without requiring auth — unexpected for SAP.")
		return {"status": "unexpected_open", "code": r.status_code}

	print(f"  ⚠ Unexpected HTTP {r.status_code}.")
	print(f"    Body (first 300 chars): {r.text[:300]}")
	return {"status": "unexpected", "code": r.status_code}


def real_call_one(augdt=None, lifnr=None, bukrs=None):
	"""
	Send ONE real SAP request. Use only after a successful dry_run.
	"""
	settings = frappe.get_doc("SAP Setting")
	if not settings.url:
		frappe.throw("SAP Setting URL is missing — fix before trying.")
	if not (settings.auth_user_name and settings.get_password("auth_user_pass", raise_exception=False)):
		frappe.throw("Basic Auth user/password not set — fix before trying (lockout risk).")

	if lifnr:
		settings.lifnr = lifnr
	if bukrs:
		settings.bukrs = bukrs

	print("=" * 70)
	print(f"SAP FBL1N — REAL CALL  augdt={augdt or 'today'}")
	print("=" * 70)
	result = fetch_fbl1n_data(augdt=augdt)
	print(f"  result: {result}")
	print("=" * 70)
	return result

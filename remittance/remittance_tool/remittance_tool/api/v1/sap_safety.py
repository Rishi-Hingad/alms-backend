"""
SAP fetch circuit breaker.

After any 401 from SAP, we engage the breaker so subsequent fetch attempts
are refused locally — preventing accidental re-tries from triggering an
SAP user lockout. The breaker persists in Frappe cache (Redis) until
manually reset via reset_circuit().
"""

import json
from datetime import datetime

import frappe

CACHE_KEY = "sap_circuit_breaker"


def _get_state():
	raw = frappe.cache().get_value(CACHE_KEY)
	if not raw:
		return {"open": False, "reason": None, "ts": None, "fail_count": 0}
	try:
		return json.loads(raw)
	except Exception:
		return {"open": False, "reason": None, "ts": None, "fail_count": 0}


def _set_state(state):
	frappe.cache().set_value(CACHE_KEY, json.dumps(state))


def assert_circuit_closed():
	"""Raise if breaker is open. Call before any SAP HTTP call."""
	state = _get_state()
	if state.get("open"):
		frappe.throw(
			f"SAP fetch is BLOCKED locally to prevent account lockout.\n"
			f"Reason: {state.get('reason') or 'previous failure'}\n"
			f"Failures so far: {state.get('fail_count', 0)}\n"
			f"Last failure at: {state.get('ts')}\n\n"
			f"To unlock: have a SAP admin verify/reset the WF-BATCH password, "
			f"update SAP Setting, then run:\n"
			f"  bench --site remittance execute "
			f"remittance_tool.remittance_tool.api.v1.sap_safety.reset_circuit"
		)


def engage_circuit(reason):
	"""Flip the breaker open. Called automatically on 401."""
	state = _get_state()
	state["open"] = True
	state["reason"] = str(reason)[:300]
	state["ts"] = datetime.now().isoformat(timespec="seconds")
	state["fail_count"] = (state.get("fail_count") or 0) + 1
	_set_state(state)


@frappe.whitelist()
def circuit_status():
	"""Show current breaker state. Safe to run any time."""
	state = _get_state()
	if state.get("open"):
		print("=" * 70)
		print("SAP CIRCUIT BREAKER: OPEN — fetch is blocked")
		print("=" * 70)
		print(f"  Reason     : {state.get('reason')}")
		print(f"  Failures   : {state.get('fail_count')}")
		print(f"  Last fail  : {state.get('ts')}")
		print("=" * 70)
	else:
		print("SAP CIRCUIT BREAKER: closed (fetch allowed).")
	return state


@frappe.whitelist()
def reset_circuit():
	"""Clear the breaker. Use ONLY after SAP admin confirms the password is current."""
	frappe.cache().delete_value(CACHE_KEY)
	print("SAP circuit breaker reset. Fetch is allowed again.")
	return {"status": "reset"}

"""Permission query conditions used by hooks.py.

Hides superseded/outdated RE KR Entry rows from anyone except Administrator
and System Manager. Outdated rows are kept in the table for audit/history.
"""

import frappe


def fbl1n_query_conditions(user=None):
	"""Return a SQL WHERE-fragment to hide is_outdated=1 rows for non-admins."""
	user = user or frappe.session.user
	if user == "Administrator":
		return ""
	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return ""
	# tabRE KR Entry alias is `tabRE KR Entry` in list-view queries
	return "(`tabRE KR Entry`.is_outdated = 0)"


def fbl1n_has_permission(doc, user=None, ptype=None):
	"""Same logic for direct doc access — admin sees all, others can't read outdated rows."""
	user = user or frappe.session.user
	if not doc.get("is_outdated"):
		return True
	if user == "Administrator":
		return True
	if "System Manager" in frappe.get_roles(user):
		return True
	return False

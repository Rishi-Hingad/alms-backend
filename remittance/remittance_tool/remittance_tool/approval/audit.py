"""Quick verification that outdated RE KR Entry is hidden from non-admins."""

import frappe


def run():
	out = []

	# Insert a test outdated row to make sure something exists to hide
	test_name = "TEST-OUTDATED-9999"
	if not frappe.db.exists("RE KR Entry", test_name):
		doc = frappe.get_doc(
			{
				"doctype": "RE KR Entry",
				"bukrs": "9999",
				"belnr": "9999999999",
				"lifnr": "0000000000",
				"name1": "AUDIT TEST",
				"is_outdated": 1,
			}
		)
		doc.insert(ignore_permissions=True)
		# Force the canonical name
		if doc.name != test_name:
			frappe.rename_doc("RE KR Entry", doc.name, test_name, ignore_permissions=True)
		frappe.db.commit()
	out.append(f"Outdated test row in DB: {frappe.db.exists('RE KR Entry', test_name)}")

	# Count from each user's perspective
	frappe.set_user("Administrator")
	admin_count = frappe.db.count("RE KR Entry", {"is_outdated": 1})
	out.append(f"Administrator sees outdated rows in DB: {admin_count}")

	for u in ("maker@test.local", "checker1@test.local"):
		frappe.set_user(u)
		# get_list applies permission_query_conditions
		rows = frappe.get_list(
			"RE KR Entry",
			filters={"is_outdated": 1},
			fields=["name"],
			ignore_permissions=False,
			limit_page_length=10,
		)
		out.append(f"{u} sees outdated rows via get_list: {len(rows)}")

	frappe.set_user("Administrator")
	# Cleanup test row
	frappe.delete_doc("RE KR Entry", test_name, force=1, ignore_permissions=True)
	frappe.db.commit()
	out.append("Test row cleaned up.")

	print("\n".join(out))
	return out

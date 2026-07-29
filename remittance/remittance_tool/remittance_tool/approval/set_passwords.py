import frappe
from frappe.utils.password import update_password


def run():
	creds = {
		"maker@test.local": "Maker@123",
		"checker1@test.local": "Checker1@123",
		"checker2@test.local": "Checker2@123",
	}
	for user, pwd in creds.items():
		update_password(user, pwd)
	frappe.db.commit()
	return creds

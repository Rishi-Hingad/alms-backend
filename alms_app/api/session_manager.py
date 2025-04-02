import frappe

def add_custom_session_data(login_manager):
    if frappe.session.user and frappe.session.user != "Guest":
        # designation = frappe.db.get_value("User", frappe.session.user, "designation")
        # frappe.local.session.data["designation"] = designation
        # print("Session Store",designation)
        frappe.local.session_obj.update()

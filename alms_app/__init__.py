__version__ = "0.0.1"

# import frappe

# try:
#     from alms_app.utils.custom_send_email import custom_sendmail
#     # Override frappe's sendmail with your custom one
#     frappe.sendmail = custom_sendmail
#     frappe.logger().info("✅ Patched frappe.sendmail with custom_sendmail")
# except Exception as e:
#     # Fail safe: don’t break the app if import/patch fails
#     frappe.logger().error(f"❌ Failed to patch frappe.sendmail: {e}")

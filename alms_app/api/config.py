import frappe

@frappe.whitelist(allow_guest=True)
def get_site_config_values():
    config = frappe.get_site_config()  # This reads both site_config and common_site_config
    return {
        "redis_cache": config.get("saurabh"),
        "socketio_port": config.get("socketio_port", 9000),
        # Add more keys as needed
    }
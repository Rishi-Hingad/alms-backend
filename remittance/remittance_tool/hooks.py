app_name = "remittance_tool"
app_title = "Remittance Tool"
app_publisher = "Saurabh Tiwari"
app_description = "A tool for remittance calculation that simplifies the work of a Chartered Accountant."
app_email = "saurabh.tiwari1@merillife.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "remittance_tool",
# 		"logo": "/assets/remittance_tool/logo.png",
# 		"title": "Remittance Tool",
# 		"route": "/remittance_tool",
# 		"has_permission": "remittance_tool.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/remittance_tool/css/remittance_tool.css"
# app_include_js = "/assets/remittance_tool/js/remittance_tool.js"

app_include_js = [
	"/assets/remittance_tool/js/remittance_utils.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/remittance_tool/css/remittance_tool.css"
# web_include_js = "/assets/remittance_tool/js/remittance_tool.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "remittance_tool/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "remittance_tool/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "remittance_tool.utils.jinja_methods",
# 	"filters": "remittance_tool.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "remittance_tool.install.before_install"
# after_install = "remittance_tool.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "remittance_tool.uninstall.before_uninstall"
# after_uninstall = "remittance_tool.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "remittance_tool.utils.before_app_install"
# after_app_install = "remittance_tool.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "remittance_tool.utils.before_app_uninstall"
# after_app_uninstall = "remittance_tool.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "remittance_tool.notifications.get_notification_config"

# Permissions
# -----------
# Hide outdated/superseded RE KR Entry rows from non-admins.

permission_query_conditions = {
	"RE KR Entry": "remittance_tool.remittance_tool.permissions.fbl1n_query_conditions",
}

has_permission = {
	"RE KR Entry": "remittance_tool.remittance_tool.permissions.fbl1n_has_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Remittance Form 15 CB": {
		"on_update": "remittance_tool.remittance_tool.approval.router.trigger_approval_if_matrix_exists",
		"on_submit": "remittance_tool.remittance_tool.approval.router.trigger_approval_if_matrix_exists",
		"on_trash": "remittance_tool.remittance_tool.approval.router.cleanup_approval_entries_on_trash",
	},
	"SAP Mapper": {
		"on_update": "remittance_tool.remittance_tool.api.v1.vendor.invalidate_sap_mapper_cache",
		"on_trash": "remittance_tool.remittance_tool.api.v1.vendor.invalidate_sap_mapper_cache",
	},
}

# Scheduled Tasks
# ---------------

# SAP FBL1N daily sync — disabled
# scheduler_events = {
# 	"daily": ["remittance_tool.remittance_tool.api.v1.fetch_fbl1n_data.sync_fbl1n_daily"],
# }

# Testing
# -------

# before_tests = "remittance_tool.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "remittance_tool.event.get_events"
# }

override_whitelisted_methods = {
	"frappe.core.doctype.user.user.reset_password": "remittance_tool.remittance_tool.api.auth.reset_password",
}

#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "remittance_tool.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["remittance_tool.utils.before_request"]
# after_request = ["remittance_tool.utils.after_request"]

# Job Events
# ----------
# before_job = ["remittance_tool.utils.before_job"]
# after_job = ["remittance_tool.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"remittance_tool.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

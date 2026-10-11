app_name = "frappin"
app_title = "Frappin"
app_publisher = "Nitish"
app_description = "Frappin a smart, user-specific clipboard manager for Frappe and ERPNext that lets you save, search, organize, and reuse copied content instantly."
app_email = "devlprnitish@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "frappin",
# 		"logo": "/assets/frappin/logo.png",
# 		"title": "Frappin",
# 		"route": "/frappin",
# 		"has_permission": "frappin.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# Mount the Vue widget on every Desk page.
app_include_css = ["frappin_widget.bundle.css"]
app_include_js = ["frappin_widget.bundle.js"]

# Mount the same Vue widget on website pages.
web_include_css = ["frappin_widget.bundle.css"]
web_include_js = ["frappin_widget.bundle.js"]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "frappin/public/scss/website"

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
# app_include_icons = "frappin/public/icons.svg"

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
# 	"methods": "frappin.utils.jinja_methods",
# 	"filters": "frappin.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "frappin.install.before_install"
# after_install = "frappin.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "frappin.uninstall.before_uninstall"
# after_uninstall = "frappin.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "frappin.utils.before_app_install"
# after_app_install = "frappin.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "frappin.utils.before_app_uninstall"
# after_app_uninstall = "frappin.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "frappin.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["frappin.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

permission_query_conditions = {
	"Frappin Clipboard Item": "frappin.frappin.doctype.frappin_clipboard_item.frappin_clipboard_item.get_permission_query_conditions",
	"Frappin Collection": "frappin.frappin.doctype.frappin_collection.frappin_collection.get_permission_query_conditions",
}

has_permission = {
	"Frappin Clipboard Item": "frappin.frappin.doctype.frappin_clipboard_item.frappin_clipboard_item.has_permission",
	"Frappin Collection": "frappin.frappin.doctype.frappin_collection.frappin_collection.has_permission",
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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"frappin.tasks.all"
# 	],
# 	"daily": [
# 		"frappin.tasks.daily"
# 	],
# 	"hourly": [
# 		"frappin.tasks.hourly"
# 	],
# 	"weekly": [
# 		"frappin.tasks.weekly"
# 	],
# 	"monthly": [
# 		"frappin.tasks.monthly"
# 	],
# }

scheduler_events = {
	"daily": ["frappin.tasks.delete_expired_clipboard_items"],
}

# Testing
# -------

# before_tests = "frappin.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "frappin.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "frappin.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["frappin.utils.before_request"]
# after_request = ["frappin.utils.after_request"]

# Job Events
# ----------
# before_job = ["frappin.utils.before_job"]
# after_job = ["frappin.utils.after_job"]

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
# 	"frappin.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

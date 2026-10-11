import frappe
from frappe.utils import add_days, cint, now_datetime


def delete_expired_clipboard_items():
	retention_days = cint(frappe.db.get_single_value("Frappin Settings", "retention_days")) or 2
	cutoff = add_days(now_datetime(), -max(1, retention_days))
	now = now_datetime()

	item_names = frappe.db.sql_list(
		"""
		SELECT name
		FROM `tabFrappin Clipboard Item`
		WHERE permanent = 0
		  AND (
			(expires_at IS NOT NULL AND expires_at <= %(now)s)
			OR (
				expires_at IS NULL
				AND COALESCE(last_used_at, creation) <= %(cutoff)s
			)
		  )
		""",
		{"now": now, "cutoff": cutoff},
	)

	for name in item_names:
		frappe.delete_doc("Frappin Clipboard Item", name, ignore_permissions=True)

	return len(item_names)

import re

import frappe
from frappe.utils import cint, now_datetime

from frappin.frappin.doctype.frappin_clipboard_item.frappin_clipboard_item import (
	CONTENT_TYPES,
	MAX_CONTENT_LENGTH,
	make_content_hash,
)

URL_PATTERN = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)


def _enabled():
	if not frappe.db.exists("DocType", "Frappin Settings"):
		return False
	return not bool(cint(frappe.db.get_single_value("Frappin Settings", "disabled")))


def _require_user():
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to use Frappin.", frappe.PermissionError)
	if not _enabled():
		frappe.throw("Frappin is disabled.", frappe.PermissionError)


@frappe.whitelist(allow_guest=True)
def get_widget_settings():
	return {
		"enabled": _enabled() and frappe.session.user != "Guest",
		"user": None if frappe.session.user == "Guest" else frappe.session.user,
	}


@frappe.whitelist()
def save_clipboard_item(content, title=None, content_type=None, source_doctype=None, source_name=None, source_field=None):
	_require_user()

	content = (content or "").strip()
	if not content:
		return None
	if len(content) > MAX_CONTENT_LENGTH:
		frappe.throw(f"Clipboard content cannot exceed {MAX_CONTENT_LENGTH:,} characters.")

	content_type = content_type or ("url" if URL_PATTERN.fullmatch(content) else "text")
	if content_type not in CONTENT_TYPES:
		frappe.throw("Unsupported clipboard content type.")

	if source_doctype and source_name and not frappe.has_permission(source_doctype, "read", source_name):
		frappe.throw("You cannot save a reference to a document you cannot read.", frappe.PermissionError)

	content_hash = make_content_hash(content, content_type)
	existing = frappe.db.get_value(
		"Frappin Clipboard Item",
		{"owner_user": frappe.session.user, "content_hash": content_hash},
		"name",
	)

	if existing:
		frappe.db.set_value(
			"Frappin Clipboard Item",
			existing,
			{"last_used_at": now_datetime()},
			update_modified=True,
		)
		return {"name": existing, "deduplicated": True}

	doc = frappe.get_doc(
		{
			"doctype": "Frappin Clipboard Item",
			"owner_user": frappe.session.user,
			"title": (title or "").strip() or None,
			"content": content,
			"content_type": content_type,
			"content_hash": content_hash,
			"source_doctype": source_doctype,
			"source_name": source_name,
			"source_field": source_field,
			"last_used_at": now_datetime(),
			"visibility": "private",
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "deduplicated": False}


@frappe.whitelist()
def get_clipboard_items(limit=30):
	_require_user()
	limit = max(1, min(cint(limit) or 30, 100))
	items = frappe.get_list(
		"Frappin Clipboard Item",
		fields=[
			"name",
			"title",
			"content",
			"content_type",
			"pinned",
			"permanent",
			"favorite",
			"source_doctype",
			"source_name",
			"source_field",
			"last_used_at",
			"creation",
		],
		filters={"owner_user": frappe.session.user},
		order_by="pinned desc, last_used_at desc, creation desc",
		limit_page_length=limit,
	)

	return [item for item in items if _can_read_source(item)]


def _owned_item(name):
	doc = frappe.get_doc("Frappin Clipboard Item", name)
	if doc.owner_user != frappe.session.user and frappe.session.user != "Administrator":
		frappe.throw("You cannot change this clipboard item.", frappe.PermissionError)
	return doc


@frappe.whitelist()
def set_item_pinned(name, pinned=1):
	_require_user()
	doc = _owned_item(name)
	value = cint(pinned)
	doc.pinned = value
	doc.permanent = value
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "pinned": bool(value), "permanent": bool(value)}


@frappe.whitelist()
def update_clipboard_item(name, content, title=None):
	_require_user()
	doc = _owned_item(name)
	doc.content = (content or "").strip()
	if title is not None:
		doc.title = (title or "").strip() or None
	doc.last_used_at = now_datetime()
	doc.save(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def delete_clipboard_item(name):
	_require_user()
	doc = _owned_item(name)
	frappe.delete_doc(doc.doctype, doc.name, ignore_permissions=True)
	return {"name": name, "deleted": True}


def _can_read_source(item):
	if not item.source_doctype or not item.source_name:
		return True
	return bool(frappe.has_permission(item.source_doctype, "read", item.source_name))

import re

import frappe
from frappe.utils import cint, now_datetime

from frappin.frappin.doctype.frappin_clipboard_item.frappin_clipboard_item import (
	CONTENT_TYPES,
	MAX_CONTENT_LENGTH,
	make_content_hash,
	normalize_template_content,
)
from frappin.frappin.doctype.frappin_clipboard_item.frappin_clipboard_item import (
	get_template_fields as get_allowed_template_fields,
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


def _validate_collection(collection):
	if not collection:
		return None
	owner_user = frappe.db.get_value("Frappin Collection", collection, "owner_user")
	if owner_user != frappe.session.user:
		frappe.throw("You can only use your own Frappin collections.", frappe.PermissionError)
	return collection


@frappe.whitelist(allow_guest=True)
def get_widget_settings():
	return {
		"enabled": _enabled() and frappe.session.user != "Guest",
		"user": None if frappe.session.user == "Guest" else frappe.session.user,
	}


@frappe.whitelist()
def save_clipboard_item(
	content,
	title=None,
	content_type=None,
	source_doctype=None,
	source_name=None,
	source_field=None,
	share_mode=None,
	users=None,
	pinned=None,
	permanent=None,
	allow_edit=0,
	allow_delete=0,
	collection=None,
):
	_require_user()
	if collection is not None:
		collection = _validate_collection(collection)

	content = (content or "").strip()
	if not content:
		return None
	if len(content) > MAX_CONTENT_LENGTH:
		frappe.throw(f"Clipboard content cannot exceed {MAX_CONTENT_LENGTH:,} characters.")

	content_type = content_type or ("url" if URL_PATTERN.fullmatch(content) else "text")
	if content_type not in CONTENT_TYPES:
		frappe.throw("Unsupported clipboard content type.")
	if content_type == "template":
		content = normalize_template_content(content, source_doctype)
		title = (title or "").strip() or f"{source_doctype} template"

	if source_doctype and source_name and not frappe.has_permission(source_doctype, "read", source_name):
		frappe.throw("You cannot save a reference to a document you cannot read.", frappe.PermissionError)

	content_hash = make_content_hash(content, content_type, source_doctype)
	existing = frappe.db.get_value(
		"Frappin Clipboard Item",
		{"owner_user": frappe.session.user, "content_hash": content_hash},
		"name",
	)

	if existing:
		updates = {"last_used_at": now_datetime()}
		if pinned is not None:
			updates["pinned"] = cint(pinned)
		if permanent is not None:
			updates["permanent"] = cint(permanent)
		if collection is not None:
			updates["collection"] = collection or None
		frappe.db.set_value(
			"Frappin Clipboard Item",
			existing,
			updates,
			update_modified=True,
		)
		if share_mode is not None:
			_set_item_sharing(_owned_item(existing), share_mode, users, allow_edit, allow_delete)
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
			"pinned": cint(pinned) if pinned is not None else 0,
			"permanent": cint(permanent) if permanent is not None else 0,
			"collection": collection or None,
		}
	)
	doc.insert(ignore_permissions=True)
	if share_mode is not None:
		_set_item_sharing(doc, share_mode, users, allow_edit, allow_delete)
	return {"name": doc.name, "deduplicated": False}


@frappe.whitelist()
def get_clipboard_items(limit=5, start=0, filter_type="all", collection=None):
	_require_user()
	limit = max(1, min(cint(limit) or 5, 20))
	start = max(0, cint(start))
	shared_names = frappe.share.get_shared(
		"Frappin Clipboard Item", user=frappe.session.user, rights=["read"], limit=500
	)
	or_filters = [
		["owner_user", "=", frappe.session.user],
		["visibility", "=", "shared"],
	]
	if shared_names:
		or_filters.append(["name", "in", shared_names])
	filters = []
	if filter_type == "pinned":
		filters.append(["pinned", "=", 1])
	elif filter_type == "recent":
		filters.append(["pinned", "=", 0])
	elif filter_type == "erp_documents":
		filters.append(["source_doctype", "is", "set"])
	if collection:
		filters.append(["collection", "=", collection])

	items = frappe.get_all(
		"Frappin Clipboard Item",
		fields=[
			"name",
			"owner_user",
			"title",
			"content",
			"content_type",
			"pinned",
			"permanent",
			"collection",
			"source_doctype",
			"source_name",
			"source_field",
			"last_used_at",
			"creation",
			"shared_can_edit",
			"shared_can_delete",
		],
		filters=filters,
		or_filters=or_filters,
		order_by="pinned desc, last_used_at desc, creation desc",
		limit_start=start,
		limit_page_length=limit + 1,
	)

	has_more = len(items) > limit
	page_items = items[:limit]
	for item in page_items:
		item.is_owner = item.owner_user == frappe.session.user or frappe.session.user == "Administrator"
		item.can_edit = item.is_owner or bool(item.shared_can_edit)
		item.can_delete = item.is_owner or bool(item.shared_can_delete)
		item.can_share = item.is_owner
	return {
		"items": [item for item in page_items if _can_read_source(item)],
		"has_more": has_more,
		"next_start": start + limit,
	}


@frappe.whitelist()
def get_collections():
	_require_user()
	return frappe.get_all(
		"Frappin Collection",
		filters={"owner_user": frappe.session.user},
		fields=["name", "title"],
		order_by="title asc",
		limit_page_length=100,
	)


@frappe.whitelist()
def create_collection(title):
	_require_user()
	title = (title or "").strip()
	if not title:
		frappe.throw("Collection name is required.")
	if len(title) > 140:
		frappe.throw("Collection name cannot exceed 140 characters.")

	existing = frappe.db.get_value(
		"Frappin Collection",
		{"owner_user": frappe.session.user, "title": title},
		"name",
	)
	if existing:
		return {"name": existing, "title": title, "created": False}

	doc = frappe.get_doc(
		{
			"doctype": "Frappin Collection",
			"title": title,
			"owner_user": frappe.session.user,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "title": doc.title, "created": True}


@frappe.whitelist()
def get_template_doctypes(search=None):
	_require_user()
	filters = {"istable": 0}
	if search:
		filters["name"] = ["like", f"%{str(search).strip()}%"]
	doctypes = frappe.get_all(
		"DocType",
		filters=filters,
		pluck="name",
		order_by="name asc",
		limit_page_length=2000,
	)
	return [
		doctype
		for doctype in doctypes
		if frappe.has_permission(doctype, "create") or frappe.has_permission(doctype, "write")
	]


@frappe.whitelist()
def get_template_fields(doctype):
	_require_user()
	fields = []
	for field in get_allowed_template_fields(doctype):
		if field.fieldtype == "Table" and field.options:
			for child_field in frappe.get_meta(field.options).fields:
				if (
					child_field.fieldname
					and not child_field.hidden
					and not child_field.read_only
					and child_field.fieldtype
					not in {"Button", "Column Break", "Fold", "Heading", "HTML", "Section Break", "Tab Break", "Table"}
				):
					fields.append(
						{
							"fieldname": f"{field.fieldname}[1].{child_field.fieldname}",
							"label": f"{field.label or field.fieldname} row 1 · {child_field.label or child_field.fieldname}",
							"fieldtype": child_field.fieldtype,
							"options": child_field.options,
							"reqd": bool(child_field.reqd),
						}
					)
			continue
		fields.append(
			{
				"fieldname": field.fieldname,
				"label": field.label or field.fieldname,
				"fieldtype": field.fieldtype,
				"options": field.options,
				"reqd": bool(field.reqd),
			}
		)
	return fields


def _owned_item(name):
	doc = frappe.get_doc("Frappin Clipboard Item", name)
	if doc.owner_user != frappe.session.user and frappe.session.user != "Administrator":
		frappe.throw("You cannot change this clipboard item.", frappe.PermissionError)
	return doc


def _user_can_read_item(doc, user=None):
	user = user or frappe.session.user
	if user == "Administrator" or doc.owner_user == user or doc.visibility == "shared":
		return True
	return bool(
		frappe.db.exists(
			"DocShare",
			{
				"share_doctype": doc.doctype,
				"share_name": doc.name,
				"user": user,
				"read": 1,
			},
		)
	)


def _item_for_action(name, action):
	doc = frappe.get_doc("Frappin Clipboard Item", name)
	if doc.owner_user == frappe.session.user or frappe.session.user == "Administrator":
		return doc
	allowed = _user_can_read_item(doc) and bool(doc.get(f"shared_can_{action}"))
	if not allowed:
		frappe.throw(f"You cannot {action} this clipboard item.", frappe.PermissionError)
	return doc


@frappe.whitelist()
def set_item_pinned(name, pinned=1):
	_require_user()
	doc = _owned_item(name)
	value = cint(pinned)
	doc.pinned = value
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "pinned": bool(value)}


@frappe.whitelist()
def set_item_permanent(name, permanent=1):
	_require_user()
	doc = _owned_item(name)
	value = cint(permanent)
	doc.permanent = value
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "permanent": bool(value)}


def _parse_users(users):
	if isinstance(users, str):
		users = frappe.parse_json(users) if users else []
	if not isinstance(users, (list, tuple)):
		return []
	return list(dict.fromkeys(user for user in users if isinstance(user, str) and user))


def _set_item_sharing(doc, share_mode="private", users=None, allow_edit=0, allow_delete=0):
	share_mode = share_mode if share_mode in {"private", "users", "everyone"} else "private"
	requested_users = _parse_users(users) if share_mode == "users" else []
	valid_users = set()
	if requested_users:
		valid_users = set(
			frappe.get_all(
				"User",
				filters={"name": ["in", requested_users], "enabled": 1},
				pluck="name",
			)
		)
	valid_users.discard("Guest")
	valid_users.discard(doc.owner_user)

	existing_shares = frappe.get_all(
		"DocShare",
		filters={"share_doctype": doc.doctype, "share_name": doc.name, "everyone": 0},
		fields=["name", "user"],
	)
	for share in existing_shares:
		if share.user not in valid_users:
			frappe.delete_doc("DocShare", share.name, ignore_permissions=True)

	for user in valid_users:
		frappe.share.add_docshare(
			doc.doctype,
			doc.name,
			user=user,
			read=1,
			flags={"ignore_share_permission": True},
		)

	doc.db_set("visibility", "shared" if share_mode == "everyone" else "private", update_modified=True)
	doc.db_set(
		{
			"shared_can_edit": cint(allow_edit) if share_mode != "private" else 0,
			"shared_can_delete": cint(allow_delete) if share_mode != "private" else 0,
		},
		update_modified=True,
	)
	return {
		"mode": share_mode,
		"users": sorted(valid_users),
		"allow_edit": bool(doc.shared_can_edit),
		"allow_delete": bool(doc.shared_can_delete),
	}


@frappe.whitelist()
def get_shareable_users():
	_require_user()
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "name": ["not in", ["Guest", frappe.session.user]]},
		fields=["name", "full_name"],
		order_by="full_name asc, name asc",
		limit_page_length=200,
	)
	return [{"value": user.name, "label": user.full_name or user.name} for user in users]


@frappe.whitelist()
def get_item_sharing(name):
	_require_user()
	doc = _owned_item(name)
	users = frappe.get_all(
		"DocShare",
		filters={"share_doctype": doc.doctype, "share_name": doc.name, "read": 1, "everyone": 0},
		pluck="user",
	)
	return {
		"mode": "everyone" if doc.visibility == "shared" else ("users" if users else "private"),
		"users": users,
		"allow_edit": bool(doc.shared_can_edit),
		"allow_delete": bool(doc.shared_can_delete),
	}


@frappe.whitelist()
def set_item_sharing(name, share_mode="private", users=None, allow_edit=0, allow_delete=0):
	_require_user()
	return _set_item_sharing(_owned_item(name), share_mode, users, allow_edit, allow_delete)


@frappe.whitelist()
def update_clipboard_item(
	name,
	content,
	title=None,
	collection=None,
	content_type=None,
	source_doctype=None,
):
	_require_user()
	doc = _item_for_action(name, "edit")
	content_type = content_type or doc.content_type
	source_doctype = source_doctype if source_doctype is not None else doc.source_doctype
	doc.content = (
		normalize_template_content(content, source_doctype)
		if content_type == "template"
		else (content or "").strip()
	)
	doc.content_type = content_type
	doc.source_doctype = source_doctype or None
	if title is not None:
		doc.title = (title or "").strip() or None
	if collection is not None:
		doc.collection = collection or None
	doc.last_used_at = now_datetime()
	doc.save(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def delete_clipboard_item(name):
	_require_user()
	doc = _item_for_action(name, "delete")
	frappe.delete_doc(doc.doctype, doc.name, ignore_permissions=True)
	return {"name": name, "deleted": True}


def _can_read_source(item):
	if not item.source_doctype or not item.source_name:
		return True
	return bool(frappe.has_permission(item.source_doctype, "read", item.source_name))

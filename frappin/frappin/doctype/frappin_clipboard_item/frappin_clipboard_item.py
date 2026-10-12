import hashlib
import json
import re

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

MAX_CONTENT_LENGTH = 100_000
CONTENT_TYPES = {"text", "url", "template", "doc_reference"}
TEMPLATE_EXCLUDED_FIELDTYPES = {
	"Button",
	"Column Break",
	"Fold",
	"Geolocation",
	"Heading",
	"HTML",
	"Image",
	"Read Only",
	"Section Break",
	"Signature",
	"Tab Break",
	"Table MultiSelect",
	"Attach",
	"Attach Image",
}
FIELDNAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CHILD_FIELD_PATH_PATTERN = re.compile(
	r"^[A-Za-z_][A-Za-z0-9_]*\[[1-9][0-9]{0,2}\]\.[A-Za-z_][A-Za-z0-9_]*$"
)


def get_template_fields(doctype):
	if not doctype or not frappe.db.exists("DocType", doctype):
		frappe.throw("Choose a valid target DocType.")
	if not (frappe.has_permission(doctype, "create") or frappe.has_permission(doctype, "write")):
		frappe.throw(f"You cannot create or edit {doctype} documents.", frappe.PermissionError)

	meta = frappe.get_meta(doctype)
	writable_permlevels = set(meta.get_permlevel_access("write", user=frappe.session.user))
	return [
		field
		for field in meta.fields
		if field.fieldname
		and not field.hidden
		and not field.read_only
		and field.permlevel in writable_permlevels
		and field.fieldtype not in TEMPLATE_EXCLUDED_FIELDTYPES
	]


def normalize_template_content(content, source_doctype):
	try:
		values = json.loads(content) if isinstance(content, str) else content
	except (TypeError, ValueError):
		frappe.throw("Template values must be valid JSON.")

	if not isinstance(values, dict) or not values:
		frappe.throw("Add at least one field and value to the template.")
	if len(values) > 100:
		frappe.throw("A template can contain at most 100 fields.")

	invalid_fields = sorted(
		fieldname
		for fieldname in values
		if not isinstance(fieldname, str)
		or len(fieldname) > 140
		or not (
			FIELDNAME_PATTERN.fullmatch(fieldname) or CHILD_FIELD_PATH_PATTERN.fullmatch(fieldname)
		)
	)
	if invalid_fields:
		frappe.throw(f"These are not valid Frappe field names: {', '.join(invalid_fields)}")

	for fieldname, value in values.items():
		if not isinstance(fieldname, str) or not isinstance(value, (str, int, float, bool, type(None))):
			frappe.throw("Template fields can only contain simple values.")

	return json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class FrappinClipboardItem(Document):
	def before_insert(self):
		self.owner_user = frappe.session.user

	def validate(self):
		self.content = (self.content or "").strip()
		if not self.content:
			frappe.throw("Clipboard content cannot be empty.")
		if len(self.content) > MAX_CONTENT_LENGTH:
			frappe.throw(f"Clipboard content cannot exceed {MAX_CONTENT_LENGTH:,} characters.")

		self.content_type = self.content_type or "text"
		if self.content_type not in CONTENT_TYPES:
			frappe.throw("Unsupported clipboard content type.")
		if self.content_type == "template":
			self.content = normalize_template_content(self.content, self.source_doctype)

		if not self.is_new():
			owner_user = frappe.db.get_value(self.doctype, self.name, "owner_user")
			if owner_user and self.owner_user != owner_user:
				frappe.throw("Clipboard item ownership cannot be changed.", frappe.PermissionError)

		if self.collection:
			collection_owner = frappe.db.get_value("Frappin Collection", self.collection, "owner_user")
			if collection_owner != self.owner_user:
				frappe.throw("You can only use your own Frappin collections.", frappe.PermissionError)

		if self.source_doctype and self.source_name:
			if not frappe.has_permission(self.source_doctype, "read", self.source_name):
				frappe.throw("You cannot reference a document you cannot read.", frappe.PermissionError)

		self.content_hash = make_content_hash(self.content, self.content_type, self.source_doctype)
		self.last_used_at = self.last_used_at or now_datetime()
		self.visibility = self.visibility or "private"


def make_content_hash(content, content_type="text", source_doctype=None):
	template_scope = f"\0{source_doctype or ''}" if content_type == "template" else ""
	payload = f"{content_type}{template_scope}\0{content}".encode()
	return hashlib.sha256(payload).hexdigest()


def get_permission_query_conditions(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return ""
	escaped_user = frappe.db.escape(user)
	return (
		f"(`tabFrappin Clipboard Item`.`owner_user` = {escaped_user} "
		"OR `tabFrappin Clipboard Item`.`visibility` = 'shared' "
		"OR EXISTS (SELECT 1 FROM `tabDocShare` "
		"WHERE `tabDocShare`.`share_doctype` = 'Frappin Clipboard Item' "
		"AND `tabDocShare`.`share_name` = `tabFrappin Clipboard Item`.`name` "
		f"AND `tabDocShare`.`user` = {escaped_user} AND `tabDocShare`.`read` = 1))"
	)


def has_permission(doc, ptype=None, user=None):
	user = user or frappe.session.user
	if user == "Administrator" or doc.owner_user == user:
		return True
	shared_read = doc.visibility == "shared" or bool(
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
	if ptype == "read":
		return shared_read
	if ptype == "write":
		return shared_read and bool(doc.shared_can_edit)
	if ptype == "delete":
		return shared_read and bool(doc.shared_can_delete)
	return False

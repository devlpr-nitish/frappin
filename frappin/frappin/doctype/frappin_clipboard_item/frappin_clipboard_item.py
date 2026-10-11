import hashlib

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

MAX_CONTENT_LENGTH = 100_000
CONTENT_TYPES = {"text", "url", "template", "doc_reference"}


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

		self.content_hash = make_content_hash(self.content, self.content_type)
		self.last_used_at = self.last_used_at or now_datetime()
		self.visibility = self.visibility or "private"


def make_content_hash(content, content_type="text"):
	payload = f"{content_type}\0{content}".encode()
	return hashlib.sha256(payload).hexdigest()


def get_permission_query_conditions(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return ""
	escaped_user = frappe.db.escape(user)
	return (
		f"(`tabFrappin Clipboard Item`.`owner_user` = {escaped_user} "
		"OR `tabFrappin Clipboard Item`.`visibility` = 'shared')"
	)


def has_permission(doc, ptype=None, user=None):
	user = user or frappe.session.user
	if user == "Administrator" or doc.owner_user == user:
		return True
	return ptype == "read" and doc.visibility == "shared"

import frappe
from frappe.model.document import Document


class FrappinCollection(Document):
	def before_insert(self):
		self.owner_user = frappe.session.user

	def validate(self):
		if not self.is_new():
			owner_user = frappe.db.get_value(self.doctype, self.name, "owner_user")
			if owner_user and self.owner_user != owner_user:
				frappe.throw("Collection ownership cannot be changed.", frappe.PermissionError)


def get_permission_query_conditions(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return ""
	return f"`tabFrappin Collection`.`owner_user` = {frappe.db.escape(user)}"


def has_permission(doc, ptype=None, user=None):
	user = user or frappe.session.user
	return user == "Administrator" or doc.owner_user == user

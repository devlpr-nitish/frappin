import frappe
from frappe.model.document import Document
from frappe.utils import cint


class FrappinSettings(Document):
	def validate(self):
		self.retention_days = 2 if self.retention_days in (None, "") else cint(self.retention_days)
		if self.retention_days < 1:
			frappe.throw("Retention days must be at least 1.")

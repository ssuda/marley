# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

from healthcare.healthcare.doctype.patient_encounter.patient_encounter import (
	get_prescription_dates,
)
from healthcare.healthcare.utils import (
	calculate_distance,
	set_address_display,
	set_service_unit_phone,
)


class MedicationOrder(Document):
	def validate(self):
		self.validate_duplicate()
		self.set_total_orders()
		set_address_display(self)
		set_service_unit_phone(self)
		calculate_distance(self)

	def on_submit(self):
		self.validate_inpatient()
		self.set_status()

	def on_cancel(self):
		self.set_status()

	def validate_duplicate(self):
		existing_mo = frappe.db.exists(
			"Medication Order",
			{
				"patient_encounter": self.patient_encounter,
				"docstatus": ("!=", 2),
				"name": ("!=", self.name),
			},
		)
		if existing_mo:
			frappe.throw(
				_("An Medication Order {0} against Patient Encounter {1} already exists.").format(
					existing_mo, self.patient_encounter
				),
				frappe.DuplicateEntryError,
			)

	def set_total_orders(self):
		self.db_set("total_orders", len(self.medication_orders))


	@frappe.whitelist()
	def add_order_entries(self, order):
		if order.get("drug_code"):
			entry = self.append("medication_orders")
			entry.medication = order.get("medication")
			entry.drug = order.get("drug_code")
			entry.drug_name = frappe.db.get_value("Item", order.get("drug_code"), "item_name")
			entry.dosage = order.get("dosage")
			entry.dosage_form = order.get("dosage_form")
			entry.duration = order.get("duration")
			entry.duration_uom = order.get("duration_uom")
			entry.quantity = order.get("quantity")
			entry.route = order.get("route")
			entry.dosage_by_interval = order.get("dosage_by_interval")
			entry.interval = order.get("interval")
			entry.interval_uom = order.get("interval_uom")
		return

	@frappe.whitelist()
	def get_from_encounter(self, encounter):
		patient_encounter = frappe.get_doc("Patient Encounter", encounter)
		self.patient = patient_encounter.patient
		self.patient_name = patient_encounter.patient_name
		self.gender = patient_encounter.patient_sex
		self.age = patient_encounter.patient_age
		self.practitioner = patient_encounter.practitioner
		self.start_date = patient_encounter.encounter_date
		self.company = patient_encounter.company
		self.patient_encounter = list(patient_encounter.name)[0] if isinstance(patient_encounter.name, list) else patient_encounter.name

		if not patient_encounter.drug_prescription:
			return
		
		self.set("medication_orders", [])
		for drug in patient_encounter.drug_prescription:
			self.add_order_entries(drug)

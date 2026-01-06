# Copyright (c) 2026, earthians Health Informatics Pvt. Ltd. and Contributors
# See license.txt
from frappe.utils import nowdate
import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestMedicationOrder(IntegrationTestCase):
	def setUp(self):
		# Create Company
		self.company = frappe.db.get_value("Company", {"company_name": "_Test Company"})
		self.company = frappe.db.get_value("Company", {"company_name": "_Test Company"})
		if not self.company:
			self.company = frappe.get_doc({
				"doctype": "Company",
				"company_name": "_Test Company",
				"abbr": "_TC",
				"currency": "INR",
				"country": "India"
			}).insert(ignore_permissions=True).name
		
		frappe.db.set_single_value("Global Defaults", "default_company", self.company)


		# Create Patient
		try:
			self.patient = frappe.get_doc({
				"doctype": "Patient",
				"first_name": "Test Patient",
				"sex": "Male",
				"mobile": "1234567890"
			}).insert(ignore_permissions=True)
		except frappe.DuplicateEntryError:
			self.patient = frappe.get_doc("Patient", {"first_name": "Test Patient"})

		# Create Practitioner
		try:
			self.practitioner = frappe.get_doc({
				"doctype": "Healthcare Practitioner",
				"first_name": "Test Practitioner",
				"sex": "Male"
			}).insert(ignore_permissions=True)
		except frappe.DuplicateEntryError:
			self.practitioner = frappe.get_doc("Healthcare Practitioner", {"first_name": "Test Practitioner"})

		# Create Item (Drug)
		if not frappe.db.exists("Item", "Drug A"):
			self.item = frappe.get_doc({
				"doctype": "Item",
				"item_code": "Drug A",
				"item_group": "Products",
				"is_stock_item": 0
			}).insert(ignore_permissions=True)
		else:
			self.item = frappe.get_doc("Item", "Drug A")

		# Create Medication
		if not frappe.db.exists("Medication", "Drug A"):
			self.medication = frappe.get_doc({
				"doctype": "Medication",
				"item": "Drug A",
				"medication_name": "Drug A"
			}).insert(ignore_permissions=True)
		else:
			self.medication = frappe.get_doc("Medication", "Drug A")

		# Create Prescription Dosage
		if not frappe.db.exists("Prescription Dosage", "1-0-1"):
			self.dosage = frappe.get_doc({
				"doctype": "Prescription Dosage",
				"name": "1-0-1",
				"dosage": "1-0-1",
				"dosage_strength": [
					{"strength": 1, "strength_time": "08:00:00"},
					{"strength": 1, "strength_time": "20:00:00"}
				]
			}).insert(ignore_permissions=True)
		else:
			self.dosage = frappe.get_doc("Prescription Dosage", "1-0-1")

		# Create Prescription Duration
		if not frappe.db.exists("Prescription Duration", "7 Days"):
			self.duration = frappe.get_doc({
				"doctype": "Prescription Duration",
				"name": "7 Days"
			}).insert(ignore_permissions=True)

		# Create Simple Appointment Type
		if not frappe.db.exists("Appointment Type", "Simple Type"):
			self.appointment_type = frappe.get_doc({
				"doctype": "Appointment Type",
				"appointment_type": "Simple Type",
				"default_duration": 15
			}).insert(ignore_permissions=True)
		else:
			self.appointment_type = frappe.get_doc("Appointment Type", "Simple Type")

	def test_get_from_encounter(self):
		from unittest.mock import MagicMock, patch

		# Mock Patient Encounter
		mock_encounter = MagicMock()
		mock_encounter.name = "ENC-123"
		mock_encounter.patient = self.patient.name
		mock_encounter.patient_name = self.patient.first_name
		mock_encounter.patient_sex = self.patient.sex
		mock_encounter.patient_age = "25"
		mock_encounter.practitioner = self.practitioner.name
		mock_encounter.encounter_date = "2023-10-10"
		mock_encounter.company = self.company
		
		# Mock Drug Prescription Row
		mock_drug = MagicMock()
		mock_drug.drug_code = "Drug A"
		mock_drug.medication = self.medication.name
		mock_drug.dosage = self.dosage.name
		mock_drug.dosage_form = "Tablet" # Assuming dosage form
		mock_drug.dosage_form = "Tablet" # Assuming dosage form
		mock_drug.dosage_form = "Tablet" # Assuming dosage form
		mock_drug.duration = 7
		mock_drug.duration_uom = "Day"
		mock_drug.quantity = 14
		mock_drug.route = "Oral"
		mock_drug.dosage_by_interval = 0
		mock_drug.interval = 0
		mock_drug.interval_uom = None

		mock_encounter.drug_prescription = [mock_drug]

		# mocking frappe.get_doc to return our mock encounter
		with patch('frappe.get_doc', side_effect=lambda doctype, name=None: mock_encounter if doctype == "Patient Encounter" else frappe.get_doc(doctype, name)):
			# Create Medication Order
			mo = frappe.new_doc("Medication Order")
			
			# We need to ensure mo.get_from_encounter calls frappe.get_doc
			# However, frappe.get_doc is imported in medication_order.py? 
			# In frappe, usually it's `import frappe` and `frappe.get_doc`. 
			# Patching `frappe.get_doc` globally should work if it's accessed via `frappe.get_doc`.
			
			# Wait, patch inside 'frappe.get_doc' might be tricky if it calls itself or loops.
			# Better to mock specifically for the call we expect.
			# But side_effect lambda handles pass-through.
			
			mo.get_from_encounter("ENC-123")

			self.assertEqual(mo.patient, self.patient.name)
			self.assertEqual(mo.practitioner, self.practitioner.name)
			self.assertEqual(str(mo.start_date), "2023-10-10")

			# Check Medication Orders populated
			self.assertEqual(len(mo.medication_orders), 1)
			
			entry1 = mo.medication_orders[0]
			self.assertEqual(entry1.medication, self.medication.name)
			self.assertEqual(entry1.dosage, self.dosage.name)
			self.assertEqual(entry1.duration, 7)
			self.assertEqual(entry1.duration_uom, "Day")
			self.assertEqual(entry1.quantity, 14)
			self.assertEqual(entry1.route, "Oral")


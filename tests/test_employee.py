from unittest import TestCase
from services.employee_service import EmployeeService
import unittest

class test_employee(TestCase):
    def setUp(self):
        self.employee_service = EmployeeService()

    def test_add_employee(self):
        self.employee_service.add_employee({"name": "John Doe", "department": "IT", "skills": {"Technical": ["Python", "SQL"], "Business": ["Sales", "Marketing"], "Languages": ["English", "Spanish"]}})
        self.assertEqual(len(self.employee_service.employees), 1)
        self.assertEqual(self.employee_service.employees[0]["name"], "John Doe")
        self.assertEqual(self.employee_service.employees[0]["department"], "IT")
if __name__ == '__main__':
    unittest.main()

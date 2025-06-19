from unittest import TestCase
from services.employee_service import EmployeeService
import unittest

class test_employee(TestCase):
    def test_add_employee(self):
        """Test successful employee addition"""
        self.service.add_employee(self.sample_employee)
        self.assertEqual(len(self.service.employees), 1)
        self.assertEqual(self.service.employees[0]["name"], "John Doe")

    def test_add_employee_duplicate(self):
        """Test duplicate prevention (if implemented)"""
        self.service.add_employee(self.sample_employee)
        with self.assertRaises(ValueError):
            self.service.add_employee(self.sample_employee)

    def test_get_employee(self):
        """Test employee retrieval"""
        self.service.add_employee(self.sample_employee)
        employee = self.service.get(0) 
        self.assertEqual(employee["department"], "IT")
if __name__ == '__main__':
    unittest.main()

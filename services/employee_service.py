import json
import os

class EmployeeService:
    def __init__(self):
        self.data_file = "employees_data.txt"  # File to store data
        self.employees = []
        self.departments = ["HR", "IT", "Finance", "Research"]  # Default departments
        self._load_data()  # Load data when the service starts

        if not self.departments:
            self.departments = ["HR", "IT", "Finance", "Research"]
            self._save_data()

    def _load_data(self):
        """Load employees from the file if it exists."""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as file:
                try:
                    data = json.load(file)
                    self.employees = data.get("employees", [])
                    self.departments = data.get("departments", self.departments)
                except json.JSONDecodeError:
                    # File is corrupt; start fresh
                    self.employees = []
                    self.departments = ["HR", "IT", "Finance", "Research"]

    def _save_data(self):
        """Save employees and departments to the file."""
        with open(self.data_file, 'w') as file:
            json.dump({
                "employees": self.employees,
                "departments": self.departments
            }, file, indent=4)

    def get(self, employee_id):
        for employee in self.employees:
            if employee["id"] == employee_id:
                return employee
        return None 
       

    def add_employee(self, form_data):
      new_employee = {
        "id": len(self.employees) + 1,
        "name": form_data["name"],
        "department": form_data["department"],
        "skills": {
            "Technical": [],
            "Business": [],
            "Languages": []
        }
    }
      self.employees.append(new_employee)
      self._save_data()

    def search(self, filters):
        results = self.employees
        if 'department' in filters and filters['department']:
            results = [e for e in results if e['department'] == filters['department']]
        return results

def _load_data(self):
    """Load data from file with error handling"""
    try:
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as file:
                data = json.load(file)
                self.employees = data.get("employees", [])
                self.departments = data.get("departments", [])
            print(f"DEBUG: Loaded {len(self.employees)} employees from file")
        else:
            print("DEBUG: No data file found, using defaults")
    except json.JSONDecodeError:
        print("ERROR: Corrupt data file, resetting")
        self.employees = []
        self.departments = [] 

    def add_department(self, name):
        """Add a new department if it doesn't exist."""
        if name not in self.departments:
            self.departments.append(name)
            self._save_data()
            return True
        return False  # Department already exists
    def get_departments(self):
        """Return all departments."""
        return self.departments
        self.employees.append(new_employee)
        self._save_data()  
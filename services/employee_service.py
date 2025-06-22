from database.json_importer import JsonImporter
import json
import os

class EmployeeService:
    def __init__(self):
        self.data_file = "data.json"
        self.employees = []
        self.departments = ["HR", "IT", "Finance", "Research"]
        self._load_data()

        if not self.departments:
            self.departments = ["HR", "IT", "Finance", "Research"]
            self._save_data()

    def _load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as file:
                    data = json.load(file)
                    self.employees = data.get("employees", [])
                    self.departments = data.get("departments", self.departments)
                print(f"DEBUG: Loaded {len(self.employees)} employees from {self.data_file}")
            else:
                print("DEBUG: No data file found, using defaults")
        except json.JSONDecodeError:
            print("ERROR: Corrupt data file, resetting")
            self.employees = []
            self.departments = self.departments

    def _save_data(self):
        with open(self.data_file, 'w') as file:
            json.dump({
                "employees": self.employees,
                "departments": self.departments
            }, file, indent=4)
        print(f"DEBUG: Saved {len(self.employees)} employees to {self.data_file}")

    def get(self, employee_id):
        for employee in self.employees:
            if employee["id"] == employee_id:
                return employee
        return None

    def add_employee(self, form_data):
        technical_skills = [s.strip() for s in form_data.getlist("technical_skills[]") if s.strip()]
        business_skills = [s.strip() for s in form_data.getlist("business_skills[]") if s.strip()]
        languages = []
        language_names = form_data.getlist("language[]")
        language_levels = form_data.getlist("language_level[]")

        for name, level in zip(language_names, language_levels):
            name = name.strip()
            level = level.strip()
            if name:
                languages.append(f"{name} ({level})")

        new_employee = {
            "id": len(self.employees) + 1,
            "name": form_data["name"],
            "department": form_data["department"],
            "skills": {
                "Technical": technical_skills,
                "Business": business_skills,
                "Languages": languages
            }
        }

        self.employees.append(new_employee)
        self._save_data()

        # ✅ Re-import into the database after saving to data.json
        try:
            importer = JsonImporter()
            importer.import_data()
            print("DEBUG: Database successfully updated after employee added.")
        except Exception as e:
            print(f"ERROR: Failed to update database from JSON: {e}")

        return True

    def search(self, filters):
        results = self.employees
        if 'department' in filters and filters['department']:
            results = [e for e in results if e['department'] == filters['department']]
        return results

        from database.json_importer import JsonImporter

    def add_department(self, name):
        if name not in self.departments:
           self.departments.append(name)
           self._save_data()

        # Sync to database
        try:
            importer = JsonImporter()
            importer.import_data()
            print("DEBUG: Database updated after department added.")
        except Exception as e:
            print(f"ERROR: Failed to update database after department add: {e}")

        return True

    def get_departments(self):
        return self.departments
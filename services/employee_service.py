from models import Employee, Employee_collection

class EmployeeService:
    @staticmethod
    def get_all_employees():
        return Employee_collection.get_Employee_collection().get_employees()

    @staticmethod
    def add_employee(form_data):
        emp_collection = Employee_collection.get_Employee_collection()
        emp_collection.add_employee(Employee(
            id=form_data['id'],
            name=form_data['name'],
            department=form_data['department'],
            skills=form_data['skills']
        ))
        return True

    @staticmethod
    def search_employees(filters):
        employees = Employee_collection.get_Employee_collection().get_employees()
        
        if filters.get('id'):
            employees = [e for e in employees if e.id == int(filters['id'])]
        if filters.get('name'):
            name_lower = filters['name'].lower()
            employees = [e for e in employees if name_lower in e.name.lower()]
        if filters.get('department'):
            employees = [e for e in employees if e.department == filters['department']]
        if filters.get('technical_skill'):
            tech_lower = filters['technical_skill'].lower()
            employees = [e for e in employees if any(tech_lower in s.lower() for s in e.skills['Technical'])]
        # Add similar filters for business_skill and languages_skill
        
        return employees

    @staticmethod
    def get_all_departments():
        employees = Employee_collection.get_Employee_collection().get_employees()
        return sorted({e.department for e in employees})
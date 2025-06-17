class Employee:
    def __init__(self, id, name, department, skills=None):
        self.id = id
        self.name = name
        self.department = department
        self.skills = skills if skills is not None else {
            "Technical": [],
            "Business": [],
            "Languages": {}
        }

    def get_id(self):
        return self.id
    
    def get_name(self):
        return self.name
    
    def get_department(self):
        return self.department
    
    def get_skills(self):
        return self.skills


class employee_collection():
    _instance = None
    
    def __init__(self):
        if not employee_collection._instance:
            self.employees = []
            employee_collection._instance = self
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = employee_collection()
        return cls._instance
    
    def add(self, employee):
        self.employees.append(employee)
    
    def get(self, employee_id):
        for employee in self.employees:
            if employee.get_id() == employee_id:
                return employee
        return None
    
    def get_all(self):
        return self.employees.copy()
    
    def search(self, **filters):
        results = self.employees
        
        if 'id' in filters:
            results = [e for e in results if e.get_id() == int(filters['id'])]
        if 'name' in filters:
            name_lower = filters['name'].lower()
            results = [e for e in results if name_lower in e.get_name().lower()]
        if 'department' in filters:
            results = [e for e in results if e.get_department() == filters['department']]
            
        return results
    
    def get_departments(self):
        return sorted({e.get_department() for e in self.employees})


# Singleton instance
employee_collection = employee_collection.get_instance()
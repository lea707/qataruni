# models/employee.py
class Employee:
    def __init__(self, id, name, department, skills=None):
        """
        Initialize an Employee with basic information and skills
        Args:
            id: Unique employee identifier
            name: Full name of employee
            department: Department name
            skills: Dictionary of skills (defaults to empty skill categories)
        """
        self.id = id
        self.name = name
        self.department = department
        self.skills = skills if skills is not None else {
            "Technical": [],
            "Business": [],
            "Languages": {}
        }

    def to_dict(self):
        """Convert Employee object to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "skills": self.skills
        }

    def get_technical_skills(self):
        """Get list of technical skills"""
        return self.skills.get("Technical", [])

    def get_business_skills(self):
        """Get list of business skills"""
        return self.skills.get("Business", [])

    def get_languages(self):
        """Get dictionary of languages and proficiency levels"""
        return self.skills.get("Languages", {})

    def add_technical_skill(self, skill):
        """Add a technical skill if not already present"""
        if skill and skill not in self.skills["Technical"]:
            self.skills["Technical"].append(skill)

    def add_business_skill(self, skill):
        """Add a business skill if not already present"""
        if skill and skill not in self.skills["Business"]:
            self.skills["Business"].append(skill)

    def add_language(self, language, proficiency):
        """Add or update a language with proficiency level"""
        if language and proficiency:
            self.skills["Languages"][language] = proficiency

class EmployeeCollection:
    def __init__(self, employees=None):
        self.employees = employees or []
    
    def add(self, employee):
        self.employees.append(employee)
    
    def get(self, employee_id):
        return next((e for e in self.employees if e.id == employee_id), None)
    
    def get_all(self):
        return self.employees.copy()
    
    def search(self, **filters):
        results = self.employees
        
        if 'id' in filters and filters['id']:
            results = [e for e in results if e.id == int(filters['id'])]
        if 'name' in filters and filters['name']:
            name_lower = filters['name'].lower()
            results = [e for e in results if name_lower in e.name.lower()]
        if 'department' in filters and filters['department']:
            results = [e for e in results if e.department == filters['department']]
        if 'technical_skill' in filters and filters['technical_skill']:
            tech_lower = filters['technical_skill'].lower()
            results = [e for e in results if any(tech_lower in s.lower() for s in e.skills['Technical'])]
        if 'business_skill' in filters and filters['business_skill']:
            bus_lower = filters['business_skill'].lower()
            results = [e for e in results if any(bus_lower in s.lower() for s in e.skills['Business'])]
        if 'languages_skill' in filters and filters['languages_skill']:
            lang_lower = filters['languages_skill'].lower()
            results = [e for e in results if any(lang_lower in l.lower() for l in e.skills['Languages'].keys())]
            
        return results
    
    def get_departments(self):
        return sorted({e.department for e in self.employees}) 
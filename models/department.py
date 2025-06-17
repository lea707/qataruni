class Department:
    departments = []  
    
    def __init__(self, name, description=None):
        if any(dept.name == name for dept in self.departments):
            raise ValueError(f"Department '{name}' already exists")
        
        self.name = name
        self.description = description
        self.departments.append(self)

    def __repr__(self):
        return f'<Department {self.name}>'

    @classmethod
    def get_all(cls):
        """Get all departments ordered by name"""
        return sorted(cls.departments, key=lambda dept: dept.name)

    @classmethod
    def add(cls, name, description=None):
        """Add a new department"""
        return cls(name, description)

    @classmethod
    def get_by_name(cls, name):
        """Get department by name"""
        return next((dept for dept in cls.departments if dept.name == name), None)

    @classmethod
    def delete(cls, name):
        """Delete a department by name"""
        cls.departments = [dept for dept in cls.departments if dept.name != name]
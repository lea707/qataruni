import pandas as pd
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
import pandas as pd
class ExcelEmployeeReader:
    @staticmethod
    def read_employee_excel(file_path):
        """Reads employee data from Excel and returns structured data"""
        try:
         

            df = pd.read_excel(file_path, engine="openpyxl")

            # Rename columns to match your model
            df.columns = ['business_id', 'english_name', 'arab_name', 'email', 
                        'phone', 'Departments', 'is_active_text', 'hire_date']
            print(f"columns= {df.columns}")

            # Normalize values
            df['is_active'] = df['is_active_text'].str.lower().map({'yes': True, 'no': False})
            if pd.api.types.is_datetime64_any_dtype(df['hire_date']):
                df['hire_date'] = df['hire_date'].astype(str)

            rows = df.to_dict(orient="records")

            for row in rows:
                dept_obj = DepartmentService.ensure_department_by_name(row.get('Departments'))
                row['department_id'] = dept_obj.department_id if dept_obj else None

                row['skills'] = {}

            return rows

        except Exception as e:
            print(f"Error reading Excel file: {e}")
            raise
    @staticmethod
    def import_employees(file_path, update_existing=False):
        """Imports employees from Excel file"""
        employee_data = ExcelEmployeeReader.read_employee_excel(file_path)
        employee_service = EmployeeService()
        
        results = {
            'success': 0,
            'errors': 0,
            'details': []
        }

        for row in employee_data:
            try:
                if update_existing and row.get('business_id'):
                    # Update existing employee
                    employee_service.update_employee_by_business_id(
                        row['business_id'], 
                        row
                    )
                else:
                    # Create new employee
                    employee_service.create_employee(row)
                
                results['success'] += 1
                results['details'].append({
                    'business_id': row.get('business_id'),
                    'name': row.get('english_name'),
                    'status': 'success'
                })
            except Exception as e:
                results['errors'] += 1
                results['details'].append({
                    'business_id': row.get('business_id'),
                    'name': row.get('english_name'),
                    'status': 'error',
                    'message': str(e)
                })

        return results

def main():
    if __name__ == '__main__':
        main()
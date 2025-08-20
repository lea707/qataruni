import pandas as pd
import sys
from models.employee import Employee
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from database.connection import SessionLocal, db


class ExcelEmployeeReader:
    @staticmethod
    def read_employee_excel(file_path):
        """Reads employee data from Excel and returns structured data"""
        try:
            df = pd.read_excel(file_path, engine="openpyxl")

            # Rename columns to match your model
            df.columns = [
                'business_id', 'english_name', 'arab_name', 'email',
                'phone', 'Departments', 'is_active_text', 'hire_date'
            ]
            print(f"columns= {df.columns}")

            # Normalize values
            df['is_active'] = df['is_active_text'].str.lower().map({'yes': True, 'no': False})
            if pd.api.types.is_datetime64_any_dtype(df['hire_date']):
                df['hire_date'] = df['hire_date'].astype(str)

            rows = df.to_dict(orient="records")
            print(f"employees: {rows}")

            for row in rows:
                dept_obj = DepartmentService.ensure_department_by_name(row.get('Departments'))
                row['department_id'] = dept_obj.department_id if dept_obj else None
                print(f"Processed row: {row}")
                row['skills'] = {}  # Excel does not carry skills for now

            return rows

        except Exception as e:
            print(f"Error reading Excel file: {e}")
            raise

    from database.connection import SessionLocal

    @classmethod
    def import_employees(cls, file_path, update_existing=False):
        employees = cls.read_employee_excel(file_path)   # ✅ fixed: call the right method
        results = {"inserted": 0, "updated": 0, "skipped": 0, "errors": []}

        session = SessionLocal()   # 🔑 get a real session
        try:
            for row in employees:
                try:
                    existing = session.query(Employee).filter_by(email=row["email"]).first()

                    if existing:
                        if update_existing:
                            print(f"🟡 Updating {row['email']} ...")
                            existing.phone = row.get("phone")
                            existing.department_id = row.get("department_id")
                            existing.english_name = row.get("english_name")
                            existing.arab_name = row.get("arab_name")
                            existing.hire_date = row.get("hire_date")
                            existing.is_active = row.get("is_active")
                            results["updated"] += 1
                        else:
                            print(f"⏭️ Skipping existing {row['email']}")
                            results["skipped"] += 1
                    else:
                        print(f"🟢 Creating new {row['email']} ...")
                        new_emp = Employee(
                            busness_id=row["business_id"],  # your DB column is spelled like this
                            english_name=row["english_name"],
                            arab_name=row["arab_name"],
                            email=row["email"],
                            phone=row["phone"],
                            hire_date=row["hire_date"],
                            is_active=row["is_active"],
                            department_id=row["department_id"],
                        )
                        session.add(new_emp)
                        results["inserted"] += 1

                except Exception as e:
                    session.rollback()
                    print(f"❌ Error for {row['email']}: {e}")
                    results["errors"].append({"email": row["email"], "error": str(e)})

            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

        return results


    def main():
        if len(sys.argv) < 2:
            print("Usage: python excel_employee_reader.py <file_path> [--update]")
            return

        file_path = sys.argv[1]
        update_existing = "--update" in sys.argv
        print(f"➡️ Importing employees from file_path={file_path}")

        results = ExcelEmployeeReader.import_employees(file_path, update_existing=update_existing)
        print("=== Import Results ===")
        print(results)


    if __name__ == '__main__':
        main()

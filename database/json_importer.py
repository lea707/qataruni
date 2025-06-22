import json
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "data.json"
load_dotenv(PROJECT_ROOT / '.env')

def parse_language_entry(entry):
    """
    Splits a language entry like "english (Basic)" into:
      - language name: "english"
      - proficiency: "Basic"
    If not in expected format, returns the whole string as name and a default level.
    """
    if '(' in entry and ')' in entry:
        name_part = entry.split('(')[0].strip()
        level_part = entry.split('(')[1].split(')')[0].strip()
        return name_part, level_part
    return entry, "Unknown"

class JsonImporter:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )

    def import_data(self):
        try:
            print(f"🔍 Looking for data file at: {DATA_FILE}")
            if not DATA_FILE.exists():
                raise FileNotFoundError(f"Data file not found at: {DATA_FILE}")

            with open(DATA_FILE) as f:
                data = json.load(f)

            with self.conn.cursor() as cur:
                # Clear existing data from tables.
                self._clear_tables(cur)

                # Import each department.
                dept_map = {}
                for dept in data['departments']:
                    dept_name = dept if isinstance(dept, str) else dept.get('name')
                    cur.execute(
                        "INSERT INTO departments (dep_name) VALUES (%s) ON CONFLICT (dep_name) DO NOTHING RETURNING d_id",
                        (dept_name,)
                    )
                    result = cur.fetchone()
                    if result:
                        dept_id = result[0]
                    else:
                        cur.execute("SELECT d_id FROM departments WHERE dep_name = %s", (dept_name,))
                        dept_id = cur.fetchone()[0]
                    dept_map[dept_name] = dept_id

                # Import employees and their skills
                for emp in data['employees']:
                    self._import_employee(cur, emp, dept_map)

            self.conn.commit()
            print(f"✅ Successfully imported from {DATA_FILE}")

        except Exception as e:
            print(f"❌ Error: {e}")
            self.conn.rollback()
            raise
        finally:
            self.conn.close()

    def _clear_tables(self, cur):
        # The order here uses CASCADE, which will clear dependent data.
        tables = [
            'speaks',
            'knows_tech',
            'knows_bus',
            'employees',
            'languages',
            'technical_skill',
            'business_skills',
            'departments'
        ]
        for table in tables:
            try:
                cur.execute(f"TRUNCATE TABLE {table} CASCADE")
            except Exception as e:
                print(f"⚠️ Could not truncate {table}: {e}")
                raise

    def _import_employee(self, cur, emp, dept_map):
        # Insert employee; note that the JSON “id” is not used.
        cur.execute(
            "INSERT INTO employees (name, departments_d_id) VALUES (%s, %s) RETURNING id",
            (emp['name'], dept_map.get(emp['department']))
        )
        emp_id = cur.fetchone()[0]
        self._import_skills(cur, emp.get('skills', {}), emp_id)

    def _import_skills(self, cur, skills, emp_id):
        # Technical Skills
        for skill in skills.get('Technical', []):
            try:
                cur.execute("""
                    WITH skill_data AS (
                        INSERT INTO technical_skill (t_name)
                        VALUES (%s)
                        ON CONFLICT (t_name) DO UPDATE SET t_name = EXCLUDED.t_name
                        RETURNING tech_ID
                    )
                    INSERT INTO knows_tech (employee_id, technical_skill_id)
                    SELECT %s, tech_ID FROM skill_data
                    ON CONFLICT DO NOTHING
                """, (skill, emp_id))
            except Exception as e:
                self.conn.rollback()
                print(f"❌ Technical skill failed: {skill} (Employee ID: {emp_id})")
                raise

        # Business Skills
        for skill in skills.get('Business', []):
            try:
                cur.execute("""
                    WITH skill_data AS (
                        INSERT INTO business_skills (b_name)
                        VALUES (%s)
                        ON CONFLICT (b_name) DO UPDATE SET b_name = EXCLUDED.b_name
                        RETURNING bus_ID
                    )
                    INSERT INTO knows_bus (employee_id, business_skill_id)
                    SELECT %s, bus_ID FROM skill_data
                    ON CONFLICT DO NOTHING
                """, (skill, emp_id))
            except Exception as e:
                self.conn.rollback()
                print(f"❌ Business skill failed: {skill} (Employee ID: {emp_id})")
                raise

        # Languages
        for lang_entry in skills.get('Languages', []):
            lang_name, lang_level = parse_language_entry(lang_entry)
            try:
                cur.execute("""
                    WITH lang_data AS (
                        INSERT INTO languages (l_name, l_level)
                        VALUES (%s, %s)
                        ON CONFLICT (l_name) DO UPDATE SET l_level = EXCLUDED.l_level
                        RETURNING id
                    )
                    INSERT INTO speaks (employees_id, languages_id, proficiency)
                    SELECT %s, id, %s FROM lang_data
                    ON CONFLICT DO NOTHING
                """, (lang_name, lang_level, emp_id, lang_level))
            except Exception as e:
                self.conn.rollback()
                print(f"❌ Language failed: {lang_entry} (Employee ID: {emp_id})")
                raise

if __name__ == "__main__":
    importer = JsonImporter()
    importer.import_data()

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def verify_lea_project():
    try:
        # Connect to EXISTING database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),  # Uses lea_project
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        
        print(f"✅ Connected to '{os.getenv('DB_NAME')}' (OID: 16388)")
        
        # Verify physical location (read-only)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT oid, datname 
                FROM pg_database 
                WHERE datname = %s
            """, (os.getenv('DB_NAME'),))
            db_info = cur.fetchone()
            print(f"Physical path: C:\\Program Files\\PostgreSQL\\17\\data\\base\\{db_info[0]}")
            
        conn.close()
    except Exception as e:
        print("❌ Connection failed:", e)
        print("Troubleshooting:")
        print("- Run `services.msc` and check 'postgresql-x64-17' is running")
        print("- Verify DB_NAME in .env matches pgAdmin exactly")

if __name__ == "__main__":
    verify_lea_project()
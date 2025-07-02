from database import db

def test_connection():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print("✅ Database connected successfully!")
            print("PostgreSQL version:", version[0])
    except Exception as e:
        print("❌ Failed to connect to the database.")
        print("Error:", e)

if __name__ == "__main__":
    test_connection()
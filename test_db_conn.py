import os
import psycopg2
import sqlite3

DATABASE_URL = "postgresql://postgres:B%40c%40lori%402015@db.wfdoqlomlpsowxzwfxfu.supabase.co:5432/postgres?sslmode=require"

def test_connections():
    print("--- Testing Postgres ---")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Postgres Connection Successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Postgres Failed: {e}")

    print("\n--- Testing SQLite ---")
    try:
        db_path = os.path.join(os.getcwd(), 'api', 'douera.db')
        print(f"Target path: {db_path}")
        conn = sqlite3.connect(db_path)
        print("✅ SQLite Connection Successful!")
        conn.close()
    except Exception as e:
        print(f"❌ SQLite Failed: {e}")

if __name__ == "__main__":
    test_connections()

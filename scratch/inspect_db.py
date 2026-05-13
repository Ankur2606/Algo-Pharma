import sqlite3
import json

def inspect_db():
    try:
        conn = sqlite3.connect("algopharma.db")
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        for table in [t[0] for t in tables]:
            print(f"\n--- Table: {table} ---")
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            print(f"Columns: {[c[1] for c in columns]}")
            
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"Rows: {count}")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 1;")
                row = cursor.fetchone()
                print(f"Sample row: {row}")
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()

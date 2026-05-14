import sqlite3

def alter_db():
    conn = sqlite3.connect('algopharma.db')
    cursor = conn.cursor()
    
    queries = [
        "ALTER TABLE users ADD COLUMN email VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN last_login DATETIME",
        "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1",
        "ALTER TABLE projects ADD COLUMN user_id INTEGER REFERENCES users(id)"
    ]
    
    for q in queries:
        try:
            cursor.execute(q)
            print(f"Success: {q}")
        except Exception as e:
            print(f"Skipped/Error: {q} - {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    alter_db()

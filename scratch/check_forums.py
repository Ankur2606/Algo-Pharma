import sqlite3

def check_forums():
    conn = sqlite3.connect("algopharma.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM projects WHERE name LIKE '%forum%';")
    print(f"Forum Projects: {cursor.fetchall()}")
    
    cursor.execute("SELECT * FROM sources;")
    print(f"Sources: {cursor.fetchall()}")
    
    conn.close()

if __name__ == "__main__":
    check_forums()

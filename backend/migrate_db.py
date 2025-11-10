import sqlite3
import os

DB_PATH = "jobalytics.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("No database found, will be created on next run")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check if columns exist
    cur.execute("PRAGMA table_info(resumes)")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'experience_years' not in columns:
        print("Adding experience_years column...")
        cur.execute("ALTER TABLE resumes ADD COLUMN experience_years REAL DEFAULT 0")
    
    if 'education' not in columns:
        print("Adding education column...")
        cur.execute("ALTER TABLE resumes ADD COLUMN education TEXT DEFAULT 'none'")
    
    # Check jobs table
    cur.execute("PRAGMA table_info(jobs)")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'experience_required' not in columns:
        print("Adding experience_required column...")
        cur.execute("ALTER TABLE jobs ADD COLUMN experience_required REAL DEFAULT 0")
    
    if 'education_required' not in columns:
        print("Adding education_required column...")
        cur.execute("ALTER TABLE jobs ADD COLUMN education_required TEXT DEFAULT 'none'")
    
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()

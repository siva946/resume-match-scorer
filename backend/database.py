import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime

DB_PATH = "jobalytics.db"

def init_db():
    """Initialize database with proper schema"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Resumes table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Resume skills table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resume_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
        )
    """)
    
    # Resume experience table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resume_experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            years REAL NOT NULL,
            start_date TEXT,
            end_date TEXT,
            context TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
        )
    """)
    
    # Resume education table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resume_education (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            degree TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
        )
    """)
    
    # Jobs table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            description TEXT NOT NULL,
            url TEXT,
            embedding TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Job skills table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    
    # Job requirements table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            experience_years REAL,
            education_level INTEGER,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_resume_skills ON resume_skills(resume_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_job_skills ON job_skills(job_id)")
    
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

class ResumeDB:
    @staticmethod
    def insert_resume(filename: str, text: str, embedding: List[float], 
                     skills: List[str], experience_years: float, 
                     experience_entries: List[Dict], education_level: int, 
                     degrees: List[str]) -> int:
        """Insert resume with all related data"""
        conn = get_db()
        cur = conn.cursor()
        
        # Delete old resumes (single resume mode)
        cur.execute("DELETE FROM resumes")
        
        # Insert main resume
        cur.execute(
            "INSERT INTO resumes (filename, text, embedding) VALUES (?, ?, ?)",
            (filename, text, json.dumps(embedding))
        )
        resume_id = cur.lastrowid
        
        # Insert skills
        for skill in skills:
            cur.execute(
                "INSERT INTO resume_skills (resume_id, skill) VALUES (?, ?)",
                (resume_id, skill)
            )
        
        # Insert experience
        cur.execute(
            "INSERT INTO resume_experience (resume_id, years) VALUES (?, ?)",
            (resume_id, experience_years)
        )
        
        for exp in experience_entries:
            cur.execute(
                "INSERT INTO resume_experience (resume_id, years, start_date, end_date, context) VALUES (?, ?, ?, ?, ?)",
                (resume_id, 0, exp.get('start_date'), exp.get('end_date'), exp.get('context'))
            )
        
        # Insert education
        cur.execute(
            "INSERT INTO resume_education (resume_id, level) VALUES (?, ?)",
            (resume_id, education_level)
        )
        
        for degree in degrees:
            cur.execute(
                "INSERT INTO resume_education (resume_id, level, degree) VALUES (?, ?, ?)",
                (resume_id, 0, degree)
            )
        
        conn.commit()
        conn.close()
        return resume_id
    
    @staticmethod
    def get_resume(resume_id: int) -> Optional[Dict]:
        """Get resume with all related data"""
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT id, filename, text, embedding, created_at FROM resumes WHERE id = ?", (resume_id,))
        resume = cur.fetchone()
        
        if not resume:
            conn.close()
            return None
        
        # Get skills
        cur.execute("SELECT skill FROM resume_skills WHERE resume_id = ?", (resume_id,))
        skills = [row[0] for row in cur.fetchall()]
        
        # Get experience
        cur.execute("SELECT years FROM resume_experience WHERE resume_id = ? AND years > 0", (resume_id,))
        exp_row = cur.fetchone()
        experience_years = exp_row[0] if exp_row else 0
        
        # Get education
        cur.execute("SELECT level FROM resume_education WHERE resume_id = ? AND level > 0", (resume_id,))
        edu_row = cur.fetchone()
        education_level = edu_row[0] if edu_row else 0
        
        conn.close()
        
        return {
            'id': resume[0],
            'filename': resume[1],
            'text': resume[2],
            'embedding': json.loads(resume[3]),
            'skills': skills,
            'experience_years': experience_years,
            'education_level': education_level,
            'created_at': resume[4]
        }
    
    @staticmethod
    def list_resumes() -> List[Dict]:
        """List all resumes"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, filename, created_at FROM resumes ORDER BY created_at DESC")
        resumes = [{"id": r[0], "filename": r[1], "created_at": r[2]} for r in cur.fetchall()]
        conn.close()
        return resumes

class JobDB:
    @staticmethod
    def insert_job(title: str, company: str, description: str, url: Optional[str],
                   embedding: List[float], required_skills: List[str], 
                   experience_required: float, education_required: int) -> int:
        """Insert job with all related data"""
        conn = get_db()
        cur = conn.cursor()
        
        # Insert main job
        cur.execute(
            "INSERT INTO jobs (title, company, description, url, embedding) VALUES (?, ?, ?, ?, ?)",
            (title, company, description, url, json.dumps(embedding))
        )
        job_id = cur.lastrowid
        
        # Insert skills
        for skill in required_skills:
            cur.execute(
                "INSERT INTO job_skills (job_id, skill) VALUES (?, ?)",
                (job_id, skill)
            )
        
        # Insert requirements
        cur.execute(
            "INSERT INTO job_requirements (job_id, experience_years, education_level) VALUES (?, ?, ?)",
            (job_id, experience_required, education_required)
        )
        
        conn.commit()
        conn.close()
        return job_id
    
    @staticmethod
    def get_job(job_id: int) -> Optional[Dict]:
        """Get job with all related data"""
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT id, title, company, description, url, embedding, created_at FROM jobs WHERE id = ?", (job_id,))
        job = cur.fetchone()
        
        if not job:
            conn.close()
            return None
        
        # Get skills
        cur.execute("SELECT skill FROM job_skills WHERE job_id = ?", (job_id,))
        skills = [row[0] for row in cur.fetchall()]
        
        # Get requirements
        cur.execute("SELECT experience_years, education_level FROM job_requirements WHERE job_id = ?", (job_id,))
        req = cur.fetchone()
        experience_required = req[0] if req else 0
        education_required = req[1] if req else 0
        
        conn.close()
        
        return {
            'id': job[0],
            'title': job[1],
            'company': job[2],
            'description': job[3],
            'url': job[4],
            'embedding': json.loads(job[5]),
            'required_skills': skills,
            'experience_required': experience_required,
            'education_required': education_required,
            'created_at': job[6]
        }
    
    @staticmethod
    def get_all_jobs() -> List[Dict]:
        """Get all jobs with their data"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM jobs")
        job_ids = [row[0] for row in cur.fetchall()]
        conn.close()
        
        return [JobDB.get_job(job_id) for job_id in job_ids]
    
    @staticmethod
    def list_jobs() -> List[Dict]:
        """List all jobs (summary)"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, title, company, url, created_at FROM jobs ORDER BY created_at DESC")
        jobs = [{"id": j[0], "title": j[1], "company": j[2], "url": j[3], "created_at": j[4]} for j in cur.fetchall()]
        conn.close()
        return jobs

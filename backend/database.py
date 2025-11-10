import sqlite3
import json
from typing import List, Dict, Optional

DB_PATH = "resumsync.db"

def init_db():
    """Initialize database with detailed matching tables"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Resumes table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            experience_years REAL DEFAULT 0,
            education TEXT DEFAULT 'none',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Resume skills
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resume_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
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
            experience_required REAL DEFAULT 0,
            education_required TEXT DEFAULT 'none',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Job skills
    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    
    # Match results table - stores detailed breakdown
    cur.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            overall_score REAL NOT NULL,
            skills_score REAL NOT NULL,
            experience_score REAL NOT NULL,
            education_score REAL NOT NULL,
            semantic_score REAL NOT NULL,
            matched_skills_count INTEGER NOT NULL,
            total_required_skills INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    
    # Matched skills detail
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matched_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_result_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            is_matched BOOLEAN NOT NULL,
            FOREIGN KEY (match_result_id) REFERENCES match_results(id) ON DELETE CASCADE
        )
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_resume_skills ON resume_skills(resume_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_job_skills ON job_skills(job_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_match_results ON match_results(resume_id, job_id)")
    
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

class ResumeDB:
    @staticmethod
    def insert_resume(filename: str, text: str, embedding: List[float], 
                     skills: List[str], experience_years: float, education: str) -> int:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM resumes")
        
        cur.execute(
            "INSERT INTO resumes (filename, text, embedding, experience_years, education) VALUES (?, ?, ?, ?, ?)",
            (filename, text, json.dumps(embedding), experience_years, education)
        )
        resume_id = cur.lastrowid
        
        for skill in skills:
            cur.execute("INSERT INTO resume_skills (resume_id, skill) VALUES (?, ?)", (resume_id, skill))
        
        conn.commit()
        conn.close()
        return resume_id
    
    @staticmethod
    def get_resume(resume_id: int) -> Optional[Dict]:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT id, filename, text, embedding, experience_years, education FROM resumes WHERE id = ?", (resume_id,))
        resume = cur.fetchone()
        
        if not resume:
            conn.close()
            return None
        
        cur.execute("SELECT skill FROM resume_skills WHERE resume_id = ?", (resume_id,))
        skills = [row[0] for row in cur.fetchall()]
        
        conn.close()
        
        return {
            'id': resume[0],
            'filename': resume[1],
            'text': resume[2],
            'embedding': json.loads(resume[3]),
            'experience_years': resume[4],
            'education': resume[5],
            'skills': skills
        }
    
    @staticmethod
    def list_resumes() -> List[Dict]:
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
                   experience_required: float, education_required: str) -> int:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO jobs (title, company, description, url, embedding, experience_required, education_required) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, company, description, url, json.dumps(embedding), experience_required, education_required)
        )
        job_id = cur.lastrowid
        
        for skill in required_skills:
            cur.execute("INSERT INTO job_skills (job_id, skill) VALUES (?, ?)", (job_id, skill))
        
        conn.commit()
        conn.close()
        return job_id
    
    @staticmethod
    def get_job(job_id: int) -> Optional[Dict]:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT id, title, company, description, url, embedding, experience_required, education_required FROM jobs WHERE id = ?", (job_id,))
        job = cur.fetchone()
        
        if not job:
            conn.close()
            return None
        
        cur.execute("SELECT skill FROM job_skills WHERE job_id = ?", (job_id,))
        skills = [row[0] for row in cur.fetchall()]
        
        conn.close()
        
        return {
            'id': job[0],
            'title': job[1],
            'company': job[2],
            'description': job[3],
            'url': job[4],
            'embedding': json.loads(job[5]),
            'experience_required': job[6],
            'education_required': job[7],
            'required_skills': skills
        }
    
    @staticmethod
    def get_all_jobs() -> List[Dict]:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM jobs")
        job_ids = [row[0] for row in cur.fetchall()]
        conn.close()
        return [JobDB.get_job(job_id) for job_id in job_ids]
    
    @staticmethod
    def list_jobs() -> List[Dict]:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, title, company, url, created_at FROM jobs ORDER BY created_at DESC")
        jobs = [{"id": j[0], "title": j[1], "company": j[2], "url": j[3], "created_at": j[4]} for j in cur.fetchall()]
        conn.close()
        return jobs

class MatchDB:
    @staticmethod
    def save_match_result(resume_id: int, job_id: int, overall_score: float,
                         skills_score: float, experience_score: float, 
                         education_score: float, semantic_score: float,
                         matched_skills: List[str], missing_skills: List[str],
                         total_required: int) -> int:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO match_results 
            (resume_id, job_id, overall_score, skills_score, experience_score, 
             education_score, semantic_score, matched_skills_count, total_required_skills)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (resume_id, job_id, overall_score, skills_score, experience_score,
              education_score, semantic_score, len(matched_skills), total_required))
        
        match_id = cur.lastrowid
        
        for skill in matched_skills:
            cur.execute("INSERT INTO matched_skills (match_result_id, skill, is_matched) VALUES (?, ?, ?)",
                       (match_id, skill, True))
        
        for skill in missing_skills:
            cur.execute("INSERT INTO matched_skills (match_result_id, skill, is_matched) VALUES (?, ?, ?)",
                       (match_id, skill, False))
        
        conn.commit()
        conn.close()
        return match_id

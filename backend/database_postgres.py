import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import List, Dict, Optional

def get_db_url():
    return os.getenv('DATABASE_URL', '').replace('postgres://', 'postgresql://')

def get_db():
    return psycopg2.connect(get_db_url())

def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            experience_years REAL DEFAULT 0,
            education TEXT DEFAULT 'none',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resume_skills (
            id SERIAL PRIMARY KEY,
            resume_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
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
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_skills (
            id SERIAL PRIMARY KEY,
            job_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id SERIAL PRIMARY KEY,
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
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matched_skills (
            id SERIAL PRIMARY KEY,
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

class ResumeDB:
    @staticmethod
    def insert_resume(filename: str, text: str, embedding: List[float], 
                     skills: List[str], experience_years: float, education: str) -> int:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM resumes")
        
        cur.execute(
            "INSERT INTO resumes (filename, text, embedding, experience_years, education) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (filename, text, json.dumps(embedding), experience_years, education)
        )
        resume_id = cur.fetchone()[0]
        
        for skill in skills:
            cur.execute("INSERT INTO resume_skills (resume_id, skill) VALUES (%s, %s)", (resume_id, skill))
        
        conn.commit()
        conn.close()
        return resume_id
    
    @staticmethod
    def get_resume(resume_id: int) -> Optional[Dict]:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT id, filename, text, embedding, experience_years, education FROM resumes WHERE id = %s", (resume_id,))
        resume = cur.fetchone()
        
        if not resume:
            conn.close()
            return None
        
        cur.execute("SELECT skill FROM resume_skills WHERE resume_id = %s", (resume_id,))
        skills = [row['skill'] for row in cur.fetchall()]
        
        conn.close()
        
        return {
            'id': resume['id'],
            'filename': resume['filename'],
            'text': resume['text'],
            'embedding': json.loads(resume['embedding']),
            'experience_years': resume['experience_years'],
            'education': resume['education'],
            'skills': skills
        }
    
    @staticmethod
    def list_resumes() -> List[Dict]:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, filename, created_at FROM resumes ORDER BY created_at DESC")
        resumes = [dict(r) for r in cur.fetchall()]
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
            "INSERT INTO jobs (title, company, description, url, embedding, experience_required, education_required) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (title, company, description, url, json.dumps(embedding), experience_required, education_required)
        )
        job_id = cur.fetchone()[0]
        
        for skill in required_skills:
            cur.execute("INSERT INTO job_skills (job_id, skill) VALUES (%s, %s)", (job_id, skill))
        
        conn.commit()
        conn.close()
        return job_id
    
    @staticmethod
    def get_job(job_id: int) -> Optional[Dict]:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT id, title, company, description, url, embedding, experience_required, education_required FROM jobs WHERE id = %s", (job_id,))
        job = cur.fetchone()
        
        if not job:
            conn.close()
            return None
        
        cur.execute("SELECT skill FROM job_skills WHERE job_id = %s", (job_id,))
        skills = [row['skill'] for row in cur.fetchall()]
        
        conn.close()
        
        return {
            'id': job['id'],
            'title': job['title'],
            'company': job['company'],
            'description': job['description'],
            'url': job['url'],
            'embedding': json.loads(job['embedding']),
            'experience_required': job['experience_required'],
            'education_required': job['education_required'],
            'required_skills': skills
        }
    
    @staticmethod
    def get_all_jobs() -> List[Dict]:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id FROM jobs")
        job_ids = [row['id'] for row in cur.fetchall()]
        conn.close()
        return [JobDB.get_job(job_id) for job_id in job_ids]
    
    @staticmethod
    def list_jobs() -> List[Dict]:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, title, company, url, created_at FROM jobs ORDER BY created_at DESC")
        jobs = [dict(j) for j in cur.fetchall()]
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (resume_id, job_id, overall_score, skills_score, experience_score,
              education_score, semantic_score, len(matched_skills), total_required))
        
        match_id = cur.fetchone()[0]
        
        for skill in matched_skills:
            cur.execute("INSERT INTO matched_skills (match_result_id, skill, is_matched) VALUES (%s, %s, %s)",
                       (match_id, skill, True))
        
        for skill in missing_skills:
            cur.execute("INSERT INTO matched_skills (match_result_id, skill, is_matched) VALUES (%s, %s, %s)",
                       (match_id, skill, False))
        
        conn.commit()
        conn.close()
        return match_id

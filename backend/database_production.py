import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import json
from typing import List, Dict, Optional
from contextlib import contextmanager
from config import settings
from logger import logger

class DatabasePool:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self):
        if self._pool is None:
            try:
                self._pool = ThreadedConnectionPool(
                    minconn=1,
                    maxconn=settings.db_pool_size,
                    dsn=settings.database_url
                )
                logger.info("Database pool initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise
    
    @contextmanager
    def get_connection(self):
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            self._pool.putconn(conn)
    
    def close_all(self):
        if self._pool:
            self._pool.closeall()
            logger.info("Database pool closed")

db_pool = DatabasePool()

def init_db():
    db_pool.initialize()
    with db_pool.get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT user_id FROM resumes LIMIT 1")
        except:
            logger.info("Dropping old tables to recreate with user_id")
            cur.execute("DROP TABLE IF EXISTS matched_skills CASCADE")
            cur.execute("DROP TABLE IF EXISTS match_results CASCADE")
            cur.execute("DROP TABLE IF EXISTS job_skills CASCADE")
            cur.execute("DROP TABLE IF EXISTS resume_skills CASCADE")
            cur.execute("DROP TABLE IF EXISTS jobs CASCADE")
            cur.execute("DROP TABLE IF EXISTS resumes CASCADE")
            conn.commit()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                text TEXT NOT NULL,
                embedding TEXT,
                experience_years REAL DEFAULT 0,
                education TEXT DEFAULT 'none',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                description TEXT NOT NULL,
                url TEXT,
                embedding TEXT,
                experience_required REAL DEFAULT 0,
                education_required TEXT DEFAULT 'none',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_resume_user ON resumes(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_job_user ON jobs(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_resume_skills ON resume_skills(resume_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_job_skills ON job_skills(job_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_match_results ON match_results(resume_id, job_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

class UserDB:
    @staticmethod
    def create_user(email: str, hashed_password: str) -> int:
        with db_pool.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (email, hashed_password) VALUES (%s, %s) RETURNING id",
                (email, hashed_password)
            )
            return cur.fetchone()[0]
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        with db_pool.get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id, email, hashed_password FROM users WHERE email = %s", (email,))
            result = cur.fetchone()
            return dict(result) if result else None

class ResumeDB:
    @staticmethod
    def insert_resume(user_id: int, filename: str, text: str, embedding: Optional[List[float]], 
                     skills: List[str], experience_years: float, education: str) -> int:
        with db_pool.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO resumes (user_id, filename, text, embedding, experience_years, education) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (user_id, filename, text, json.dumps(embedding) if embedding else None, experience_years, education)
            )
            resume_id = cur.fetchone()[0]
            
            for skill in skills:
                cur.execute("INSERT INTO resume_skills (resume_id, skill) VALUES (%s, %s)", (resume_id, skill))
            
            logger.info(f"Resume {resume_id} inserted for user {user_id}")
            return resume_id
    
    @staticmethod
    def get_resume(resume_id: int, user_id: int) -> Optional[Dict]:
        with db_pool.get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT id, filename, text, embedding, experience_years, education FROM resumes WHERE id = %s AND user_id = %s",
                (resume_id, user_id)
            )
            resume = cur.fetchone()
            
            if not resume:
                return None
            
            cur.execute("SELECT skill FROM resume_skills WHERE resume_id = %s", (resume_id,))
            skills = [row['skill'] for row in cur.fetchall()]
            
            result = dict(resume)
            result['skills'] = skills
            if result['embedding']:
                result['embedding'] = json.loads(result['embedding'])
            return result
    
    @staticmethod
    def list_resumes(user_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        with db_pool.get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT id, filename, created_at FROM resumes WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (user_id, limit, offset)
            )
            return [dict(r) for r in cur.fetchall()]
    
    @staticmethod
    def delete_resume(resume_id: int, user_id: int):
        with db_pool.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM resumes WHERE id = %s AND user_id = %s", (resume_id, user_id))
            logger.info(f"Resume {resume_id} deleted by user {user_id}")

class JobDB:
    @staticmethod
    def insert_job(user_id: int, title: str, company: str, description: str, url: Optional[str],
                   embedding: Optional[List[float]], required_skills: List[str], 
                   experience_required: float, education_required: str) -> int:
        with db_pool.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO jobs (user_id, title, company, description, url, embedding, experience_required, education_required) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (user_id, title, company, description, url, json.dumps(embedding) if embedding else None, experience_required, education_required)
            )
            job_id = cur.fetchone()[0]
            
            for skill in required_skills:
                cur.execute("INSERT INTO job_skills (job_id, skill) VALUES (%s, %s)", (job_id, skill))
            
            logger.info(f"Job {job_id} inserted for user {user_id}")
            return job_id
    
    @staticmethod
    def get_job(job_id: int, user_id: int) -> Optional[Dict]:
        with db_pool.get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT id, title, company, description, url, embedding, experience_required, education_required FROM jobs WHERE id = %s AND user_id = %s",
                (job_id, user_id)
            )
            job = cur.fetchone()
            
            if not job:
                return None
            
            cur.execute("SELECT skill FROM job_skills WHERE job_id = %s", (job_id,))
            skills = [row['skill'] for row in cur.fetchall()]
            
            result = dict(job)
            result['required_skills'] = skills
            if result['embedding']:
                result['embedding'] = json.loads(result['embedding'])
            return result
    
    @staticmethod
    def get_all_jobs(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        with db_pool.get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT id FROM jobs WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (user_id, limit, offset)
            )
            job_ids = [row['id'] for row in cur.fetchall()]
            return [JobDB.get_job(job_id, user_id) for job_id in job_ids]
    
    @staticmethod
    def list_jobs(user_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        with db_pool.get_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT id, title, company, url, created_at FROM jobs WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (user_id, limit, offset)
            )
            return [dict(j) for j in cur.fetchall()]
    
    @staticmethod
    def delete_job(job_id: int, user_id: int):
        with db_pool.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM jobs WHERE id = %s AND user_id = %s", (job_id, user_id))
            logger.info(f"Job {job_id} deleted by user {user_id}")

class MatchDB:
    @staticmethod
    def save_match_result(resume_id: int, job_id: int, overall_score: float,
                         skills_score: float, experience_score: float, 
                         education_score: float, semantic_score: float,
                         matched_skills: List[str], missing_skills: List[str],
                         total_required: int) -> int:
        with db_pool.get_connection() as conn:
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
            
            return match_id

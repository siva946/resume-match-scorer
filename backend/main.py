from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import asyncio
from contextlib import asynccontextmanager

from parser import get_resume_parser, get_job_parser
from database_production import init_db, ResumeDB, JobDB, MatchDB, UserDB, db_pool
from jobalytics_matcher import get_matcher
from config import settings
from logger import logger
from auth import verify_token, create_access_token, get_password_hash, verify_password, TokenData
from rate_limiter import rate_limiter
from validators import validate_pdf_upload, sanitize_string, validate_email

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ResumSync API")
    init_db()
    yield
    db_pool.close_all()
    logger.info("Shutting down ResumSync API")

app = FastAPI(lifespan=lifespan, title="ResumSync API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)

if settings.environment == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_origins)

resume_parser = get_resume_parser()
job_parser = get_job_parser()
matcher = get_matcher()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class JobDescription(BaseModel):
    title: str
    company: str
    description: str
    url: Optional[str] = None

class MatchJobRequest(BaseModel):
    resume_id: int
    job_description: str

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    try:
        email = validate_email(request.email)
        if len(request.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        existing = UserDB.get_user_by_email(email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = get_password_hash(request.password)
        user_id = UserDB.create_user(email, hashed_password)
        
        token = create_access_token({"user_id": user_id, "email": email})
        logger.info(f"User registered: {email}")
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    try:
        email = validate_email(request.email)
        user = UserDB.get_user_by_email(email)
        
        if not user or not verify_password(request.password, user['hashed_password']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_access_token({"user_id": user['id'], "email": user['email']})
        logger.info(f"User logged in: {email}")
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/resume/upload")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    token: TokenData = Depends(verify_token)
):
    await rate_limiter.check_rate_limit(request)
    
    try:
        content = await validate_pdf_upload(file)
        
        # Parse with timeout
        parsed_data = await asyncio.wait_for(
            asyncio.to_thread(resume_parser.parse_resume, content),
            timeout=settings.api_timeout_seconds
        )
        
        filename = sanitize_string(file.filename, 255)
        
        resume_id = ResumeDB.insert_resume(
            user_id=token.user_id,
            filename=filename,
            text=parsed_data['text'],
            embedding=None,
            skills=parsed_data['skills'],
            experience_years=parsed_data['experience_years'],
            education=parsed_data['education']
        )
        
        logger.info(f"Resume uploaded: {resume_id} by user {token.user_id}")
        return {
            "id": resume_id,
            "filename": filename,
            "text_length": len(parsed_data['text']),
            "skills": parsed_data['skills'],
            "experience_years": parsed_data['experience_years'],
            "education": parsed_data['education']
        }
    except asyncio.TimeoutError:
        logger.error(f"Resume upload timeout for user {token.user_id}")
        raise HTTPException(status_code=408, detail="Processing timeout")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        raise HTTPException(status_code=500, detail="Error processing PDF")

@app.post("/api/jobs")
async def add_job(
    request: Request,
    job: JobDescription,
    token: TokenData = Depends(verify_token)
):
    await rate_limiter.check_rate_limit(request)
    
    try:
        title = sanitize_string(job.title, 255)
        company = sanitize_string(job.company, 255)
        description = sanitize_string(job.description, 50000)
        url = sanitize_string(job.url, 2048) if job.url else None
        
        parsed_job = await asyncio.wait_for(
            asyncio.to_thread(job_parser.parse_job_description, description),
            timeout=settings.api_timeout_seconds
        )
        
        job_id = JobDB.insert_job(
            user_id=token.user_id,
            title=title,
            company=company,
            description=description,
            url=url,
            embedding=None,
            required_skills=parsed_job['required_skills'],
            experience_required=parsed_job['experience_required'],
            education_required=parsed_job['education_required']
        )
        
        logger.info(f"Job added: {job_id} by user {token.user_id}")
        return {
            "id": job_id,
            "title": title,
            "required_skills": parsed_job['required_skills'],
            "experience_required": parsed_job['experience_required']
        }
    except asyncio.TimeoutError:
        logger.error(f"Job add timeout for user {token.user_id}")
        raise HTTPException(status_code=408, detail="Processing timeout")
    except Exception as e:
        logger.error(f"Job add error: {e}")
        raise HTTPException(status_code=500, detail="Error adding job")

@app.get("/api/matches/{resume_id}")
async def get_matches(
    request: Request,
    resume_id: int,
    limit: int = 10,
    token: TokenData = Depends(verify_token)
):
    await rate_limiter.check_rate_limit(request)
    
    try:
        if limit > settings.max_jobs_per_request:
            limit = settings.max_jobs_per_request
        
        resume_data = ResumeDB.get_resume(resume_id, token.user_id)
        if not resume_data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        jobs = JobDB.get_all_jobs(token.user_id, limit=settings.max_jobs_per_request)
        matches = []
        
        async def process_job(job):
            result = await asyncio.to_thread(
                matcher.get_match_result,
                resume_data['text'],
                job['description']
            )
            
            MatchDB.save_match_result(
                resume_id=resume_id,
                job_id=job['id'],
                overall_score=result['score'],
                skills_score=0,
                experience_score=0,
                education_score=0,
                semantic_score=result['score'],
                matched_skills=result['matches'],
                missing_skills=result['unmatches'],
                total_required=len(result['unmatches']) + len(result['matches'])
            )
            
            return {
                "job_id": job['id'],
                "title": job['title'],
                "company": job['company'],
                "score": result['score'],
                "matched_skills": result['matches'],
                "missing_skills": result['unmatches'],
                "description": job['description'][:200],
                "url": job['url']
            }
        
        tasks = [process_job(job) for job in jobs]
        matches = await asyncio.wait_for(
            asyncio.gather(*tasks),
            timeout=settings.api_timeout_seconds
        )
        
        matches.sort(key=lambda x: x['score'], reverse=True)
        logger.info(f"Matches calculated for resume {resume_id}")
        return matches[:limit]
    except asyncio.TimeoutError:
        logger.error(f"Matches timeout for resume {resume_id}")
        raise HTTPException(status_code=408, detail="Processing timeout")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Matches error: {e}")
        raise HTTPException(status_code=500, detail="Error calculating matches")

@app.get("/api/resumes")
async def list_resumes(
    request: Request,
    token: TokenData = Depends(verify_token),
    limit: int = 100,
    offset: int = 0
):
    await rate_limiter.check_rate_limit(request)
    return ResumeDB.list_resumes(token.user_id, limit, offset)

@app.get("/api/jobs")
async def list_jobs(
    request: Request,
    token: TokenData = Depends(verify_token),
    limit: int = 100,
    offset: int = 0
):
    await rate_limiter.check_rate_limit(request)
    return JobDB.list_jobs(token.user_id, limit, offset)

@app.delete("/api/jobs/{job_id}")
async def delete_job(
    request: Request,
    job_id: int,
    token: TokenData = Depends(verify_token)
):
    await rate_limiter.check_rate_limit(request)
    job = JobDB.get_job(job_id, token.user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    JobDB.delete_job(job_id, token.user_id)
    logger.info(f"Job {job_id} deleted by user {token.user_id}")
    return {"message": "Job deleted successfully"}

@app.delete("/api/resumes/{resume_id}")
async def delete_resume(
    request: Request,
    resume_id: int,
    token: TokenData = Depends(verify_token)
):
    await rate_limiter.check_rate_limit(request)
    resume = ResumeDB.get_resume(resume_id, token.user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    ResumeDB.delete_resume(resume_id, token.user_id)
    logger.info(f"Resume {resume_id} deleted by user {token.user_id}")
    return {"message": "Resume deleted successfully"}

@app.post("/api/match-job")
async def match_job(
    request: Request,
    match_request: MatchJobRequest,
    token: TokenData = Depends(verify_token)
):
    await rate_limiter.check_rate_limit(request)
    
    try:
        resume_data = ResumeDB.get_resume(match_request.resume_id, token.user_id)
        if not resume_data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        description = sanitize_string(match_request.job_description, 50000)
        
        result = await asyncio.wait_for(
            asyncio.to_thread(matcher.get_match_result, resume_data['text'], description),
            timeout=settings.api_timeout_seconds
        )
        
        return {
            "score": result['score'],
            "matched_skills": result['matches'],
            "missing_skills": result['unmatches']
        }
    except asyncio.TimeoutError:
        logger.error(f"Match job timeout for user {token.user_id}")
        raise HTTPException(status_code=408, detail="Processing timeout")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Match job error: {e}")
        raise HTTPException(status_code=500, detail="Error matching job")



@app.get("/")
async def root():
    return {
        "status": "ResumSync API is running",
        "version": "2.0.0",
        "environment": settings.environment
    }

@app.get("/health")
async def health():
    try:
        # Check database connection
        with db_pool.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
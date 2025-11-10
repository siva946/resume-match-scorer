from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from ml_model import get_model
from parser import get_resume_parser, get_job_parser
import os
if os.getenv('DATABASE_URL'):
    from database_postgres import init_db, ResumeDB, JobDB, MatchDB
else:
    from database import init_db, ResumeDB, JobDB, MatchDB

app = FastAPI()

origins=[
    "https://resumsync-frontend.onrender.com",
    "https://resumsync.vercel.app/",
    "http://localhost:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

init_db()

# Lazy load model to save memory
ml_model = None
resume_parser = get_resume_parser()
job_parser = get_job_parser()

def get_ml_model():
    global ml_model
    if ml_model is None:
        ml_model = get_model()
    return ml_model

class JobDescription(BaseModel):
    title: str
    company: str
    description: str
    url: Optional[str] = None

class MatchJobRequest(BaseModel):
    resume_id: int
    job_description: str

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files supported")
    
    try:
        content = await file.read()
        parsed_data = resume_parser.parse_resume(content)
        
        embedding = get_ml_model().encode(parsed_data['text'])
        
        resume_id = ResumeDB.insert_resume(
            filename=file.filename,
            text=parsed_data['text'],
            embedding=embedding,
            skills=parsed_data['skills'],
            experience_years=parsed_data['experience_years'],
            education=parsed_data['education']
        )
        
        return {
            "id": resume_id,
            "filename": file.filename,
            "text_length": len(parsed_data['text']),
            "skills": parsed_data['skills'],
            "experience_years": parsed_data['experience_years'],
            "education": parsed_data['education']
        }
    except Exception as e:
        raise HTTPException(500, f"Error processing PDF: {str(e)}")

@app.post("/api/jobs")
async def add_job(job: JobDescription):
    parsed_job = job_parser.parse_job_description(job.description)
    embedding = get_ml_model().encode(job.description)
    
    job_id = JobDB.insert_job(
        title=job.title,
        company=job.company,
        description=job.description,
        url=job.url,
        embedding=embedding,
        required_skills=parsed_job['required_skills'],
        experience_required=parsed_job['experience_required'],
        education_required=parsed_job['education_required']
    )
    
    return {
        "id": job_id,
        "title": job.title,
        "required_skills": parsed_job['required_skills'],
        "experience_required": parsed_job['experience_required']
    }

@app.get("/api/matches/{resume_id}")
async def get_matches(resume_id: int, limit: int = 10):
    resume_data = ResumeDB.get_resume(resume_id)
    if not resume_data:
        raise HTTPException(404, "Resume not found")
    
    jobs = JobDB.get_all_jobs()
    matches = []
    
    for job in jobs:
        overall_score, breakdown = get_ml_model().calculate_match_score(resume_data, job)
        
        # Save match result to database
        MatchDB.save_match_result(
            resume_id=resume_id,
            job_id=job['id'],
            overall_score=breakdown['overall_score'],
            skills_score=breakdown['skills_score'],
            experience_score=breakdown['experience_score'],
            education_score=breakdown['education_score'],
            semantic_score=breakdown['semantic_score'],
            matched_skills=breakdown['matched_skills'],
            missing_skills=breakdown['missing_skills'],
            total_required=breakdown['total_required_skills']
        )
        
        matches.append({
            "job_id": job['id'],
            "title": job['title'],
            "company": job['company'],
            "score": breakdown['overall_score'],
            "skills_score": breakdown['skills_score'],
            "experience_score": breakdown['experience_score'],
            "education_score": breakdown['education_score'],
            "semantic_score": breakdown['semantic_score'],
            "matched_skills": breakdown['matched_skills'],
            "missing_skills": breakdown['missing_skills'],
            "description": job['description'][:200],
            "url": job['url']
        })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches[:limit]

@app.get("/api/resumes")
async def list_resumes():
    return ResumeDB.list_resumes()

@app.get("/api/jobs")
async def list_jobs():
    return JobDB.list_jobs()

@app.post("/api/match-job")
async def match_job(request: MatchJobRequest):
    resume_data = ResumeDB.get_resume(request.resume_id)
    if not resume_data:
        raise HTTPException(404, "Resume not found")
    
    parsed_job = job_parser.parse_job_description(request.job_description)
    job_embedding = get_ml_model().encode(request.job_description)
    
    job_data = {
        'embedding': job_embedding,
        'required_skills': parsed_job['required_skills'],
        'experience_required': parsed_job['experience_required'],
        'education_required': parsed_job['education_required']
    }
    
    overall_score, breakdown = get_ml_model().calculate_match_score(resume_data, job_data)
    
    return {
        "score": breakdown['overall_score'],
        "breakdown": {
            "skills_score": breakdown['skills_score'],
            "experience_score": breakdown['experience_score'],
            "education_score": breakdown['education_score'],
            "semantic_score": breakdown['semantic_score']
        },
        "matched_skills": breakdown['matched_skills'],
        "missing_skills": breakdown['missing_skills'],
        "experience_match": resume_data['experience_years'] >= parsed_job['experience_required']
    }

@app.get("/api/debug/resume/{resume_id}")
async def debug_resume(resume_id: int):
    resume_data = ResumeDB.get_resume(resume_id)
    if not resume_data:
        raise HTTPException(404, "Resume not found")
    return {
        "skills": resume_data['skills'],
        "experience_years": resume_data['experience_years'],
        "education": resume_data['education']
    }

@app.get("/api/debug/job/{job_id}")
async def debug_job(job_id: int):
    job_data = JobDB.get_job(job_id)
    if not job_data:
        raise HTTPException(404, "Job not found")
    return {
        "required_skills": job_data['required_skills'],
        "experience_required": job_data['experience_required'],
        "education_required": job_data['education_required']
    }

@app.post("/api/test-extraction")
async def test_extraction(request: dict):
    """Test endpoint to see what's being extracted from job description"""
    description = request.get('description', '')
    parsed = job_parser.parse_job_description(description)
    return {
        "description_length": len(description),
        "extracted_skills": parsed['required_skills'],
        "extracted_experience": parsed['experience_required'],
        "extracted_education": parsed['education_required']
    }

@app.get("/")
async def root():
    return {"status": "ResumSync API is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

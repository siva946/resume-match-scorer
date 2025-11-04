from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from ml_model import get_model
from parser import get_resume_parser, get_job_parser
from database import init_db, ResumeDB, JobDB

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Get model and parser instances
ml_model = get_model()
resume_parser = get_resume_parser()
job_parser = get_job_parser()

class JobDescription(BaseModel):
    title: str
    company: str
    description: str
    url: Optional[str] = None

class MatchResult(BaseModel):
    job_id: int
    title: str
    company: str
    score: float
    description: str

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
        
        embedding = ml_model.encode(parsed_data['text'])
        
        resume_id = ResumeDB.insert_resume(
            filename=file.filename,
            text=parsed_data['text'],
            embedding=embedding,
            skills=parsed_data['skills'],
            experience_years=parsed_data['experience_years'],
            experience_entries=parsed_data['experience_entries'],
            education_level=parsed_data['education_level'],
            degrees=parsed_data['degrees']
        )
        
        return {
            "id": resume_id,
            "filename": file.filename,
            "text_length": len(parsed_data['text']),
            "skills": parsed_data['skills'],
            "experience_years": parsed_data['experience_years'],
            "education_level": parsed_data['education_level']
        }
    except Exception as e:
        raise HTTPException(500, f"Error processing PDF: {str(e)}")

@app.post("/api/jobs")
async def add_job(job: JobDescription):
    parsed_job = job_parser.parse_job_description(job.description)
    embedding = ml_model.encode(job.description)
    
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
    
    return {"id": job_id, "title": job.title}

@app.get("/api/matches/{resume_id}")
async def get_matches(resume_id: int, limit: int = 10):
    resume_data = ResumeDB.get_resume(resume_id)
    if not resume_data:
        raise HTTPException(404, "Resume not found")
    
    jobs = JobDB.get_all_jobs()
    matches = []
    
    for job in jobs:
        score = ml_model.calculate_match_score(resume_data, job)
        
        matches.append({
            "job_id": job['id'],
            "title": job['title'],
            "company": job['company'],
            "score": score,
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
    job_embedding = ml_model.encode(request.job_description)
    
    job_data = {
        'embedding': job_embedding,
        'required_skills': parsed_job['required_skills'],
        'experience_required': parsed_job['experience_required'],
        'education_required': parsed_job['education_required']
    }
    
    score = ml_model.calculate_match_score(resume_data, job_data)
    
    return {
        "score": score,
        "matched_skills": list(set(resume_data['skills']) & set(parsed_job['required_skills'])),
        "missing_skills": list(set(parsed_job['required_skills']) - set(resume_data['skills'])),
        "experience_match": resume_data['experience_years'] >= parsed_job['experience_required']
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

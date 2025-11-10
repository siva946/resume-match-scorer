from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Tuple

class JobalyticsModel:
    """Jobalytics.co matching algorithm"""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    
    def encode(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()
    
    def cosine_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        a = np.array(emb1)
        b = np.array(emb2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def calculate_match_score(self, resume_data: Dict, job_data: Dict) -> Tuple[float, Dict]:
        """
        Jobalytics.co formula:
        - Skills Match: 50%
        - Experience Match: 20%
        - Education Match: 10%
        - Semantic Similarity: 20%
        """
        
        # 1. Skills matching (50%)
        resume_skills = set(s.lower() for s in resume_data.get('skills', []))
        job_skills = set(s.lower() for s in job_data.get('required_skills', []))
        
        if job_skills:
            matched = resume_skills & job_skills
            skills_score = len(matched) / len(job_skills)
        else:
            skills_score = 1.0
        
        # 2. Experience matching (20%)
        resume_exp = resume_data.get('experience_years', 0)
        required_exp = job_data.get('experience_required', 0)
        
        if required_exp == 0:
            experience_score = 1.0
        elif resume_exp >= required_exp:
            experience_score = 1.0
        else:
            experience_score = resume_exp / required_exp
        
        # 3. Education matching (10%)
        education_levels = {'none': 0, 'bachelor': 1, 'master': 2, 'phd': 3}
        resume_edu = education_levels.get(resume_data.get('education', 'none'), 0)
        required_edu = education_levels.get(job_data.get('education_required', 'none'), 0)
        
        if required_edu == 0:
            education_score = 1.0
        elif resume_edu >= required_edu:
            education_score = 1.0
        else:
            education_score = resume_edu / required_edu if required_edu > 0 else 0.5
        
        # 4. Semantic similarity (20%)
        semantic_score = self.cosine_similarity(
            resume_data['embedding'],
            job_data['embedding']
        )
        
        # Final weighted score
        overall_score = (
            skills_score * 0.50 +
            experience_score * 0.20 +
            education_score * 0.10 +
            semantic_score * 0.20
        )
        
        # Get matched and missing skills
        matched_skills = list(resume_skills & job_skills)
        missing_skills = list(job_skills - resume_skills)
        
        breakdown = {
            'overall_score': round(overall_score, 4),
            'skills_score': round(skills_score, 4),
            'experience_score': round(experience_score, 4),
            'education_score': round(education_score, 4),
            'semantic_score': round(semantic_score, 4),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'total_required_skills': len(job_skills)
        }
        
        return overall_score, breakdown

_model_instance = None

def get_model() -> JobalyticsModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = JobalyticsModel()
    return _model_instance

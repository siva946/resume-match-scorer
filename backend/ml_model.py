from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import re

class JobalyticsModel:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    
    def encode(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.model.encode(text).tolist()
    
    def cosine_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        a = np.array(emb1)
        b = np.array(emb2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def calculate_match_score(self, resume_data: Dict, job_data: Dict) -> float:
        """
        Calculate comprehensive match score with weighted components
        """
        # Skills matching (40% weight)
        skills_score = self._calculate_skills_match(
            resume_data.get('skills', []),
            job_data.get('required_skills', [])
        )
        
        # Experience matching (20% weight)
        exp_score = self._calculate_experience_match(
            resume_data.get('experience_years', 0),
            job_data.get('experience_required', 0)
        )
        
        # Education matching (10% weight)
        edu_score = self._calculate_education_match(
            resume_data.get('education_level', 0),
            job_data.get('education_required', 0)
        )
        
        # Semantic similarity (30% weight)
        semantic_score = self.cosine_similarity(
            resume_data['embedding'],
            job_data['embedding']
        )
        
        # Weighted final score
        final_score = (
            skills_score * 0.40 +
            exp_score * 0.20 +
            edu_score * 0.10 +
            semantic_score * 0.30
        )
        
        return round(final_score, 4)
    
    def _calculate_skills_match(self, resume_skills: List[str], job_skills: List[str]) -> float:
        """Calculate skill overlap with Jaccard similarity"""
        if not job_skills:
            return 0.5
        
        resume_set = set(s.lower().strip() for s in resume_skills if s)
        job_set = set(s.lower().strip() for s in job_skills if s)
        
        if not job_set:
            return 0.5
        
        intersection = len(resume_set & job_set)
        union = len(resume_set | job_set)
        
        jaccard = intersection / union if union > 0 else 0
        coverage = intersection / len(job_set) if job_set else 0
        
        return (jaccard * 0.4 + coverage * 0.6)
    
    def _calculate_experience_match(self, resume_years: float, required_years: float) -> float:
        """Calculate experience match with diminishing returns"""
        if required_years == 0:
            return 0.8
        
        if resume_years >= required_years:
            excess = resume_years - required_years
            return min(1.0, 0.95 + (excess * 0.01))
        else:
            ratio = resume_years / required_years
            if ratio >= 0.8:
                return 0.7 + (ratio - 0.8) * 1.25
            else:
                return ratio * 0.875
    
    def _calculate_education_match(self, resume_level: int, required_level: int) -> float:
        """Calculate education match (0=None, 1=Bachelor, 2=Master, 3=PhD)"""
        if required_level == 0:
            return 1.0
        
        if resume_level >= required_level:
            return 1.0
        elif resume_level == required_level - 1:
            return 0.7
        else:
            return 0.4

# Singleton instance
_model_instance = None

def get_model() -> JobalyticsModel:
    """Get or create model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = JobalyticsModel()
    return _model_instance

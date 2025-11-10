import re
import pdfplumber
from typing import Dict, List, Set
import io

class ResumeParser:
    SKILLS = [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala',
        'react', 'angular', 'vue', 'node.js', 'nodejs', 'express', 'django', 'flask', 'fastapi', 'spring', 'asp.net',
        'html', 'css', 'sass', 'less', 'bootstrap', 'tailwind', 'jquery', 'webpack', 'next.js', 'nuxt',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'dynamodb', 'oracle', 'sqlite', 'elasticsearch',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'devops',
        'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision', 'data science', 'tensorflow', 'pytorch', 
        'pandas', 'numpy', 'scikit-learn', 'spark', 'hadoop', 'kafka', 'airflow',
        'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'agile', 'scrum', 'kanban',
        'linux', 'unix', 'bash', 'powershell', 'windows', 'macos',
        'rest api', 'graphql', 'microservices', 'serverless', 'api', 'restful',
        'testing', 'unit testing', 'integration testing', 'jest', 'pytest', 'selenium', 'cypress',
        'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator',
        'excel', 'powerpoint', 'word', 'google sheets', 'tableau', 'power bi',
        'communication', 'leadership', 'teamwork', 'problem solving', 'analytical', 'critical thinking'
    ]
    
    def parse_pdf(self, file_content: bytes) -> str:
        """Extract text using pdfplumber"""
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        full_text = "\n".join(text_parts)
        return full_text.strip()
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        text_lower = text.lower()
        text_lower = re.sub(r'[^\w\s.#+/-]', ' ', text_lower)
        
        found_skills = []
        for skill in self.SKILLS:
            skill_normalized = skill.replace('.', r'\.').replace('+', r'\+')
            if re.search(r'\b' + skill_normalized + r'\b', text_lower):
                found_skills.append(skill)
        
        return found_skills
    
    def extract_experience_years(self, text: str) -> float:
        """Extract years of experience"""
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)[\s\w]*(?:of\s+)?experience',
            r'experience[:\s]+(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s+experience'
        ]
        
        max_years = 0.0
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                years = float(match)
                if 0 < years < 50:
                    max_years = max(max_years, years)
        
        return max_years
    
    def extract_education(self, text: str) -> str:
        """Extract highest education level"""
        text_lower = text.lower()
        
        if re.search(r'\b(phd|ph\.d|doctorate|doctoral)\b', text_lower):
            return 'phd'
        elif re.search(r'\b(master|masters|mba|m\.s|m\.tech|m\.e|m\.sc)\b', text_lower):
            return 'master'
        elif re.search(r'\b(bachelor|bachelors|b\.s|b\.tech|b\.e|b\.sc|undergraduate)\b', text_lower):
            return 'bachelor'
        
        return 'none'
    
    def parse_resume(self, file_content: bytes) -> Dict:
        """Parse resume and extract all information"""
        text = self.parse_pdf(file_content)
        
        if not text.strip():
            raise ValueError("Could not extract text from PDF")
        
        return {
            'text': text,
            'skills': self.extract_skills(text),
            'experience_years': self.extract_experience_years(text),
            'education': self.extract_education(text)
        }

class JobParser:
    def __init__(self):
        self.resume_parser = ResumeParser()
    
    def parse_job_description(self, description: str) -> Dict:
        """Parse job description"""
        return {
            'required_skills': self.resume_parser.extract_skills(description),
            'experience_required': self.resume_parser.extract_experience_years(description),
            'education_required': self.resume_parser.extract_education(description)
        }

_resume_parser = None
_job_parser = None

def get_resume_parser() -> ResumeParser:
    global _resume_parser
    if _resume_parser is None:
        _resume_parser = ResumeParser()
    return _resume_parser

def get_job_parser() -> JobParser:
    global _job_parser
    if _job_parser is None:
        _job_parser = JobParser()
    return _job_parser

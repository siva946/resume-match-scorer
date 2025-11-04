import re
from typing import Dict, List, Tuple
import PyPDF2
import io

class ResumeParser:
    SKILLS_DATABASE = {
        'programming': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'scala', 'kotlin', 'swift', 'php', 'ruby', 'r', 'matlab', 'perl'],
        'web': ['react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'asp.net', 'html', 'css', 'sass', 'webpack', 'next.js'],
        'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'dynamodb', 'oracle', 'sqlite', 'elasticsearch'],
        'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'devops'],
        'data': ['machine learning', 'deep learning', 'ai', 'data science', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn', 'spark', 'hadoop', 'kafka'],
        'tools': ['git', 'jira', 'confluence', 'linux', 'bash', 'powershell', 'vim', 'vscode', 'intellij']
    }
    
    DEGREE_LEVELS = {
        'phd': 3, 'ph.d': 3, 'doctorate': 3, 'doctoral': 3,
        'master': 2, 'masters': 2, 'mba': 2, 'm.s': 2, 'm.tech': 2, 'm.e': 2, 'm.sc': 2,
        'bachelor': 1, 'bachelors': 1, 'b.s': 1, 'b.tech': 1, 'b.e': 1, 'b.sc': 1, 'undergraduate': 1
    }
    
    def parse_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF with improved parsing"""
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text_parts = []
        
        for page in pdf_reader.pages:
            page_text = page.extract_text() or ""
            # Clean up common PDF artifacts
            page_text = re.sub(r'\s+', ' ', page_text)
            page_text = re.sub(r'[^\x00-\x7F]+', ' ', page_text)
            text_parts.append(page_text)
        
        full_text = " ".join(text_parts)
        return full_text.strip()
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills with improved detection"""
        text_lower = text.lower()
        found_skills = []
        
        for category, skills in self.SKILLS_DATABASE.items():
            for skill in skills:
                # Word boundary matching for accuracy
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.append(skill)
        
        return list(set(found_skills))
    
    def extract_experience(self, text: str) -> Tuple[float, List[Dict]]:
        """Extract total years and experience entries"""
        patterns = [
            r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'experience[:\s]*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)',
            r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)'
        ]
        
        max_years = 0.0
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                years = float(match)
                if years > max_years and years < 50:
                    max_years = years
        
        # Extract experience sections
        experiences = self._extract_experience_sections(text)
        
        return max_years, experiences
    
    def _extract_experience_sections(self, text: str) -> List[Dict]:
        """Extract individual job experiences"""
        experiences = []
        
        # Look for date patterns (e.g., "2020-2023", "Jan 2020 - Present")
        date_pattern = r'(\d{4}|\w{3,9}\s+\d{4})\s*[-–—]\s*(\d{4}|\w{3,9}\s+\d{4}|Present|Current)'
        matches = re.finditer(date_pattern, text, re.IGNORECASE)
        
        for match in matches:
            start_date = match.group(1)
            end_date = match.group(2)
            
            # Extract surrounding context (job title and company)
            start_pos = max(0, match.start() - 200)
            end_pos = min(len(text), match.end() + 200)
            context = text[start_pos:end_pos]
            
            experiences.append({
                'start_date': start_date,
                'end_date': end_date,
                'context': context.strip()
            })
        
        return experiences[:10]  # Limit to 10 most recent
    
    def extract_education(self, text: str) -> Tuple[int, List[str]]:
        """Extract education level and degrees"""
        text_lower = text.lower()
        max_level = 0
        found_degrees = []
        
        for degree, level in self.DEGREE_LEVELS.items():
            if re.search(r'\b' + re.escape(degree) + r'\b', text_lower):
                found_degrees.append(degree)
                if level > max_level:
                    max_level = level
        
        return max_level, list(set(found_degrees))
    
    def parse_resume(self, file_content: bytes) -> Dict:
        """Complete resume parsing"""
        text = self.parse_pdf(file_content)
        
        if not text.strip():
            raise ValueError("Could not extract text from PDF")
        
        skills = self.extract_skills(text)
        experience_years, experience_entries = self.extract_experience(text)
        education_level, degrees = self.extract_education(text)
        
        return {
            'text': text,
            'skills': skills,
            'experience_years': experience_years,
            'experience_entries': experience_entries,
            'education_level': education_level,
            'degrees': degrees
        }

class JobParser:
    def __init__(self):
        self.resume_parser = ResumeParser()
    
    def parse_job_description(self, description: str) -> Dict:
        """Parse job description for structured data"""
        skills = self.resume_parser.extract_skills(description)
        experience_years, _ = self.resume_parser.extract_experience(description)
        education_level, _ = self.resume_parser.extract_education(description)
        
        return {
            'required_skills': skills,
            'experience_required': experience_years,
            'education_required': education_level
        }

# Singleton instances
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

import re
from typing import List, Dict, Tuple, Set

# Keyword lists from Jobalytics
from jobalytics_keywords import (
    general_keywords,
    swe_essentials,
    swe_nice_to_haves,
    pm_marketing_keywords,
    synonyms
)

WORD_PREFIXES = [
    "communicat", "strateg", "project manage", "product manage",
    "engineer", "collaborat", "machine learning"
]

class JobalyticsMatcher:
    
    def fetch_domain(self, text: str) -> str:
        """Detect job domain from text"""
        text_lower = text.lower()
        
        swe_regex = re.compile(
            r"engineer(ing)?|developer|programmer|coder|solutions architect|"
            r"machine learning|ai|tech( analyst)?",
            re.IGNORECASE
        )
        
        pm_marketing_regex = re.compile(
            r"product|marketing|marketer|advertising|advertiser|copywriting|"
            r"copywriter|social media|brand|ambassador|cmo",
            re.IGNORECASE
        )
        
        if swe_regex.search(text_lower):
            return "swe"
        elif pm_marketing_regex.search(text_lower):
            return "pm_marketing"
        else:
            return "general"
    
    def get_keywords_from_text(self, text: str, words: List[str]) -> List[str]:
        """Extract keywords from text"""
        # Filter special words (with non-word chars)
        regex_special = re.compile(r'\b[a-z]\W+\B', re.IGNORECASE)
        special_words = [w for w in words if regex_special.search(w)]
        normal_words = [w for w in words if not regex_special.search(w)]
        
        # Escape regex metacharacters
        regex_metachars = re.compile(r'[(){[*+?.\\^$|]')
        normal_words = [regex_metachars.sub(r'\\\g<0>', w) for w in normal_words]
        special_words = [regex_metachars.sub(r'\\\g<0>', w) for w in special_words]
        
        # Build regex pattern
        pattern = r'\b(?:' + '|'.join(special_words) + r')\B|\b(?:' + '|'.join(normal_words) + r')\b'
        regex = re.compile(pattern, re.IGNORECASE)
        
        matches = regex.findall(text)
        keywords = list(set([m.lower() for m in matches]))
        
        # Replace dashes with spaces
        keywords = [k.replace('-', ' ') for k in keywords]
        
        return keywords
    
    def get_keywords_with_suffixes(self, text: str, domain: List[str]) -> List[str]:
        """Extract keywords with suffix variations"""
        suffixes = ["ing", "d", "ed", "s"]
        words = sorted(domain, key=len, reverse=True)
        
        all_keywords = self.get_keywords_from_text(text, words)
        
        for suffix in suffixes:
            suffix_words = [w + suffix for w in words]
            suffix_keywords = self.get_keywords_from_text(text, suffix_words)
            # Remove suffix from matched keywords
            suffix_keywords = [k[:-len(suffix)] for k in suffix_keywords]
            all_keywords.extend(suffix_keywords)
        
        return list(set(all_keywords))
    
    def correct_for_synonyms(self, keywords: List[str]) -> List[str]:
        """Replace synonyms with canonical form"""
        idx_to_kw = {}
        kw_to_idx = {}
        
        for kw in keywords:
            for i, synonym_group in enumerate(synonyms):
                if kw in synonym_group:
                    kw_to_idx[kw] = i
                    if i not in idx_to_kw:
                        idx_to_kw[i] = kw
        
        result = []
        for kw in keywords:
            if kw in kw_to_idx:
                result.append(idx_to_kw[kw_to_idx[kw]])
            else:
                result.append(kw)
        
        return list(set(result))
    
    def correct_for_prefixes(self, keywords: List[str]) -> List[str]:
        """Normalize keywords with common prefixes"""
        prefix_to_kw = {}
        kw_to_prefix = {}
        
        for prefix in WORD_PREFIXES:
            for kw in keywords:
                if kw.startswith(prefix):
                    kw_to_prefix[kw] = prefix
                    if prefix not in prefix_to_kw:
                        prefix_to_kw[prefix] = kw
        
        result = []
        for kw in keywords:
            if kw in kw_to_prefix:
                result.append(prefix_to_kw[kw_to_prefix[kw]])
            else:
                result.append(kw)
        
        return list(set(result))
    
    def match_basic(self, resume_keywords: List[str], job_keywords: List[str]) -> Dict:
        """Basic matching algorithm for general/pm_marketing"""
        resume_kw = [k.lower() for k in resume_keywords]
        job_kw = [k.lower() for k in job_keywords]
        
        resume_kw = self.correct_for_prefixes(self.correct_for_synonyms(resume_kw))
        job_kw = self.correct_for_prefixes(self.correct_for_synonyms(job_kw))
        
        matched = list(set(resume_kw) & set(job_kw))
        missing = list(set(job_kw) - set(resume_kw))
        
        score = len(matched) / len(job_kw) if job_kw else 0.0
        
        return {
            'score': round(score, 4),
            'matches': matched,
            'unmatches': missing
        }
    
    def match_weighted(
        self,
        resume_essentials: List[str],
        resume_nice: List[str],
        job_essentials: List[str],
        job_nice: List[str]
    ) -> Dict:
        """Weighted matching algorithm for SWE"""
        resume_essentials = self.correct_for_prefixes(
            self.correct_for_synonyms([k.lower() for k in resume_essentials])
        )
        resume_nice = self.correct_for_prefixes(
            self.correct_for_synonyms([k.lower() for k in resume_nice])
        )
        job_essentials = self.correct_for_prefixes(
            self.correct_for_synonyms([k.lower() for k in job_essentials])
        )
        job_nice = self.correct_for_prefixes(
            self.correct_for_synonyms([k.lower() for k in job_nice])
        )
        
        essentials_matched = list(set(job_essentials) & set(resume_essentials))
        essentials_missing = list(set(job_essentials) - set(resume_essentials))
        
        nice_matched = list(set(job_nice) & set(resume_nice))
        nice_missing = list(set(job_nice) - set(resume_nice))
        
        if not essentials_matched and not essentials_missing and not nice_matched and not nice_missing:
            score = 0.0
        else:
            score = (
                (len(essentials_matched) * 5 + len(nice_matched)) /
                ((len(essentials_matched) + len(essentials_missing)) * 5 +
                 len(nice_matched) + len(nice_missing))
            )
        
        return {
            'score': round(score, 4),
            'matches': essentials_matched + nice_matched,
            'unmatches': essentials_missing + nice_missing
        }
    
    def get_match_result(self, resume_text: str, job_text: str) -> Dict:
        """Main matching function - exact Jobalytics algorithm"""
        domain = self.fetch_domain(job_text)
        
        if domain == "swe":
            resume_ess = self.get_keywords_with_suffixes(resume_text, swe_essentials)
            resume_nice = self.get_keywords_with_suffixes(resume_text, swe_nice_to_haves)
            job_ess = self.get_keywords_with_suffixes(job_text, swe_essentials)
            job_nice = self.get_keywords_with_suffixes(job_text, swe_nice_to_haves)
            
            return self.match_weighted(resume_ess, resume_nice, job_ess, job_nice)
        else:
            if domain == "pm_marketing":
                keywords = pm_marketing_keywords
            else:
                keywords = general_keywords
            
            resume_kw = self.get_keywords_with_suffixes(resume_text, keywords)
            job_kw = self.get_keywords_with_suffixes(job_text, keywords)
            
            return self.match_basic(resume_kw, job_kw)

_matcher = None

def get_matcher() -> JobalyticsMatcher:
    global _matcher
    if _matcher is None:
        _matcher = JobalyticsMatcher()
    return _matcher

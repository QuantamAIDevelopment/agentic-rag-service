"""Advanced query preprocessing for better search quality."""

import re
from typing import List, Dict, Any
from app.config.settings import settings

class QueryProcessor:
    def __init__(self):
        self.legal_abbreviations = {
            'sec': 'section',
            's.': 'section',
            'sub-sec': 'subsection',
            'para': 'paragraph',
            'art': 'article',
            'r/w': 'read with',
            'viz': 'namely',
            'w.r.t': 'with respect to',
            'u/s': 'under section'
        }
        
        self.legal_synonyms = {
            'established': ['constituted', 'formed', 'created'],
            'authority': ['body', 'organization', 'agency'],
            'provision': ['clause', 'section', 'rule'],
            'regulation': ['rule', 'guideline', 'directive']
        }
    
    def preprocess_query(self, query: str) -> str:
        """Enhanced query preprocessing."""
        # Clean and normalize
        query = query.strip().lower()
        
        # Expand abbreviations
        for abbr, full in self.legal_abbreviations.items():
            query = re.sub(rf'\b{re.escape(abbr)}\b', full, query, flags=re.IGNORECASE)
        
        # Fix common typos
        query = self._fix_common_typos(query)
        
        # Add synonyms for key terms
        query = self._add_synonyms(query)
        
        return query
    
    def _fix_common_typos(self, query: str) -> str:
        """Fix common spelling mistakes."""
        typo_fixes = {
            'recieve': 'receive',
            'seperate': 'separate',
            'occured': 'occurred',
            'developement': 'development',
            'goverment': 'government',
            'committe': 'committee'
        }
        
        for typo, correct in typo_fixes.items():
            query = re.sub(rf'\b{typo}\b', correct, query, flags=re.IGNORECASE)
        
        return query
    
    def _add_synonyms(self, query: str) -> str:
        """Add relevant synonyms to expand search."""
        words = query.split()
        expanded_words = []
        
        for word in words:
            expanded_words.append(word)
            if word in self.legal_synonyms:
                # Add first synonym only to avoid query bloat
                expanded_words.append(self.legal_synonyms[word][0])
        
        return ' '.join(expanded_words)
    
    def extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms for enhanced search."""
        # Remove stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        
        words = re.findall(r'\b\w+\b', query.lower())
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        return key_terms[:10]  # Limit to top 10 terms

query_processor = QueryProcessor()
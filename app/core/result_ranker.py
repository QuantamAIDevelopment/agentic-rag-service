"""Advanced result ranking for better search quality."""

from typing import List, Dict, Any
import re

class ResultRanker:
    def __init__(self):
        self.legal_keywords = ['section', 'subsection', 'act', 'rule', 'regulation', 'authority', 'provision', 'statute']
        self.importance_keywords = ['shall', 'must', 'required', 'mandatory', 'prohibited', 'entitled']
    
    def rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Enhanced result ranking with multiple factors."""
        if not results:
            return results
        
        query_terms = set(query.lower().split())
        
        for result in results:
            score = self._calculate_relevance_score(result, query_terms)
            result['relevance_score'] = score
        
        # Sort by combined score (similarity + relevance)
        return sorted(results, key=lambda x: (x.get('similarity', 0) * 0.7 + x.get('relevance_score', 0) * 0.3), reverse=True)
    
    def _calculate_relevance_score(self, result: Dict[str, Any], query_terms: set) -> float:
        """Calculate relevance score based on content analysis."""
        content = result.get('content', '').lower()
        metadata = result.get('metadata', {})
        
        score = 0.0
        
        # Legal keyword bonus
        legal_matches = sum(1 for keyword in self.legal_keywords if keyword in content)
        score += legal_matches * 0.1
        
        # Importance keyword bonus
        importance_matches = sum(1 for keyword in self.importance_keywords if keyword in content)
        score += importance_matches * 0.05
        
        # Query term frequency
        term_matches = sum(1 for term in query_terms if term in content)
        score += (term_matches / len(query_terms)) * 0.3 if query_terms else 0
        
        # Document type bonus
        doc_type = metadata.get('document_type', '')
        if doc_type == 'pdf':
            score += 0.1
        
        # Line number penalty (prefer earlier content)
        line_num = metadata.get('line_number', 1)
        if line_num > 100:
            score -= 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def filter_by_quality(self, results: List[Dict[str, Any]], min_similarity: float = 0.3) -> List[Dict[str, Any]]:
        """Filter results by quality thresholds."""
        return [r for r in results if r.get('similarity', 0) >= min_similarity and len(r.get('content', '')) > 20]

result_ranker = ResultRanker()
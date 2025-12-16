# OpenLead Intelligence - Intent Scorer

"""
Specific scoring module for Hiring and Buying Intent.
"""

from models.schemas import Company, HiringIntent
from utils.logger import get_logger

logger = get_logger(__name__)


class IntentScorer:
    """
    Calculates a specific 'Intent Score' based on signals.
    """
    
    def calculate(self, company: Company) -> float:
        """
        Returns a score 0-100 indicating hiring/buying intent.
        """
        score = 0.0
        if not company.enrichment:
            return score
            
        intent = company.enrichment.hiring_intent
        if intent:
            if intent.is_hiring:
                score += 50
            score += min(intent.recent_postings * 10, 50)
            
        return min(score, 100.0)

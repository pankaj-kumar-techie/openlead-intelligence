# OpenLead Intelligence - Company Size Enrichment

"""
Enrichment module to estimate company size and growth.
"""

from models.schemas import Company, CompanyEnrichment, CompanySize
from utils.logger import get_logger

logger = get_logger(__name__)


class CompanySizeEstimator:
    """
    Estimates company size based on data from various sources (social, website, etc).
    """
    
    def enrich_company(self, company: Company) -> Company:
        if not company.enrichment:
            company.enrichment = CompanyEnrichment()
            
        # If size is already known, skip
        if company.enrichment.company_size != CompanySize.UNKNOWN:
            return company
            
        # Logic to infer size
        # E.g., check 'open_positions' count -> simple heuristic
        intent = company.enrichment.hiring_intent
        if intent and intent.total_open_positions:
            if intent.total_open_positions > 50:
                company.enrichment.company_size = CompanySize.LARGE
            elif intent.total_open_positions > 10:
                company.enrichment.company_size = CompanySize.MEDIUM
            else:
                company.enrichment.company_size = CompanySize.SMALL
                
        return company

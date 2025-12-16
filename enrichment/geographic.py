# OpenLead Intelligence - Geographic Enrichment

"""
Enrichment module for geographic data normalization and timezones.
"""

from typing import Optional
from models.schemas import Company, GeographicInfo
from utils.logger import get_logger

logger = get_logger(__name__)


class GeographicEnricher:
    """
    Normalizes location data (City, Country) and adds region/timezone info.
    """
    
    def __init__(self):
        # In production, load a city/country database here
        pass
        
    def enrich_company(self, company: Company) -> Company:
        """Parse and normalize location strings."""
        if not company.enrichment or not company.enrichment.geographic_info:
            return company
            
        geo = company.enrichment.geographic_info
        
        # Example normalization logic
        if geo.city and not geo.country:
            # Try to infer country from city (simplified)
            pass
            
        # Example region mapping
        if geo.country in ['USA', 'United States', 'US']:
            geo.region = "North America"
        elif geo.country in ['UK', 'United Kingdom', 'Germany', 'France']:
            geo.region = "Europe"
            
        return company

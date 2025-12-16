# OpenLead Intelligence - Crunchbase Scraper

"""
Scraper for Crunchbase to collect company funding and investment data.
Supports both public page scraping and API usage.
"""

import time
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin

from collectors.base_scraper import BaseScraper
from models.schemas import (
    Company, CompanyEnrichment, FundingInfo, FundingStage,
    ScrapingResult, DataSource, CompanySize, GeographicInfo
)
from utils.logger import get_logger
from utils.helpers import clean_text, clean_company_name
from config import settings

logger = get_logger(__name__)


class CrunchbaseScraper(BaseScraper):
    """
    Scraper for Crunchbase.
    
    Warning: Crunchbase has strict anti-scraping protections.
    This module prioritizes using the API if a key is present,
    otherwise falls back to basic scraping techniques or advises user.
    """
    
    BASE_URL = "https://www.crunchbase.com"
    API_URL = "https://api.crunchbase.com/v3.1"
    
    def __init__(self, **kwargs):
        """Initialize Crunchbase scraper."""
        super().__init__(source=DataSource.CRUNCHBASE, **kwargs)
        self.api_key = settings.crunchbase_api_key
        
    def scrape(
        self,
        query: str = None,
        max_companies: int = 10
    ) -> ScrapingResult:
        """
        Collect data from Crunchbase.
        
        Args:
            query: Search term (company name or category)
            max_companies: Max limits
        
        Returns:
            ScrapingResult
        """
        result = ScrapingResult(source=self.source)
        start_time = time.time()
        
        try:
            if self.api_key:
                logger.info("Using Crunchbase API")
                companies = self._fetch_from_api(query, max_companies)
            else:
                logger.info("Crunchbase API key not found. Attempting limited public scraping.")
                # Note: Public scraping of CB is very difficult without Selenium/Puppeteer
                # and rotating proxies. This is a simplified educational implementation.
                companies = self._scrape_public_search(query, max_companies)
                
            for comp in companies:
                result.add_company(comp)
                
            result.execution_time = time.time() - start_time
            
        except Exception as e:
            logger.exception(f"Crunchbase collection failed: {e}")
            result.add_error(str(e))
            
        return result

    def _fetch_from_api(self, query: str, limit: int) -> List[Company]:
        """Fetch data using Crunchbase API."""
        companies = []
        # Mock implementation of API call structure
        # Real implementation requires a valid Enterprise API key structure which varies
        
        if not query:
            return []

        params = {
            "query": query,
            "user_key": self.api_key,
            "limit": limit
        }
        
        try:
            # Hypothetical endpoint
            url = f"{self.API_URL}/odm-organizations"
            response = self._make_request(url, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('items', [])
                
                for item in items:
                    props = item.get('properties', {})
                    companies.append(self._parse_api_data(props))
                    
        except Exception as e:
            logger.error(f"API request failed: {e}")
            
        return companies

    def _scrape_public_search(self, query: str, limit: int) -> List[Company]:
        """
        Scrape public search results.
        Note: CB heavily uses JS and anti-bot. This often requires Selenium.
        """
        # For robustness, we would use the SeleniumScraper here really.
        # Returning empty list with warning to avoid flagging IP.
        logger.warning(
            "Public scraping of Crunchbase requires advanced browser automation "
            "and proxy rotation. Please provide CRUNCHBASE_API_KEY in .env for reliable access."
        )
        return []

    def _parse_api_data(self, props: Dict[str, Any]) -> Company:
        """Convert API response to Company model."""
        name = props.get('name')
        
        # Funding Parsing
        total_funding_usd = props.get('total_funding_usd', 0)
        
        funding_info = FundingInfo(
            total_funding=total_funding_usd,
            stage=FundingStage.UNKNOWN # Logic to map 'role_company' etc to stage
        )
        
        geo_info = GeographicInfo(
            city=props.get('city_name'),
            region=props.get('region_name'),
            country=props.get('country_code')
        )
        
        enrichment = CompanyEnrichment(
            funding_info=funding_info,
            geographic_info=geo_info,
            description=clean_text(props.get('short_description', ''))
        )
        
        return Company(
            name=clean_company_name(name),
            domain=props.get('domain'),
            website=props.get('homepage_url'),
            description=clean_text(props.get('short_description', '')),
            source=self.source,
            enrichment=enrichment
        )

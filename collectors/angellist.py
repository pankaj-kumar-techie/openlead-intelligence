# OpenLead Intelligence - AngelList/Wellfound Scraper

"""
Scraper for AngelList (now Wellfound) to collect startup data.
Extracts funding information, team size, job postings, and company details.
"""

import time
from typing import Optional, List
from urllib.parse import urljoin

from collectors.base_scraper import BaseScraper
from models.schemas import (
    Company, CompanyEnrichment, FundingInfo, HiringIntent,
    GeographicInfo, ScrapingResult, DataSource, CompanySize,
    FundingStage
)
from utils.logger import get_logger
from utils.helpers import extract_domain, clean_text, clean_company_name

logger = get_logger(__name__)


class AngelListScraper(BaseScraper):
    """
    Scraper for AngelList/Wellfound.
    
    Note: AngelList has transitioned to Wellfound and has an API.
    This scraper is for educational purposes. Use official API when possible.
    """
    
    BASE_URL = "https://wellfound.com"
    
    def __init__(self, **kwargs):
        """Initialize AngelList scraper."""
        super().__init__(source=DataSource.ANGELLIST, **kwargs)
    
    def scrape(
        self,
        role: Optional[str] = None,
        location: Optional[str] = None,
        max_companies: int = 50
    ) -> ScrapingResult:
        """
        Scrape AngelList for startup data.
        
        Args:
            role: Filter by role/job type
            location: Filter by location
            max_companies: Maximum number of companies to scrape
        
        Returns:
            ScrapingResult with scraped companies
        """
        start_time = time.time()
        result = ScrapingResult(source=self.source)
        
        logger.info(f"Starting AngelList scrape (max={max_companies})")
        
        try:
            # Build search URL
            search_url = f"{self.BASE_URL}/companies"
            params = []
            if role:
                params.append(f"role={role}")
            if location:
                params.append(f"location={location}")
            
            if params:
                search_url += "?" + "&".join(params)
            
            logger.info(f"Scraping AngelList: {search_url}")
            
            soup = self.get_soup(search_url)
            if not soup:
                result.add_error("Failed to fetch AngelList search page")
                return result
            
            # Parse company listings
            companies_data = self._parse_company_listings(soup)
            
            for company_data in companies_data[:max_companies]:
                company = self.parse_company(company_data)
                if company:
                    result.add_company(company)
            
            result.execution_time = time.time() - start_time
            logger.info(
                f"AngelList scrape completed: {result.total_scraped} companies "
                f"in {result.execution_time:.2f}s"
            )
            
        except Exception as e:
            logger.exception(f"Error during AngelList scraping: {e}")
            result.add_error(str(e))
        
        return result
    
    def _parse_company_listings(self, soup) -> List[dict]:
        """Parse company listings from search results."""
        companies = []
        
        try:
            # Example selectors (adjust based on actual structure)
            company_cards = soup.find_all('div', class_=lambda x: x and 'company' in str(x).lower())
            
            for card in company_cards:
                try:
                    company_data = {}
                    
                    # Company name
                    name_elem = card.find('h2') or card.find('a', class_=lambda x: x and 'name' in str(x).lower())
                    if name_elem:
                        company_data['name'] = clean_text(name_elem.get_text())
                    
                    # Description
                    desc_elem = card.find('p') or card.find('div', class_=lambda x: x and 'description' in str(x).lower())
                    if desc_elem:
                        company_data['description'] = clean_text(desc_elem.get_text())
                    
                    # Company URL
                    link_elem = card.find('a', href=True)
                    if link_elem:
                        company_data['url'] = urljoin(self.BASE_URL, link_elem['href'])
                    
                    # Location
                    location_elem = card.find('span', class_=lambda x: x and 'location' in str(x).lower())
                    if location_elem:
                        company_data['location'] = clean_text(location_elem.get_text())
                    
                    # Company size
                    size_elem = card.find('span', class_=lambda x: x and 'size' in str(x).lower())
                    if size_elem:
                        company_data['size'] = clean_text(size_elem.get_text())
                    
                    # Job count
                    jobs_elem = card.find('span', class_=lambda x: x and 'job' in str(x).lower())
                    if jobs_elem:
                        jobs_text = jobs_elem.get_text()
                        try:
                            company_data['job_count'] = int(''.join(filter(str.isdigit, jobs_text)))
                        except ValueError:
                            company_data['job_count'] = 0
                    
                    if company_data.get('name'):
                        companies.append(company_data)
                
                except Exception as e:
                    logger.warning(f"Error parsing company card: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing company listings: {e}")
        
        return companies
    
    def parse_company(self, data: dict) -> Optional[Company]:
        """Parse company from AngelList data."""
        try:
            name = data.get('name')
            if not name:
                return None
            
            company_name = clean_company_name(name)
            
            # Parse location
            location_text = data.get('location', '')
            country = None
            city = None
            if location_text:
                parts = location_text.split(',')
                if len(parts) >= 2:
                    city = parts[0].strip()
                    country = parts[-1].strip()
                elif len(parts) == 1:
                    city = parts[0].strip()
            
            # Parse company size
            size_text = data.get('size', '')
            company_size = CompanySize.UNKNOWN
            employee_count = None
            
            if size_text:
                if '1-10' in size_text:
                    company_size = CompanySize.STARTUP
                    employee_count = 5
                elif '11-50' in size_text:
                    company_size = CompanySize.SMALL
                    employee_count = 30
                elif '51-200' in size_text:
                    company_size = CompanySize.MEDIUM
                    employee_count = 125
                elif '201-1000' in size_text:
                    company_size = CompanySize.LARGE
                    employee_count = 600
                elif '1000+' in size_text:
                    company_size = CompanySize.ENTERPRISE
                    employee_count = 2000
            
            # Create enrichment
            enrichment = CompanyEnrichment(
                company_size=company_size,
                employee_count=employee_count,
                geographic_info=GeographicInfo(
                    country=country,
                    city=city
                ),
                hiring_intent=HiringIntent(
                    total_open_positions=data.get('job_count', 0),
                    is_hiring=data.get('job_count', 0) > 0
                ),
                tags=['angellist', 'startup']
            )
            
            company = Company(
                name=company_name,
                description=data.get('description'),
                source=self.source,
                source_url=data.get('url'),
                enrichment=enrichment
            )
            
            logger.debug(f"Parsed company: {company_name}")
            return company
            
        except Exception as e:
            logger.error(f"Error parsing company from data: {e}")
            return None


if __name__ == "__main__":
    print("AngelList Scraper")
    print("Example usage:")
    print("  scraper = AngelListScraper()")
    print("  result = scraper.scrape(location='San Francisco', max_companies=20)")

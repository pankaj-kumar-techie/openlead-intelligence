# OpenLead Intelligence - Clutch.co Scraper

"""
Scraper for Clutch.co to collect B2B service provider data.
Extracts reviews, ratings, services, and company details.
"""

import time
from typing import Optional, List
from urllib.parse import urljoin

from collectors.base_scraper import BaseScraper
from models.schemas import (
    Company, CompanyEnrichment, ScrapingResult, 
    DataSource, CompanySize, GeographicInfo
)
from utils.logger import get_logger
from utils.helpers import clean_text, clean_company_name

logger = get_logger(__name__)


class ClutchScraper(BaseScraper):
    """
    Scraper for Clutch.co B2B directory.
    """
    
    BASE_URL = "https://clutch.co"
    
    def __init__(self, **kwargs):
        """Initialize Clutch scraper."""
        super().__init__(source=DataSource.CLUTCH, **kwargs)
    
    def scrape(
        self, 
        category: str = "web-developers", 
        max_pages: int = 1
    ) -> ScrapingResult:
        """
        Scrape Clutch companies by category.
        
        Args:
            category: Clutch category slug (e.g., 'web-developers', 'app-developers')
            max_pages: Number of pagination pages to scrape
        
        Returns:
            ScrapingResult
        """
        start_time = time.time()
        result = ScrapingResult(source=self.source)
        
        try:
            current_page = 1
            
            while current_page <= max_pages:
                url = f"{self.BASE_URL}/{category}?page={current_page}"
                logger.info(f"Scraping Clutch page {current_page}: {url}")
                
                soup = self.get_soup(url)
                if not soup:
                    result.add_error(f"Failed to fetch page {current_page}")
                    break
                
                companies_list = self._parse_listings(soup)
                
                if not companies_list:
                    logger.warning(f"No companies found on page {current_page}")
                    break
                    
                for company_data in companies_list:
                    company = self.parse_company(company_data)
                    if company:
                        result.add_company(company)
                
                current_page += 1
                # Politeness delay
                time.sleep(self.rate_limit_delay)
            
            result.execution_time = time.time() - start_time
            logger.info(f"Clutch scrape completed: {result.total_scraped} companies")
            
        except Exception as e:
            logger.exception(f"Error scraping Clutch: {e}")
            result.add_error(str(e))
            
        return result

    def _parse_listings(self, soup) -> List[dict]:
        """Parse company listings from a category page."""
        companies = []
        try:
            # Clutch HTML structure varies, standard list items usually have class 'provider-row'
            rows = soup.find_all('li', class_='provider-row')
            
            for row in rows:
                try:
                    data = {}
                    
                    # Name
                    name_elem = row.find('h3', class_='company_info')
                    if name_elem:
                        data['name'] = clean_text(name_elem.get_text())
                    
                    # Website (encoded usually, scrape the profile link)
                    profile_link = row.find('a', class_='website-link')
                    if profile_link and profile_link.get('href'):
                        data['url'] = profile_link['href'] # This assumes direct link or redirect
                        
                    # Tagline
                    tagline = row.find('p', class_='tagline')
                    if tagline:
                        data['description'] = clean_text(tagline.get_text())
                        
                    # Location
                    loc_elem = row.find('span', class_='locality')
                    if loc_elem:
                        data['location'] = clean_text(loc_elem.get_text())
                        
                    # Rating
                    rating_elem = row.find('span', class_='rating')
                    if rating_elem:
                        try:
                            data['rating'] = float(rating_elem.get_text())
                        except ValueError:
                            pass
                            
                    # Hourly Rate
                    rate_elem = row.find('div', class_='hourly-rate')
                    if rate_elem:
                        data['hourly_rate'] = clean_text(rate_elem.get_text())
                        
                    # Employee Count (often presented as range, e.g., '10 - 49')
                    emp_elem = row.find('div', class_='employees')
                    if emp_elem:
                        data['employees'] = clean_text(emp_elem.get_text())

                    if data.get('name'):
                        companies.append(data)
                        
                except Exception as e:
                    logger.debug(f"Error parsing clutch row: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing clutch listings: {e}")
            
        return companies

    def parse_company(self, data: dict) -> Optional[Company]:
        """Convert raw dictionary to Company model."""
        try:
            name = data.get('name')
            if not name:
                return None
            
            # Map employee range to CompanySize
            size_str = data.get('employees', '')
            size_enum = CompanySize.UNKNOWN
            if '10,000+' in size_str:
                size_enum = CompanySize.ENTERPRISE
            elif '1,000 - 9,999' in size_str:
                size_enum = CompanySize.ENTERPRISE
            elif '250 - 999' in size_str:
                size_enum = CompanySize.LARGE
            elif '50 - 249' in size_str:
                size_enum = CompanySize.MEDIUM
            elif '10 - 49' in size_str:
                size_enum = CompanySize.SMALL
            elif '2 - 9' in size_str:
                size_enum = CompanySize.STARTUP
            
            # Enrichment
            enrichment = CompanyEnrichment(
                company_size=size_enum,
                geographic_info=GeographicInfo(
                    city=data.get('location')  # Clutch typically gives "City, Country"
                ),
                tags=['agency', 'b2b-service']
            )
            
            # Extra data
            extra = {
                'rating': data.get('rating'),
                'hourly_rate': data.get('hourly_rate')
            }
            
            company = Company(
                name=clean_company_name(name),
                description=data.get('description'),
                source=self.source,
                source_url=data.get('url'), # Usually points to Clutch profile
                enrichment=enrichment,
                extra_data=extra
            )
            return company
            
        except Exception as e:
            logger.error(f"Error creating Company object for {data.get('name')}: {e}")
            return None

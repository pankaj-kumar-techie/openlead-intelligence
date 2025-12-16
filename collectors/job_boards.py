# OpenLead Intelligence - Hacker News Scraper

"""
Reliable scraper for Hacker News to collect job postings and company data.
Targets 'Who is Hiring' threads and 'Show HN'.
"""

import time
import re
from typing import List, Optional

from collectors.base_scraper import BaseScraper
from models.schemas import (
    Company, CompanyEnrichment, HiringIntent,
    ScrapingResult, DataSource, CompanySize, TechStack
)
from utils.logger import get_logger
from utils.helpers import clean_text, extract_domain

logger = get_logger(__name__)

class HackerNewsScraper(BaseScraper):
    """
    Scraper for Hacker News (news.ycombinator.com).
    API is available but this demonstrates resilient scraping.
    """
    
    BASE_URL = "https://news.ycombinator.com"
    
    def __init__(self, **kwargs):
        super().__init__(source=DataSource.JOB_BOARDS, **kwargs)
        
    def scrape(
        self,
        keywords: str = None, # Unused, keeping signature compatible
        location: str = None,
        max_pages: int = 1
    ) -> ScrapingResult:
        """
        Scrape 'Show HN' for new products/companies.
        """
        result = ScrapingResult(source=self.source)
        start_time = time.time()
        
        try:
            # We'll scrape "Show HN" (https://news.ycombinator.com/show)
            url = f"{self.BASE_URL}/show"
            logger.info(f"Scraping Hacker News: {url}")
            
            soup = self.get_soup(url)
            if not soup:
                result.add_error("Failed to fetch Hacker News")
                return result
                
            items = soup.find_all('tr', class_='athing')
            
            for item in items[:20]: # Limit for demo
                company = self._parse_item(item)
                if company:
                    result.add_company(company)
                    
            result.execution_time = time.time() - start_time
            logger.info(f"Hacker News scrape completed: {result.total_scraped} companies")
            
        except Exception as e:
            logger.exception(f"Error scraping HN: {e}")
            result.add_error(str(e))
            
        return result

    def parse_company(self, item) -> Optional[Company]:
        try:
            # Title line
            title_line = item.find('span', class_='titleline')
            if not title_line:
                logger.debug("Skipping: no titleline")
                return None
                
            link = title_line.find('a')
            if not link:
                logger.debug("Skipping: no link")
                return None
                
            title_text = clean_text(link.get_text())
            if not title_text:
                # Fallback: get text from the span
                title_text = clean_text(title_line.get_text())
            
            url = link['href']
            
            # Filter out internal HN links
            if url.startswith('item?id='):
                logger.debug(f"Skipping internal link: {url}")
                return None
                
            logger.debug(f"Processing: {title_text}")
            
            # Clean title "Show HN: My Company - Description"
            company_name = title_text
            description = ""
            
            # Case insensitive check
            if "show hn" in title_text.lower():
                # Try to split by colon first
                if ":" in title_text:
                    parts = title_text.split(":", 1)
                    # Use the part after colon
                    rest = parts[1].strip()
                    # Try to split by dash for description
                    if "-" in rest:
                        name_parts = rest.split("-", 1)
                        company_name = name_parts[0].strip()
                        description = name_parts[1].strip()
                    else:
                        company_name = rest
                else:
                    # just remove Show HN
                    company_name = re.sub(r'show hn', '', title_text, flags=re.IGNORECASE).strip()
            
            # Try to enrich tech stack via simple keyword matching on description
            enrichment = CompanyEnrichment(
                tags=['hacker-news', 'show-hn'],
                hiring_intent=HiringIntent(is_hiring=True) # Startups usually hiring
            )
            
            return Company(
                name=company_name,
                domain=extract_domain(url),
                website=url,
                description=description,
                source=self.source,
                source_url=f"{self.BASE_URL}/item?id={item['id']}",
                enrichment=enrichment
            )
            
        except Exception as e:
            # logger.debug(f"Row parse error: {e}")
            return None

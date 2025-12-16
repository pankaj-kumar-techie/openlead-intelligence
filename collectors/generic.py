# OpenLead Intelligence - Generic URL Scraper

"""
A generic scraper that attempts to extract company information from ANY given URL.
Useful for ad-hoc testing and scraping arbitrary lists of leads.
"""

import time
from typing import Optional, List
from urllib.parse import urljoin

from collectors.base_scraper import BaseScraper
from models.schemas import (
    Company, CompanyEnrichment, ScrapingResult, DataSource
)
from utils.logger import get_logger
from utils.helpers import clean_text, extract_domain

logger = get_logger(__name__)

class GenericScraper(BaseScraper):
    """
    Scrapes a user-provided URL and tries to extract listing items.
    Best used on pages that list companies (directories, top 10 lists, etc.).
    """
    
    def __init__(self, **kwargs):
        super().__init__(source=DataSource.OTHER, **kwargs)
        
    def scrape(self, url: str) -> ScrapingResult:
        """
        Scrape a single specific URL.
        """
        result = ScrapingResult(source=self.source)
        start_time = time.time()
        
        try:
            logger.info(f"Generic scraping starting for: {url}")
            soup = self.get_soup(url)
            
            if not soup:
                result.add_error(f"Could not load {url}")
                return result
                
            # Heuristic: Find repetitive elements that might be listings
            # We look for common patterns: <h2> or <h3> with links inside
            
            candidates = []
            
            # Strategy 1: Look for Headings with Links (Common in directories)
            for tag in ['h2', 'h3', 'h4']:
                headers = soup.find_all(tag)
                for header in headers:
                    link = header.find('a')
                    if link and link.get('href'):
                        name = clean_text(header.get_text())
                        if len(name) > 2 and len(name) < 50:
                            candidates.append({
                                'name': name,
                                'url': urljoin(url, link.get('href')),
                                'desc_elem': header.find_next('p')
                            })
            
            logger.info(f"Found {len(candidates)} potential leads using Header strategy")
            
            if not candidates:
                # Strategy 2: Look for list items with classes indicating "item" or "card"
                possible_items = soup.find_all(lambda tag: tag.name in ['div', 'li'] and 
                                             tag.get('class') and 
                                             any(x in str(tag.get('class')) for x in ['item', 'card', 'row', 'listing']))
                
                for item in possible_items[:20]: # Limit to avoid junk
                     # Try to find a title/link inside
                    link = item.find('a')
                    if link and link.get('href'):
                         text = clean_text(link.get_text())
                         if text:
                             candidates.append({
                                 'name': text,
                                 'url': urljoin(url, link.get('href')),
                                 'desc_elem': item.find('p')
                             })

            # Strategy 3: Table Rows (Common in old sites like HN)
            if not candidates:
                logger.info("Strategies 1-2 failed. Trying Table Rows...")
                rows = soup.find_all('tr')
                for row in rows[:50]:
                    # Heuristic: Row with a link that isn't tiny
                    link = row.find('a')
                    if link and link.get('href'):
                         text = clean_text(link.get_text())
                         if len(text) > 5: # Basic filter
                             candidates.append({
                                 'name': text,
                                 'url': urljoin(url, link.get('href')),
                                 'desc_elem': None
                             })
            
            # Process candidates into Companies
            logger.info(f"Total candidates found: {len(candidates)}")
            for cand in candidates:
                # Avoid duplicates in this run
                if any(c.name == cand['name'] for c in result.companies):
                    continue
                    
                description = None
                if cand.get('desc_elem'):
                    description = clean_text(cand['desc_elem'].get_text())
                
                company = Company(
                    name=cand['name'],
                    website=cand['url'],
                    domain=extract_domain(cand['url']),
                    description=description,
                    source=DataSource.MANUAL,
                    source_url=url,
                    enrichment=CompanyEnrichment(tags=['generic-scrape'])
                )
                result.add_company(company)
                
            result.execution_time = time.time() - start_time
            logger.info(f"Generic scrape finished. Scraped {result.total_scraped} items.")
            
        except Exception as e:
            logger.exception(f"Error in generic scraper: {e}")
            result.add_error(str(e))
            
        return result

    def parse_company(self, data):
        # Not used in this implementation as logic is inside scrape()
        pass

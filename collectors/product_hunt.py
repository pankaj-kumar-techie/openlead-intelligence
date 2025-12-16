# OpenLead Intelligence - Product Hunt Scraper

"""
Scraper for Product Hunt to collect newly launched products and companies.
Extracts company information, product details, and launch metrics.
"""

import time
from typing import Optional, List
from datetime import datetime, timedelta

from collectors.base_scraper import BaseScraper
from models.schemas import (
    Company, CompanyEnrichment, ScrapingResult,
    DataSource, CompanySize, TechStack
)
from utils.logger import get_logger
from utils.helpers import extract_domain, clean_text, clean_company_name

logger = get_logger(__name__)


class ProductHuntScraper(BaseScraper):
    """
    Scraper for Product Hunt.
    
    Note: Product Hunt has an official API. This scraper demonstrates
    web scraping approach, but using the API is recommended for production.
    """
    
    BASE_URL = "https://www.producthunt.com"
    
    def __init__(self, **kwargs):
        """Initialize Product Hunt scraper."""
        super().__init__(source=DataSource.PRODUCT_HUNT, **kwargs)
    
    def scrape(
        self,
        days_back: int = 7,
        max_products: int = 50,
        category: Optional[str] = None
    ) -> ScrapingResult:
        """
        Scrape Product Hunt for recent product launches.
        
        Args:
            days_back: Number of days to look back
            max_products: Maximum number of products to scrape
            category: Filter by category (optional)
        
        Returns:
            ScrapingResult with scraped companies
        """
        start_time = time.time()
        result = ScrapingResult(source=self.source)
        
        logger.info(f"Starting Product Hunt scrape (days_back={days_back}, max={max_products})")
        
        try:
            # Scrape daily pages
            products_scraped = 0
            current_date = datetime.now()
            
            for day_offset in range(days_back):
                if products_scraped >= max_products:
                    break
                
                target_date = current_date - timedelta(days=day_offset)
                date_str = target_date.strftime("%Y/%m/%d")
                
                url = f"{self.BASE_URL}/posts/{date_str}"
                logger.info(f"Scraping Product Hunt for date: {date_str}")
                
                soup = self.get_soup(url)
                if not soup:
                    result.add_warning(f"Failed to fetch page for {date_str}")
                    continue
                
                # Parse products from the page
                # Note: This is a simplified example. Actual selectors may vary.
                products = self._parse_products_page(soup, target_date)
                
                for product_data in products:
                    if products_scraped >= max_products:
                        break
                    
                    company = self.parse_company(product_data)
                    if company:
                        result.add_company(company)
                        products_scraped += 1
                
                logger.info(f"Scraped {len(products)} products from {date_str}")
            
            result.execution_time = time.time() - start_time
            logger.info(
                f"Product Hunt scrape completed: {result.total_scraped} companies "
                f"in {result.execution_time:.2f}s"
            )
            
        except Exception as e:
            logger.exception(f"Error during Product Hunt scraping: {e}")
            result.add_error(str(e))
        
        return result
    
    def _parse_products_page(self, soup, date) -> List[dict]:
        """
        Parse products from a daily page.
        
        Args:
            soup: BeautifulSoup object
            date: Date of the page
        
        Returns:
            List of product data dictionaries
        """
        products = []
        
        try:
            # Example selectors (may need adjustment based on actual HTML structure)
            # Product Hunt's structure changes frequently, so this is illustrative
            
            product_cards = soup.find_all('div', {'data-test': 'post-item'}) or \
                           soup.find_all('article') or \
                           soup.find_all('div', class_=lambda x: x and 'post' in x.lower())
            
            for card in product_cards[:20]:  # Limit per page
                try:
                    product_data = {
                        'launch_date': date,
                        'card': card
                    }
                    
                    # Extract product name
                    name_elem = card.find('h3') or card.find('a', class_=lambda x: x and 'name' in str(x).lower())
                    if name_elem:
                        product_data['name'] = clean_text(name_elem.get_text())
                    
                    # Extract tagline/description
                    desc_elem = card.find('p') or card.find('div', class_=lambda x: x and 'tagline' in str(x).lower())
                    if desc_elem:
                        product_data['description'] = clean_text(desc_elem.get_text())
                    
                    # Extract link
                    link_elem = card.find('a', href=True)
                    if link_elem:
                        product_data['product_url'] = self.BASE_URL + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                    
                    # Extract upvotes (popularity metric)
                    upvote_elem = card.find('button', class_=lambda x: x and 'vote' in str(x).lower())
                    if upvote_elem:
                        upvote_text = upvote_elem.get_text()
                        try:
                            product_data['upvotes'] = int(''.join(filter(str.isdigit, upvote_text)))
                        except ValueError:
                            product_data['upvotes'] = 0
                    
                    if product_data.get('name'):
                        products.append(product_data)
                
                except Exception as e:
                    logger.warning(f"Error parsing product card: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing products page: {e}")
        
        return products
    
    def parse_company(self, data: dict) -> Optional[Company]:
        """
        Parse company from product data.
        
        Args:
            data: Product data dictionary
        
        Returns:
            Company object or None
        """
        try:
            name = data.get('name')
            if not name:
                return None
            
            # Clean company name
            company_name = clean_company_name(name)
            
            # Try to extract website/domain
            website = None
            domain = None
            
            # If we have a product URL, we could visit it to get the actual website
            # For now, we'll use the Product Hunt URL
            product_url = data.get('product_url')
            
            # Create company object
            company = Company(
                name=company_name,
                domain=domain,
                website=website,
                description=data.get('description'),
                source=self.source,
                source_url=product_url,
                enrichment=CompanyEnrichment(
                    company_size=CompanySize.STARTUP,  # Assumption for PH launches
                    tags=['product-hunt', 'new-launch'],
                ),
                extra_data={
                    'launch_date': data.get('launch_date').isoformat() if data.get('launch_date') else None,
                    'upvotes': data.get('upvotes', 0),
                    'product_name': name,
                }
            )
            
            logger.debug(f"Parsed company: {company_name}")
            return company
            
        except Exception as e:
            logger.error(f"Error parsing company from data: {e}")
            return None
    
    def scrape_product_details(self, product_url: str) -> Optional[dict]:
        """
        Scrape detailed information from a product page.
        
        Args:
            product_url: URL of the product page
        
        Returns:
            Dictionary with product details
        """
        try:
            soup = self.get_soup(product_url)
            if not soup:
                return None
            
            details = {}
            
            # Extract website link
            website_link = soup.find('a', {'data-test': 'website-link'}) or \
                          soup.find('a', text=lambda x: x and 'website' in str(x).lower())
            if website_link and website_link.get('href'):
                details['website'] = website_link['href']
                details['domain'] = extract_domain(website_link['href'])
            
            # Extract maker information
            makers = soup.find_all('a', {'data-test': 'maker-link'})
            if makers:
                details['makers'] = [clean_text(m.get_text()) for m in makers]
            
            # Extract topics/tags
            topics = soup.find_all('a', {'data-test': 'topic-link'})
            if topics:
                details['topics'] = [clean_text(t.get_text()) for t in topics]
            
            return details
            
        except Exception as e:
            logger.error(f"Error scraping product details from {product_url}: {e}")
            return None


if __name__ == "__main__":
    # Test scraper
    scraper = ProductHuntScraper()
    
    print("Testing Product Hunt Scraper...")
    print("Note: This requires internet connection and Product Hunt to be accessible.")
    print("\nExample usage:")
    print("  scraper = ProductHuntScraper()")
    print("  result = scraper.scrape(days_back=3, max_products=10)")
    print("  print(f'Scraped {result.total_scraped} companies')")
    
    # Uncomment to test (requires internet):
    # result = scraper.scrape(days_back=1, max_products=5)
    # print(f"\nScraped {result.total_scraped} companies")
    # for company in result.companies[:3]:
    #     print(f"- {company.name}: {company.description}")

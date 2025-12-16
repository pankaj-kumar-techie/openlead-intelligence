# OpenLead Intelligence - Tech Stack Detection

"""
Technology stack detection from website HTML, headers, and meta tags.
Identifies programming languages, frameworks, databases, and tools.
"""

import re
import requests
from typing import Optional, Set, List
from bs4 import BeautifulSoup

from models.schemas import TechStack, Company
from utils.logger import get_logger
from utils.helpers import normalize_url

logger = get_logger(__name__)


class TechStackDetector:
    """
    Detect technology stack from website.
    
    Uses pattern matching on HTML, headers, scripts, and meta tags
    to identify technologies similar to BuiltWith or Wappalyzer.
    """
    
    # Technology patterns (simplified version)
    PATTERNS = {
        # JavaScript Frameworks
        'react': [
            r'react\.js',
            r'react-dom',
            r'_react',
            r'data-reactroot',
            r'data-reactid'
        ],
        'vue': [
            r'vue\.js',
            r'vue\.min\.js',
            r'data-v-',
            r'__vue__'
        ],
        'angular': [
            r'angular\.js',
            r'ng-app',
            r'ng-controller',
            r'@angular'
        ],
        'jquery': [
            r'jquery\.js',
            r'jquery\.min\.js',
            r'jquery-[0-9]'
        ],
        'svelte': [
            r'svelte',
            r'__svelte'
        ],
        
        # Backend Frameworks
        'django': [
            r'csrfmiddlewaretoken',
            r'django',
            r'__admin'
        ],
        'flask': [
            r'flask',
            r'werkzeug'
        ],
        'express': [
            r'express',
            r'x-powered-by.*express'
        ],
        'rails': [
            r'rails',
            r'ruby on rails',
            r'csrf-param'
        ],
        'laravel': [
            r'laravel',
            r'laravel_session'
        ],
        'spring': [
            r'spring',
            r'jsessionid'
        ],
        
        # CMS
        'wordpress': [
            r'wp-content',
            r'wp-includes',
            r'wordpress'
        ],
        'shopify': [
            r'shopify',
            r'cdn\.shopify\.com'
        ],
        'wix': [
            r'wix\.com',
            r'wixstatic'
        ],
        'squarespace': [
            r'squarespace',
            r'sqsp'
        ],
        
        # Analytics
        'google-analytics': [
            r'google-analytics\.com',
            r'ga\.js',
            r'gtag'
        ],
        'mixpanel': [
            r'mixpanel',
            r'cdn\.mxpnl\.com'
        ],
        'segment': [
            r'segment\.com',
            r'analytics\.js'
        ],
        'hotjar': [
            r'hotjar',
            r'static\.hotjar\.com'
        ],
        
        # Cloud Providers
        'aws': [
            r'amazonaws\.com',
            r'cloudfront\.net',
            r's3\.amazonaws'
        ],
        'google-cloud': [
            r'googleapis\.com',
            r'gstatic\.com'
        ],
        'azure': [
            r'azure',
            r'windows\.net'
        ],
        'cloudflare': [
            r'cloudflare',
            r'cf-ray'
        ],
        
        # Databases (from meta tags or comments)
        'mongodb': [r'mongodb', r'mongo'],
        'postgresql': [r'postgresql', r'postgres'],
        'mysql': [r'mysql'],
        'redis': [r'redis'],
        
        # Build Tools
        'webpack': [r'webpack'],
        'vite': [r'vite'],
        'parcel': [r'parcel'],
        
        # CSS Frameworks
        'bootstrap': [r'bootstrap'],
        'tailwind': [r'tailwind'],
        'material-ui': [r'material-ui', r'mui'],
    }
    
    # Category mapping
    CATEGORIES = {
        'languages': [],
        'frameworks': ['react', 'vue', 'angular', 'django', 'flask', 'express', 'rails', 'laravel', 'spring', 'svelte'],
        'databases': ['mongodb', 'postgresql', 'mysql', 'redis'],
        'cloud_providers': ['aws', 'google-cloud', 'azure', 'cloudflare'],
        'tools': ['webpack', 'vite', 'parcel', 'jquery'],
        'analytics': ['google-analytics', 'mixpanel', 'segment', 'hotjar'],
        'marketing': ['wordpress', 'shopify', 'wix', 'squarespace', 'bootstrap', 'tailwind', 'material-ui'],
    }
    
    def __init__(self, timeout: int = 10):
        """
        Initialize tech stack detector.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        logger.info("Initialized TechStackDetector")
    
    def detect(self, company: Company) -> Optional[TechStack]:
        """
        Detect technology stack for a company.
        
        Args:
            company: Company object with website
        
        Returns:
            TechStack object or None
        """
        if not company.website and not company.domain:
            logger.warning(f"No website/domain for company: {company.name}")
            return None
        
        url = str(company.website) if company.website else f"https://{company.domain}"
        url = normalize_url(url)
        
        logger.info(f"Detecting tech stack for: {url}")
        
        try:
            # Fetch website
            response = requests.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Detect technologies
            detected = self._detect_from_html(soup, response)
            
            # Categorize technologies
            tech_stack = self._categorize_technologies(detected)
            
            logger.info(f"Detected {len(detected)} technologies for {company.name}")
            return tech_stack
            
        except Exception as e:
            logger.error(f"Error detecting tech stack for {url}: {e}")
            return None
    
    def _detect_from_html(self, soup: BeautifulSoup, response: requests.Response) -> Set[str]:
        """
        Detect technologies from HTML and headers.
        
        Args:
            soup: BeautifulSoup object
            response: Response object
        
        Returns:
            Set of detected technology names
        """
        detected = set()
        
        # Get full HTML as text
        html_text = str(soup).lower()
        
        # Get headers
        headers_text = str(response.headers).lower()
        
        # Check each technology pattern
        for tech_name, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html_text, re.IGNORECASE) or \
                   re.search(pattern, headers_text, re.IGNORECASE):
                    detected.add(tech_name)
                    break
        
        # Check meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            content = str(meta.get('content', '')).lower()
            name = str(meta.get('name', '')).lower()
            
            for tech_name, patterns in self.PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, content) or re.search(pattern, name):
                        detected.add(tech_name)
        
        # Check script sources
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            src = script['src'].lower()
            for tech_name, patterns in self.PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, src):
                        detected.add(tech_name)
        
        return detected
    
    def _categorize_technologies(self, detected: Set[str]) -> TechStack:
        """
        Categorize detected technologies into TechStack model.
        
        Args:
            detected: Set of detected technology names
        
        Returns:
            TechStack object
        """
        tech_stack = TechStack()
        
        for tech in detected:
            # Find category
            for category, techs in self.CATEGORIES.items():
                if tech in techs:
                    # Add to appropriate list
                    tech_list = getattr(tech_stack, category)
                    tech_list.append(tech.replace('-', ' ').title())
                    break
        
        return tech_stack
    
    def enrich_company(self, company: Company) -> Company:
        """
        Enrich company with tech stack data.
        
        Args:
            company: Company object
        
        Returns:
            Enriched company object
        """
        tech_stack = self.detect(company)
        
        if tech_stack:
            if not company.enrichment:
                from models.schemas import CompanyEnrichment
                company.enrichment = CompanyEnrichment()
            
            company.enrichment.tech_stack = tech_stack
        
        return company


if __name__ == "__main__":
    from models.schemas import Company, DataSource
    
    # Test tech stack detection
    detector = TechStackDetector()
    
    # Example company
    test_company = Company(
        name="Example Corp",
        website="https://www.example.com",
        source=DataSource.MANUAL
    )
    
    print("Testing Tech Stack Detector...")
    print(f"Company: {test_company.name}")
    print(f"Website: {test_company.website}")
    
    # Uncomment to test (requires internet):
    # enriched = detector.enrich_company(test_company)
    # if enriched.enrichment and enriched.enrichment.tech_stack:
    #     print("\nDetected Technologies:")
    #     print(f"Frameworks: {enriched.enrichment.tech_stack.frameworks}")
    #     print(f"Tools: {enriched.enrichment.tech_stack.tools}")
    #     print(f"Analytics: {enriched.enrichment.tech_stack.analytics}")

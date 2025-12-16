# OpenLead Intelligence - Base Scraper

"""
Abstract base class for all scrapers with built-in retry logic,
rate limiting, error handling, and robots.txt compliance.
"""

import time
import requests
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from config import settings
from utils.logger import get_logger
from utils.helpers import retry_on_exception, check_robots_txt, validate_url
from models.schemas import Company, ScrapingResult, DataSource

logger = get_logger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all web scrapers.
    
    Provides common functionality:
    - Session management with custom headers
    - Retry logic with exponential backoff
    - Rate limiting and politeness delays
    - robots.txt compliance checking
    - Error handling and logging
    - User-agent rotation
    """
    
    def __init__(
        self,
        source: DataSource = DataSource.OTHER,
        respect_robots: bool = None,
        rate_limit_delay: float = None,
        max_retries: int = None,
        timeout: int = None
    ):
        """
        Initialize base scraper.
        
        Args:
            source: Data source identifier
            respect_robots: Whether to respect robots.txt (default from config)
            rate_limit_delay: Delay between requests in seconds (default from config)
            max_retries: Maximum retry attempts (default from config)
            timeout: Request timeout in seconds (default from config)
        """
        self.source = source
        self.respect_robots = respect_robots if respect_robots is not None else settings.respect_robots_txt
        self.rate_limit_delay = rate_limit_delay if rate_limit_delay is not None else settings.rate_limit_delay
        self.max_retries = max_retries if max_retries is not None else settings.max_retries
        self.timeout = timeout if timeout is not None else settings.request_timeout
        
        # Initialize session
        self.session = requests.Session()
        self.ua = UserAgent() if settings.rotate_user_agents else None
        self._update_headers()
        
        # Track last request time for rate limiting
        self._last_request_time = 0
        
        logger.info(f"Initialized {self.__class__.__name__} scraper")
    
    def _update_headers(self):
        """Update session headers with fresh user agent."""
        headers = settings.get_headers()
        if self.ua and settings.rotate_user_agents:
            headers['User-Agent'] = self.ua.random
        self.session.headers.update(headers)
    
    def _apply_rate_limit(self):
        """Apply rate limiting delay."""
        if self.rate_limit_delay > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    def _check_robots_txt(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.
        
        Args:
            url: URL to check
        
        Returns:
            True if allowed or check disabled, False otherwise
        """
        if not self.respect_robots:
            return True
        
        allowed = check_robots_txt(url, self.session.headers.get('User-Agent', '*'))
        if not allowed:
            logger.warning(f"URL blocked by robots.txt: {url}")
        return allowed
    
    @retry_on_exception(max_retries=3, delay=1.0, backoff=2.0, exceptions=(requests.RequestException,))
    def _make_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            url: URL to request
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for requests
        
        Returns:
            Response object or None if failed
        """
        # Validate URL
        if not validate_url(url):
            logger.error(f"Invalid URL: {url}")
            return None
        
        # Check robots.txt
        if not self._check_robots_txt(url):
            return None
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Rotate user agent
        if self.ua and settings.rotate_user_agents:
            self._update_headers()
        
        try:
            logger.debug(f"Making {method} request to: {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            response.raise_for_status()
            logger.debug(f"Request successful: {url} (Status: {response.status_code})")
            
            return response
            
        except requests.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            raise
        except requests.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            raise
        except requests.Timeout as e:
            logger.error(f"Timeout error for {url}: {e}")
            raise
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            raise
    
    def get_soup(self, url: str, parser: str = "lxml") -> Optional[BeautifulSoup]:
        """
        Get BeautifulSoup object from URL.
        
        Args:
            url: URL to scrape
            parser: HTML parser to use (lxml, html.parser, etc.)
        
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            response = self._make_request(url)
            if response:
                return BeautifulSoup(response.content, parser)
            return None
        except Exception as e:
            logger.error(f"Error creating soup from {url}: {e}")
            return None
    
    def get_json(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON data from URL.
        
        Args:
            url: URL to request
        
        Returns:
            JSON data as dictionary or None if failed
        """
        try:
            response = self._make_request(url)
            if response:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error parsing JSON from {url}: {e}")
            return None
    
    @abstractmethod
    def scrape(self, **kwargs) -> ScrapingResult:
        """
        Main scraping method to be implemented by subclasses.
        
        Args:
            **kwargs: Scraper-specific arguments
        
        Returns:
            ScrapingResult with scraped companies
        """
        pass
    
    @abstractmethod
    def parse_company(self, data: Any) -> Optional[Company]:
        """
        Parse company data from scraped content.
        
        Args:
            data: Raw data to parse (HTML element, JSON object, etc.)
        
        Returns:
            Company object or None if parsing failed
        """
        pass
    
    def close(self):
        """Close session and cleanup resources."""
        if self.session:
            self.session.close()
            logger.debug(f"Closed session for {self.__class__.__name__}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor to ensure session is closed."""
        self.close()


if __name__ == "__main__":
    # Example usage (abstract class cannot be instantiated directly)
    print("BaseScraper is an abstract class. Use specific scraper implementations.")
    print("Available methods:")
    print("- _make_request(url): Make HTTP request with retry logic")
    print("- get_soup(url): Get BeautifulSoup object")
    print("- get_json(url): Get JSON data")
    print("- scrape(**kwargs): Main scraping method (must be implemented)")
    print("- parse_company(data): Parse company data (must be implemented)")
